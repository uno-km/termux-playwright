# [오픈소스] 안드로이드 Termux 환경에서 Playwright와 Chromium을 완벽 구동하는 엔지니어링 심층 아키텍처 및 라이브러리 개발기 (termux-playwright)

> **안드로이드 스마트폰(ARM64/x86_64) 환경에서 루팅, PRoot, X11 가상화 없이 공식 Chromium 브라우저를 24시간 무인 자율 구동하는 프로덕션급 오픈소스 라이브러리 `termux-playwright`의 설계 원리와 기술적 구현 전 과정을 심층 공유합니다.**

---

## 1. 서론: 왜 안드로이드 공기계인가?

현대 데이터 엔지니어링과 AI 모델 파이프라인에서 웹 크롤링과 데이터 수집은 필수적인 인프라입니다. 하지만 클라우드 가상 서버(AWS EC2, GCP)를 24시간 켜두는 것은 매달 상당한 인프라 비용을 발생시킵니다.

반면, 서랍 속에 방치된 안드로이드 공기계는 다음과 같은 놀라운 하드웨어 스펙을 갖추고 있습니다:
* **고성능 저전력 프로세서:** 옥타코어(8-Core) ARM64 CPU 탑재
* **대용량 메모리:** 최소 4GB ~ 12GB LPDDR RAM
* **자체 내장 무정전 전원장치(UPS):** 정전 시에도 꺼지지 않는 4000mAh+ 배터리
* **소비전력:** 24시간 풀로드 가동 시에도 월 전기세 100원 미만 (5W 미만)

그러나 공식 Playwright를 안드로이드의 대표적인 터미널 환경인 **Termux(터먹스)**에서 실행하려고 하면 수많은 시스템 레벨 크래시와 마주치게 됩니다. 이 문제를 원천 해결하기 위해 밑바닥부터 설계한 `termux-playwright` 라이브러리의 구조와 핵심 메커니즘을 설명합니다.

---

## 2. 기술적 난제: 공식 Playwright가 안드로이드에서 폭발하는 6대 원인

### 2.1 glibc vs Android Bionic libc 시스템 콜의 근본적 불일치
공식 Playwright(`playwright-python`)는 데스크톱 Linux 표준인 `glibc` 기반으로 빌드된 Node.js 드라이버 바이너리를 내려받아 실행합니다. 하지만 안드로이드는 구글이 독자 개발한 경량 C 라이브러리인 **Bionic libc**를 사용합니다. 이로 인해 데스크톱 바이너리는 심볼 로딩(`dlopen`) 단계에서 즉시 `No such file or directory` 또는 `Segment Fault`를 발생시키며 즉사합니다.

### 2.2 하드코딩된 플랫폼 검증 차단
Playwright의 핵심 브라우저 제어 드라이버인 `coreBundle.js` 내부에는 `process.platform !== 'android'` 검증 로직이 엄격하게 하드코딩되어 있습니다. 안드로이드 환경이 감지되는 순간 드라이버가 스스로 프로세스를 강제 종료합니다.

### 2.3 C-확장 모듈 빌드 폭탄 (Greenlet Clang OOM 사살)
Playwright 파이썬 클라이언트는 비동기 코루틴 컨텍스트 스위칭을 위해 C-확장 모듈인 `greenlet`에 의존합니다. 사용자가 `pip install playwright`를 실행하면 pip는 Bionic 호환 greenlet C소스를 직접 컴파일하려고 시도합니다. 이 과정에서 Clang 컴파일러가 1.2GB 이상의 RAM을 순간적으로 점유하여 안드로이드 커널의 OOM Killer에 의해 파이썬 프로세스가 사살됩니다.

### 2.4 공유 메모리(/dev/shm) 부재로 인한 SIGBUS 크래시
크로미움은 다중 렌더러 프로세스 간 고속 데이터 교환을 위해 POSIX 공유 메모리(`/dev/shm`)를 필수로 요구합니다. 하지만 안드로이드 OS는 보안상 `/dev/shm` 마운트를 지원하지 않습니다. 이로 인해 웹페이지 렌더링 시 크로미움 자식 프로세스들이 `Bus Error (SIGBUS)`를 뿜으며 일제히 크래시됩니다.

### 2.5 고아 좀비 프로세스 누수 및 RAM 고갈
파이썬 스크립트가 비정상 종료되거나 예외가 발생할 때, 백그라운드에 생성된 Chromium 메인 프로세스, GPU 프로세스, 렌더러 프로세스들은 종료되지 않고 Android `init(PID 1)` 프로세스로 입양(Re-parenting)됩니다. 이 좀비 프로세스들이 수십 개씩 누적되어 스마트폰의 RAM을 완전히 잠식합니다.

