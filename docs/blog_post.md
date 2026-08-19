# [개발문서-3] #11. 남는 안드로이드 공기계(안드로이드 8/9+)를 24시간 무인 크롤링 서버로 개조하기! (Termux + Playwright 극한의 세팅)

안녕하세요!!! 쌩초보 코딩단입니다. 천천히 앞으로 나아가는 개발자입니다!

이전 포스팅에서는 AI 음성 모델을 깎고 분석하는 작업들을 해봤는데요,
데이터 분석과 AI 학습에서 **"가장 중요한 건 양질의 데이터"** 아니겠습니까?

그런데 매번 크롤러를 제 노트북에서 돌리자니 리소스도 많이 먹고 컴퓨터를 꺼둘 수가 없더라고요.
그래서 서랍 속에 잠들어있던 **안드로이드 공기계 (구형 스마트폰)**를 **24시간 크롤링 전용 리눅스 서버**로 개조해 보았습니다!! 📱🔥

이번 포스팅에서는 남들은 "안드로이드(Termux)에서는 안 돌아간다"며 포기하는 **Playwright(플레이라이트)**와 **Chromium(크로미움)** 브라우저를, 안드로이드 스마트폰 내부에서 완벽하게 구동시키는 과정을 초보자의 시선에서 공유해보려 합니다.

진짜 며칠 밤새면서 뚫어낸 눈물의 노하우입니다... 😅

---

## 🚀 전 세계 어디서든 1초 만에 설치하기 (PyPI 공식 배포)

이 삽질의 결정체를 저만 쓰기 아까워서, 아예 파이썬 공식 패키지 저장소(PyPI)에 등록해버렸습니다!! 
이제 폰을 초기화하거나 새 폰을 가져오셔도 복잡한 스크립트 칠 필요 없이 아래 **한 줄 명령어**면 끝납니다.

### ⚡ 퀵스타트: 한 줄 복사-붙여넣기 (가장 추천!)
```bash
pip install termux-playwright && termux-playwright-install
```

### 🪄 초보자용: 원클릭 쉘 부트스트래퍼 (Zero-Friction)
```bash
curl -sL https://raw.githubusercontent.com/uno-km/termux-playwright-demo/main/install.sh | bash
```

> **🔥 이 한 줄 명령어가 백그라운드에서 자동으로 해주는 일:**
> 1. Termux OS 전용 `chromium`, `nodejs`, `python-greenlet` 사전 바이너리 자동 프로비저닝 (1.2GB Clang 컴파일 차단)
> 2. PyPI aarch64 휠 플랫폼 우회 다운로드 및 pip 강제 주입
> 3. Playwright 심장부(`coreBundle.js`)에 리눅스 인식 패치 원자적 주입
> 4. `termux-playwright-doctor` 7단계 자가 진단 리포트 자동 출력

---

### 🟢 1. 전체 의존성 전수조사 총괄표 (`pkg` vs `pip` vs `Patch`)

