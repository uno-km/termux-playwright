# [오픈소스] 안드로이드 Termux 환경에서 Playwright와 Chromium을 구동하는 기술 아키텍처 및 라이브러리 개발기 (termux-playwright)

안드로이드 스마트폰(ARM64/x86_64) 환경에서 24시간 가동 가능한 무인 웹 자동화 및 데이터 파이프라인 노드를 구축하기 위해, 공식 Playwright 및 Chromium 브라우저를 Bionic libc 상에서 네이티브로 오케스트레이션하는 오픈소스 라이브러리(termux-playwright)를 개발하고 배포한 과정을 기술합니다.

---

## 1. 배경 및 기술적 문제 정의

### 1.1 공식 Playwright의 안드로이드 미지원 원인
공식 Playwright는 데스크톱 Linux(glibc 기반 x86_64/arm64), macOS, Windows만을 공식 타겟으로 지원합니다. Android Termux 환경에서 `pip install playwright`를 시도할 경우 다음과 같은 치명적인 병목 현상과 크래시가 발생합니다:

1. **플랫폼 식별자 차단:** Playwright 내부 `coreBundle.js` 드라이버에 `process.platform !== 'android'` 검증 로직이 하드코딩되어 있어 즉시 예외를 발생시키고 실행을 중단합니다.
2. **C-확장 빌드 폭탄 (Greenlet 컴파일 병목):** 파이썬 비동기 코루틴 루프를 구동하는 `greenlet` C-확장 모듈을 `pip`로 빌드하려고 시도하며, 모바일 CPU에서 1.2GB 이상의 Clang 컴파일 리소스를 요구하다가 메모리 부족(OOM)으로 프로세스가 사살됩니다.
3. **공유 메모리(/dev/shm) 고갈:** 안드로이드 커널의 `/dev/shm` 부재로 인해 크로미움 멀티 프로세스가 렌더링 도중 `Bus Error (SIGBUS)`로 크래시됩니다.
4. **고아 좀비 프로세스 누수:** 파이썬 인터프리터 종료 시 크로미움 자식 프로세스가 사살되지 않고 init(PID 1)으로 재부모화(re-parented)되어 모바일 RAM과 배터리를 영구 점유합니다.
5. **안드로이드 12~14+ Phantom Process Killer:** 백그라운드 프로세스가 32개를 초과할 때 안드로이드 커널이 Termux 전체를 `SIGKILL (signal 9)`로 사살합니다.

---

## 2. 아키텍처 및 시스템 레벨 해결 방안

### 2.1 런타임 의존성 분리 및 전수조사

| 계층 (Layer) | 구성 요소 | 제공 관리자 | 바이너리 성격 | 핵심 역할 |
| :--- | :--- | :---: | :---: | :--- |
| **0. OS 런타임** | `python` (3.8+) | `pkg` | C 바이너리 | 파이썬 실행 엔진 |
| **1. 브라우저** | `chromium` | `pkg` | C++ 바이너리 | 네이티브 ARM64 웹 브라우저 |
| **2. RPC 드라이버** | `nodejs` | `pkg` | C++ 바이너리 | Playwright-Chromium 통신 중계 |
| **3. C-확장 모듈** | `python-greenlet` | `pkg` | C 바이너리 | 사전 컴파일된 Bionic 비동기 코루틴 루프 |
| **4. 전원 제어** | `termux-api` | `pkg` | C 바이너리 | 백그라운드 CPU 절전 방지 (WakeLock) |
| **5. 순수 파이썬** | `pyee`, `typing-extensions` | `pip` | Pure Python | 이벤트 수신 및 타입 호환 |
| **6. 최적화 엔진** | `termux-playwright` | `pip` | Pure Python | 좀비 리퍼, 디스크 장부, 스텔스 주입 |

### 2.2 디스크 기반 세션 영속 장부 (Persistent Disk Ledger)
안드로이드 커널 Low Memory Killer(LMK)나 `SIGKILL` 발생 시 파이썬 메모리(RAM)의 프로세스 추적 장부는 영구 소멸됩니다. `termux-playwright`는 세션 시작 시 `$TMPDIR/.tp_ledger/{session_token}.session`에 PID를 원자적으로 기록하며, 다음번 기동 시 이전 크래시로 방치된 고아 크로미움 프로세스를 live OS PID 검증 후 100% 추적 사살합니다.

### 2.3 프로토타입 체인 안전 안티봇 스텔스 (Stealth Evasion)
기존 `Object.defineProperty(navigator, 'webdriver')` 방식은 `navigator.hasOwnProperty('webdriver') === true` 및 `toString()` 검증에 걸려 Cloudflare Turnstile과 DataDome에 즉시 차단됩니다.
`termux-playwright`는 프로토타입 체인 자체에서 속성을 삭제(`delete Object.getPrototypeOf(navigator).webdriver`)하고 네이티브 C++ 바인딩 수준의 `permissions.query`와 `window.chrome.runtime` 객체를 에뮬레이션합니다.

### 2.4 eMMC 플래시 메모리 마모 방지
모바일 기기의 NAND 플래시 수명 보호를 위해 크로미움 캐시 경로를 RAM 기반 임시 스토리지(`/dev/shm`)로 강제 라우팅하고, 디스크 및 미디어 캐시 크기를 1바이트로 제한하여 플래시 메모리 마모를 원천 차단합니다.

---

## 3. 원클릭 설치 및 배포

### 3.1 1줄 자동 설치 명령어
```bash
pip install termux-playwright && termux-playwright-install
```

### 3.2 수동 단계별 설치
```bash
# 1. 시스템 의존성 프로비저닝
pkg update -y && pkg install -y python python-pip python-greenlet chromium nodejs-lts procps termux-api

# 2. 가상환경 생성 (venv 사용 시 필수)
python -m venv --system-site-packages myenv
source myenv/bin/activate

# 3. 패키지 설치 및 패치 적용
pip install termux-playwright
termux-playwright-install
termux-playwright-doctor
```

---

## 4. 실전 프로덕션 코드 패턴

### 4.1 스텔스 우회 크롤러
```python
import asyncio
from termux_playwright import async_playwright_termux, launch, setup_stealth_context

async def main():
    async with async_playwright_termux() as p:
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
        print(f"Page Title: {title}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.2 24/7 저전력 무인 크롤링 데몬 (WakeLock & 리소스 차단)
```python
import asyncio
from termux_playwright import async_playwright_termux, launch, block_heavy_resources

async def run_worker():
    while True:
        try:
            async with async_playwright_termux() as p:
                browser = await launch(p, headless=True, low_memory_mode=True, wake_lock=True)
                page = await browser.new_page()
                await block_heavy_resources(page, images=True, media=True, fonts=True)
                
                await page.goto("https://news.ycombinator.com", timeout=45000, wait_until="domcontentloaded")
                title = await page.title()
                print(f"Harvested Title: {title}")
                await browser.close()
        except Exception as e:
            print(f"Worker cycle recovery: {e}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_worker())
```

---

## 5. 오픈소스 리소스 링크

- **PyPI 공식 패키지:** https://pypi.org/project/termux-playwright/
- **GitHub 저장소:** https://github.com/uno-km/termux-playwright-demo
- **공식 문서 웹사이트:** https://uno-km.github.io/termux-playwright-demo/
- **AI 레퍼런스 스펙 (llms.txt):** https://uno-km.github.io/termux-playwright-demo/llms.txt