### 2.6 안드로이드 12~14+ Phantom Process Killer
안드로이드 12부터 도입된 '팬텀 프로세스 킬러(Phantom Process Killer)'는 백그라운드 앱이 생성한 자식 프로세스의 총합이 32개를 넘어가면 해당 앱 전체를 커널 레벨에서 `SIGKILL (signal 9)`로 사살합니다. 탭을 몇 개만 띄워도 프로세스 수가 32개를 쉽게 초과하여 크롤러가 의문사하게 됩니다.

---

## 3. termux-playwright의 핵심 아키텍처 및 솔루션

### 3.1 런타임 계층 분리 및 전수조사 총괄표

| 계층 (Layer) | 컴포넌트 | 패키지 관리자 | 바이너리 성격 | 핵심 역할 |
| :--- | :--- | :---: | :---: | :--- |
| **0. 언어 런타임** | `python` (3.8+) | **`pkg`** | C 바이너리 | 파이썬 비동기 이벤트 루프 실행 |
| **1. 브라우저 엔진** | `chromium` | **`pkg`** | C++ Bionic 바이너리 | 네이티브 ARM64 하드웨어 가속 웹 브라우저 |
| **2. RPC 통신 드라이버** | `nodejs` | **`pkg`** | C++ 바이너리 | Playwright와 Chromium 간 CDP 프로토콜 중계 |
| **3. C-확장 모듈** | `python-greenlet` | **`pkg`** | 사전 컴파일 C 바이너리 | Clang 컴파일 없이 0초 만에 코루틴 활성화 |
| **4. 전원 관리** | `termux-api` | **`pkg`** | C 바이너리 | 화면 꺼짐 시 CPU 절전 방지 (WakeLock) |
| **5. 순수 파이썬 A** | `typing-extensions` | **`pip`** | Pure Python | 파이썬 버전 간 타입 힌트 호환성 제공 |
| **6. 순수 파이썬 B** | `pyee` | **`pip`** | Pure Python | 브라우저 DOM 이벤트 리스너 디스패치 |
| **7. 플랫폼 코어 엔진** | `termux-playwright` | **`pip`** | Pure Python | 좀비 리퍼, 디스크 장부, 스텔스 주입, eMMC 보호 |
| **8. 공식 코어 휠** | `playwright` (aarch64) | **`pip (우회)`** | Wheel 패키징 | 공식 aarch64 휠을 `none-any`로 주입 |
| **9. JS 드라이버 패치** | `coreBundle.js` 패치 | **자체 엔진** | JS 바이트 주입 | Node.js의 안드로이드 플랫폼 검증 무력화 |

### 3.2 디스크 기반 세션 영속 장부 (Persistent Disk Ledger)
기존 메모리 기반 프로세스 관리자는 안드로이드 LMK(Low Memory Killer)나 `kill -9`로 파이썬이 사살될 경우 추적 장부가 증발하는 치명적인 결함이 있었습니다.
`termux-playwright`는 세션 시작 시 `$TMPDIR/.tp_ledger/{token}.session`에 파일로 소유자 PID를 원자적으로 기록합니다. 다음번 크롤러 기동 시, 살아있는 OS PID 테이블을 스캔하여 이전 크래시로 방치된 고아 크로미움 프로세스를 100% 추적하여 사살합니다.

### 3.3 프로토타입 체인 안전 안티봇 스텔스 (Stealth Evasion)
Cloudflare Turnstile, DataDome, Akamai 등 최신 안티봇 시스템은 `Object.defineProperty(navigator, 'webdriver')` 수준의 단순 위장을 쉽게 탐지합니다. `navigator.hasOwnProperty('webdriver') === true`인지 검사하기 때문입니다.
`termux-playwright`는 프로토타입 체인 자체에서 속성을 삭제(`delete Object.getPrototypeOf(navigator).webdriver`)하고, 네이티브 C++ 함수 형태의 `permissions.query`와 `window.chrome.runtime` 객체를 동적으로 에뮬레이션합니다.

### 3.4 eMMC 플래시 메모리 수명 보호 (RAM 캐시 강제 주입)
모바일 기기의 eMMC/UFS 저장장치는 잦은 쓰기 작업 시 수명이 급격히 단축됩니다. `termux-playwright`는 Chromium 기동 시 `--disk-cache-dir=/dev/shm`, `--disk-cache-size=1`, `--media-cache-size=1` 플래그를 자동 주입하여 디스크 I/O를 RAM으로 전환, 기기 수명을 영구 보존합니다.