| 계층 (Layer) | 패키지 / 라이브러리명 | 제공처 (관리자) | 성격 (Type) | 상위 의존 대상 | 왜 필요한가? (핵심 역할) |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **0. 언어 런타임** | `python` (3.8+) | **`pkg`** | C 바이너리 | Termux 기본 환경 | 파이썬 스크립트 및 크롤러 실행 엔진 |
| **1. OS 브라우저** | `chromium` | **`pkg`** | C++ 바이너리 | Termux X11 저장소 | Playwright가 원격 조종할 실제 네이티브 웹 브라우저 |
| **2. 드라이버 런타임** | `nodejs` | **`pkg`** | C++ 바이너리 | Android Bionic | Playwright 파이썬-브라우저 간 통신을 중계하는 RPC 서버 |
| **3. C-확장 모듈** | `python-greenlet` | **`pkg`** | C 바이너리 | `python` | 1.2GB Clang 컴파일 없이 Playwright 비동기 코루틴 루프 구동 |
| **4. 전원 관리 (선택)** | `termux-api` | **`pkg`** | C 바이너리 | Android OS API | 화면 꺼짐 시 CPU 잠자기 방지 (`termux-wake-lock`) |
| **5. 순수 파이썬 A** | `typing-extensions` | **`pip`** | Pure Python | `python` | 파이썬 구형/신형 버전 간 타입 힌트 호환성 제공 |
| **6. 순수 파이썬 B** | `pyee` | **`pip`** | Pure Python | `python` | 브라우저 이벤트(클릭, 페이지 로드) 수신/발송 처리 |
| **7. 우리 도구 엔진** | `termux-playwright` | **`pip`** | Pure Python | `pyee`, `typing-ext` | 안드로이드 환경 최적화, 자동 인스톨러, 좀비 리퍼 제공 |
| **8. 공식 코어 휠** | `playwright` (aarch64) | **`pip (우회)`** | Wheel 패키징 | `python-greenlet` | PyPI의 aarch64 휠을 `none-any`로 속여 강제 설치 |
| **9. JS 코어 패치** | `coreBundle.js` 패치 | **자체 엔진** | JS 바이트 주입 | `playwright` | Node.js의 "안드로이드 실행 차단" 로직을 리눅스로 속임 |

---

### ⚡ 2. 절대 실패하지 않는 엄격한 5단계 수동 실행 명령어 (엔지니어링 상세)

**1단계: OS 시스템 패키지 설치 (`pkg`)**
```bash
pkg update -y
pkg install -y chromium nodejs python python-greenlet termux-api
```

**2단계: 파이썬 관리 툴 및 도구 설치 (`pip`)**
```bash
pip install --upgrade pip setuptools
pip install pyee typing-extensions termux-playwright
```

**3~4단계: Playwright 휠 우회 다운로드 및 코어 패치 (`자동화 파이프라인`)**
```bash
termux-playwright-install
```

**5단계: 시스템 정상 구동 자가 진단 (`doctor`)**
```bash
termux-playwright-doctor
```

> **🔥 핵심 설계 포인트 3가지:**
> 1. **`greenlet`의 소유권 분리:** `pip`가 컴파일하려 들면 터지므로, 반드시 **`pkg install python-greenlet`**이 먼저 실행되어야 합니다.
> 2. **`setup.py`의 슬림화:** 우리 패키지(`termux-playwright`)는 `pip install` 시 `greenlet`을 요구하지 않도록 순수 파이썬 메타데이터만 유지합니다.
> 3. **순서 역전 방지:** `pkg` $\rightarrow$ `pip` $\rightarrow$ `install (휠+패치)` $\rightarrow$ `doctor` 순서를 엄격히 준수할 때 100% 무장애 설치가 완성됩니다.