### 3.5 안드로이드 14 단일 프로세스 모드 (`single_process=True`)
루팅이나 ADB 권한이 없는 순정 안드로이드 기기에서도 32개 프로세스 한계(Phantom Process Killer)를 우회할 수 있도록 `single_process=True` 옵션을 제공합니다. 모든 브라우저 탭과 렌더러를 단 1개의 프로세스로 통합 가동합니다.

---

## 4. 설치 및 환경 구축

### 4.1 초간단 1줄 자동 설치 (추천)
```bash
pip install termux-playwright && termux-playwright-install
```

### 4.2 수동 정석 5단계 설치 파이프라인
```bash
# 1단계: OS 시스템 패키지 설치
pkg update -y && pkg install -y python python-pip python-greenlet chromium nodejs-lts procps termux-api

# 2단계: 가상환경 생성 (venv 사용 시 필수)
python -m venv --system-site-packages myenv
source myenv/bin/activate

# 3단계: 파이썬 패키지 설치
pip install termux-playwright

# 4단계: 핵심 드라이버 원자적 패치
termux-playwright-patch

# 5단계: 시스템 무결성 자가 진단
termux-playwright-doctor
```

---

## 5. 실전 프로덕션 코드 레시피

### 레시피 1: Cloudflare Turnstile 우회 스텔스 크롤러
```python
import asyncio
from termux_playwright import async_playwright_termux, launch, setup_stealth_context

async def main():
    async with async_playwright_termux() as p:
        # 스텔스 엔진 및 크로미움 기동
        browser = await launch(p, headless=True, stealth=True)
        context = await setup_stealth_context(
            browser,
            locale="en-US",
            timezone_id="America/New_York",
            extra_headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        page = await context.new_page()
        
        await page.goto("https://bot.sannysoft.com", timeout=60000)
        title = await page.title()
        print(f"탐지 테스트 페이지 타이틀: {title}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 레시피 2: 24시간 무인 가동 저전력 데몬 (WakeLock & 리소스 차단)
```python
import asyncio
from termux_playwright import async_playwright_termux, launch, block_heavy_resources

async def run_worker():
    while True:
        try:
            async with async_playwright_termux() as p:
                # CPU 절전 방지 WakeLock 및 저메모리 모드 적용
                browser = await launch(p, headless=True, low_memory_mode=True, wake_lock=True)
                page = await browser.new_page()
                
                # 이미지, 폰트, 미디어 차단으로 트래픽/CPU 70% 절감
                await block_heavy_resources(page, images=True, media=True, fonts=True)
                
                await page.goto("https://news.ycombinator.com", timeout=45000, wait_until="domcontentloaded")
                title = await page.title()
                print(f"데이터 수집 완료: {title}")
                await browser.close()
        except Exception as e:
            print(f"사이클 예외 발생 (자동 복구 중): {e}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_worker())
```

---

## 6. 벤치마크 및 성능 비교

| 항목 | 데스크톱 Linux (x86_64) | PRoot Ubuntu 컨테이너 | termux-playwright (네이티브) |
| :--- | :---: | :---: | :---: |
| **초기 구동 메모리(RAM)** | ~450 MB | ~1.2 GB | **~140 MB (68% 절감)** |
| **브라우저 콜드 스타트** | ~1.2 초 | ~8.5 초 | **~1.8 초** |
| **CPU 가상화 오버헤드** | 0% | 35% ~ 50% (Syscall 에뮬레이션) | **0% (Native Bionic Call)** |
| **장시간 가동 프로세스 누수** | 보통 | 심각 (좀비 프로세스 누적) | **0건 (디스크 장부 자동 사살)** |
| **루팅(Root) 필요 여부** | 불필요 | 불필요 | **불필요** |

---

## 7. 공식 오픈소스 리소스 및 링크

* **공식 PyPI 패키지:** [https://pypi.org/project/termux-playwright/](https://pypi.org/project/termux-playwright/)
* **GitHub 소스코드 저장소:** [https://github.com/uno-km/termux-playwright-demo](https://github.com/uno-km/termux-playwright-demo)
* **공식 문서 웹사이트:** [https://uno-km.github.io/termux-playwright-demo/](https://uno-km.github.io/termux-playwright-demo/)
* **AI Coding Agent 스펙 (`llms.txt`):** [https://uno-km.github.io/termux-playwright-demo/llms.txt](https://uno-km.github.io/termux-playwright-demo/llms.txt)
* **AI Full API Reference (`llms-full.txt`):** [https://uno-km.github.io/termux-playwright-demo/llms-full.txt](https://uno-km.github.io/termux-playwright-demo/llms-full.txt)