모든 소스코드와 데모 코드는 깃허브에도 공개해두었습니다!
- **GitHub Repository**: [uno-km/termux-playwright-demo](https://github.com/uno-km/termux-playwright-demo)
- **PyPI Package**: [termux-playwright](https://pypi.org/project/termux-playwright/)

---

## 💻 코드 설명 및 로직 (`examples/basic_crawler.py`)

자, 그럼 이제 환경이 구축되었으니 실제로 크롤링을 수행하는 샘플 코드를 보겠습니다.

```python
import asyncio
from termux_playwright import async_playwright_termux, launch

async def run_crawler():
    print("🚀 [Termux] Playwright 크롤러 초기화 중...")
    
    # async_playwright_termux가 환경변수 사전 주입 및 종료 시 자원 회수를 보장합니다!
    async with async_playwright_termux() as p:
        # launch()가 자동으로 Termux 전용 바이너리 경로 탐색, 샌드박스 해제, eMMC 수명 보호 인자를 주입합니다!
        browser = await launch(p, headless=True)
        
        print("🌐 브라우저 실행 완료! 네이버(Naver)로 접속합니다...")
        page = await browser.new_page()
        await page.goto("https://www.naver.com", timeout=60000)
        
        title = await page.title()
        print(f"\n✅ [접속 성공] 추출된 페이지 제목: {title}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_crawler())
```

---

## ⚡ [딥다이브] 속도(JIT) vs 안정성(jitless)의 트레이드오프와 안드로이드 버전별 비밀!

개발 도중 정말 흥미로운 안드로이드 OS의 비밀을 하나 발견했습니다.

### 1. 일반 크롬 앱 vs Termux 크롬의 차이 (`mmap(RWX)`)
* **플레이스토어 순정 크롬 앱:** 구글의 정식 앱이라 OS로부터 JIT(초고속 기계어 컴파일) 권한을 특별히 인정받습니다.
* **Termux 안의 크롬:** 일반 사용자 샌드박스에서 도는 리눅스 바이너리입니다.  
  안드로이드 10부터는 **`W^X (Write XOR Execute)`** 커널 보안 규칙 때문에, 앱이 메모리에 코드를 실시간으로 쓰면서 실행(`mmap RWX`)하려고 하면 커널이 해킹 시도로 간주하고 `SIGSEGV`로 크롬을 즉시 강제 종료시킵니다.

### 2. 안드로이드 버전별 동작 & 안드로이드 8/9 이전 구형 기기가 유리한 이유!
* **안드로이드 8.0/8.1 이하 구형 기기:** W^X 보안 제약이 도입되기 전 버전이라, 우리 라이브러리가 **자동으로 풀파워 JIT(TurboFan)를 켜서 5~20배 초고속으로 웹을 렌더링**합니다! (구형 공기계의 대반전!)
* **안드로이드 10 이상 최신 폰:** 크롬이 0.1초 만에 튕기는 것을 막기 위해 **`--jitless` (인터프리터 안전 모드)**가 자동으로 적용됩니다.

### 3. 코드에서 JIT 제어 및 1줄 초고속 가속법
```python
# 1. JIT 모드 직접 제어 (안드로이드 9 이하 / 루팅 폰 전용)
browser = await launch(p, jitless=False)  # 5~20배 풀파워 JIT 가동 (안드로이드 10+에서는 크래시 위험)

# 2. --jitless에서도 3~5배 빠르게 긁는 1줄 마법 (내장 가속기)
from termux_playwright import block_heavy_resources

await block_heavy_resources(page)  # 무거운 이미지/폰트/미디어를 1초 만에 차단!
```

> **⚠️ 루팅 관련 주의:** 안드로이드 10+에서 JIT를 쓰기 위해 SELinux를 끄거나 루팅하는 것은 보안상 대단히 위험하므로 절대 권장하지 않습니다!

---

## 🏰 두 가지 실행 모드: '하하호호 멀티스레딩 모드' vs '나홀로 독무대 요새 모드'

우리가 만든 패키지는 사용 목적에 따라 2가지 완벽한 모드를 지원합니다:

### 1. 🤝 기본 모드: 협력적 멀티스레딩 (Default)
* **목적:** 스마트폰 안에서 텔레그램 봇, 웹 서버, 여러 개의 비동기 크롤러를 동시에 돌릴 때!
* **원리:** 자식 프로세스 청소나 대기를 `asyncio.to_thread`를 통해 별도 백그라운드 워커 스레드로 넘겨서, **메인 비동기 루프에 0.0001초의 렉도 걸리지 않게 OS 자원을 화기애애하게 공유**합니다.

### 2. 👑 강력 옵션: 독무대 요새 모드 (`standalone_mode=True`)
* **목적:** "이번 작업은 진짜 단 1%의 간섭이나 이전 캐시 찌꺼기도 없이 **나 혼자 무균실에서 풀파워로 긁겠다!**" 할 때!
* **제공 혜택:**
  * **1회용 임시 무균 프로필 (`/tmp/tp_solo_UUID`)**: 이번 세션만을 위한 격리 프로필을 만들고, 브라우저가 꺼지는 순간 0바이트 하나 안 남기고 완전 파쇄!
  * **Anti-Throttling 활성화**: 화면이 꺼져도 크롬이 타이머 속도를 줄이지 않음 (`--disable-background-timer-throttling`).
  * **일체형 WakeLock 결합**: `wake_lock=True` 옵션으로 브라우저 켜짐/꺼짐과 스마트폰 잠자기 방지를 자동 연동!

```python
# 🏰 독무대 요새 모드 실행 예시
browser = await launch(
    p,
    headless=True,
    standalone_mode=True,  # 👈 완벽한 무균실 독무대 모드!
    wake_lock=True,        # 👈 CPU 잠자기 방지 자동 결합
)
```

---

## 🧪 실물 안드로이드 기기 라이브 테스트 화면

**1. 테스트용 폴더 만들고 들어가기**
```bash
mkdir test-playwright
cd test-playwright
```

**2. 5단계 설치 파이프라인 완주 후 크롤링 실행!**
```bash
python -m termux_playwright.installer doctor
python examples/basic_crawler.py
```

**(실행 결과 로그)**
> 🚀 [Termux] Playwright 크롤러 초기화 중...
> 🌐 브라우저 실행 완료! 네이버(Naver)로 접속합니다...
>
> ✅ [접속 성공] 추출된 페이지 제목: 네이버

와... 진짜 됩니다. 😭
이제 이 작은 안드로이드 공기계가, 제 방구석 와이파이를 타고 24시간 내내 무인으로 전 세계 웹사이트를 돌아다니며 데이터를 긁어와 주는 **저만의 미니 AI 데이터 센터**가 되었습니다.

---

## 💡 꿀팁: 가상환경(venv) 쓸 때 99%가 겪는 'greenlet 미싱' 함정과 해결법!

파이썬 개발자라면 습관처럼 `python -m venv myenv`를 치고 가상환경을 만드실 텐데요,
Termux 환경에서는 **반드시 알아두어야 할 치명적인 함정**이 있습니다!

### 😱 왜 가상환경에 들어가면 `greenlet missing` 에러가 날까요?
* `pkg install python-greenlet`은 스마트폰 OS의 **[아파트 공용 창고]**에 설치됩니다.
* 그런데 `python -m venv`로 새 방을 만들면, 파이썬이 **공용 창고로 가는 문을 쾅 닫아버립니다 (`include-system-site-packages = false`)!**
* 그래서 가상환경 안에서 실행하면 바깥 공용 창고에 있는 greenlet C-바이너리를 못 봐서 크래시가 납니다. (그렇다고 venv 안에서 `pip install greenlet` 치면 스마트폰에서 C컴파일 하다가 100% 빌드가 터집니다!)

### 🚀 해결법: 창문 하나 열어두기 (`--system-site-packages`)
이건 리눅스 GNOME GUI(`PyGObject`), 로봇 공학(`ROS 2`), 임베디드(`python3-opencv`) 등 **OS 레벨 C-바이너리를 다루는 전 세계 모든 파이썬 엔지니어들의 공통 표준 공식**입니다!

```bash
# 🟢 가상환경을 만들 때 --system-site-packages 옵션을 쏙 넣어주세요!
python -m venv --system-site-packages venv
source venv/bin/activate
```
이렇게 만들면 가상환경의 깔끔함은 그대로 유지하면서, `pkg`로 깔아둔 초고속 C-확장 greenlet을 1초 만에 바로 쓸 수 있습니다!

---

## 🏁 마치며...

서랍 속 낡은 스마트폰을 리눅스 서버로 바꾸고, 거기에 동적 크롤링의 끝판왕인 Playwright까지 구동시켰습니다.
"이게 될까?" 싶었던 게 하나씩 풀릴 때마다 코딩의 참맛을 느끼네요. 

제가 비전공자에 쌩초보라 돌아가는 길도 많고 삽질도 많지만, 저처럼 천천히 배우시는 분들에게 이 글이 작은 희망과 팁이 되었으면 좋겠습니다.
화이팅!! 💪🔥
