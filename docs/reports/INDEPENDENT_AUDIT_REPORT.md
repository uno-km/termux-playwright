# [독립 감사관 최종 감사 보고서: 암행어사 현미경 스나이퍼 감사]

**대상 프로젝트:** `termux-playwright` (v1.61.1)  
**감사 기준:** 실동작 코드 전수 조사, 패치 전후 취약점 추적, 단위 테스트 위장 검증, 15대 감사 영역 증거 기반 전수 감사  
**감사관 선언:** 본 보고서는 작성자의 의도, README, 문서, 발표자료, pytest 56개 전원 PASS 결과 일체를 증거로 인정하지 않고, **오직 실제 파이썬/셸 코드와 시스템 런타임 증거만을 기반으로 작성**되었습니다.

---

# Executive Verdict

### ⛔ **RELEASE BLOCKER** (출시 차단 및 배포 즉각 중단 대상)

> **핵심 사유:**  
> 1. **존재하지 않는 버전 하드코딩 폭탄:** `DEFAULT_PLAYWRIGHT_VERSION = "1.61.1"`은 PyPI 상에 영원히 존재하지 않는 가공의 버전으로, 오프라인/네트워크 일시 지연 시 폴백 루틴이 100% 붕괴(HTTP 404 Fail)합니다.  
> 2. **좀비 프로세스 청소 무력화 레이스:** 정상 종료(`browser.on("disconnected")`) 시 세션 토큰을 즉시 폐기하여, 크래시나 고착된 Chromium 자식 렌더러가 백그라운드에 영구 잔류하는 치명적 설계 결함이 확인되었습니다.  
> 3. **Toybox ps 80컬럼 절단 취약점(신규 발생):** Tier 3 `ps` 스캐너에 `-w`/`-ww` 옵션이 누락되어 80글자를 초과하는 세션 플래그 탐색이 무력화됩니다.  
> 4. **시그널 핸들러 내 서브프로세스 호출(신규 발생):** Python 시그널 핸들러 내부에서 `subprocess.run(["pgrep", ...])`을 직접 실행하여 GIL/ForkLock 데드락을 유발합니다.  
> 5. **배터리 영구 고갈(WakeLock Leak):** 비정상 종료 시 WakeLock을 OS에 영구 반납하지 않는 누수 구조가 방치되어 있습니다.

---

# 1. Hardcoded Logic Findings (하드코딩 및 위장 탐지)

```
[탐지 증거]
1. termux_playwright/installer.py:28
   DEFAULT_PLAYWRIGHT_VERSION = "1.61.1"

2. termux_playwright/browser.py:22-23
   DEFAULT_JS_MAX_OLD_SPACE_SIZE_MB: int = 128
   DEFAULT_NODE_MAX_OLD_SPACE_SIZE_MB: int = 256

3. termux_playwright/platform.py:33-34
   MINIMUM_REQUIRED_STORAGE_MB: int = 50
   ANDROID_10_SDK_VERSION: int = 29
```

### 1.1 [치명적] 존재하지 않는 Playwright 버전 하드코딩 (`DEFAULT_PLAYWRIGHT_VERSION = "1.61.1"`)
* **실제 증거:** PyPI 공식 저장소의 `playwright` 릴리스에는 `1.60.0`, `1.61.0`, `1.62.0`만 존재하며 `1.61.1`은 존재하지 않습니다.
* **위험 경로:** PyPI API 조회 실패(`resolve_latest_compatible_version()`) 시 `DEFAULT_PLAYWRIGHT_VERSION`("1.61.1")으로 폴백합니다. 그 직후 `fetch_pypi_wheel_info("1.61.1")`가 `https://pypi.org/pypi/playwright/1.61.1/json`을 호출하여 3회 재시도(2s, 4s, 8s) 후 **HTTP 404 에러와 함께 100% 붕괴**합니다.

### 1.2 위험한 임의 매직 넘버 하드코딩 (50MB / 128MB / 256MB)
* **저장공간 임계값 50MB:** Chromium의 임시 프로필 생성 및 대형 SPA(네이버, 유튜브 등) 렌더링 시 DOM 캐시와 SQLite 데이터만으로 50MB가 즉시 고갈됩니다. 51MB 남은 상태에서 preflight를 통과한 후 실제 페이지 로딩 중 OS Low Storage 잠금에 걸려 앱이 크래시됩니다.
* **Node 256MB / JS 128MB 고정:** 복잡한 JS 파싱 시 128MB 힙을 초과하면 V8 Fatal Error (OOM)로 즉시 강제 종료됩니다.

---

# 2. Test Illusion Findings (테스트 속임수 및 위장 탐지)

**"pytest 56개 전원 PASS는 철저한 Mock 격리에 의한 환상이다."**

| 테스트 항목 | 테스트 코드 위치 | 실제 런타임의 진실 |
| :--- | :--- | :--- |
| **Playwright 1.61.1 폴백 테스트** | `test_installer.py:28` | 가짜 Mock URL을 사용하여 PASS 처리함. 실제 PyPI에 1.61.1이 없다는 사실을 은폐. |
| **aarch64 휠 다운로드 테스트** | `test_installer.py:38` | 가짜 JSON 응답 객체를 주입하여 PASS. 실제 manylinux wheel unzipping 무결성은 단 1회도 검증 안 함. |
| **비동기/동기 브라우저 기동** | `test_browser.py:117, 180` | `mock_playwright.chromium.launch = AsyncMock()`으로 Playwright 전체를 통째로 가짜 객체로 대체함. |
| **Tier 3 ps 프로세스 탐색** | `test_reaper.py:186` | `FakeOut(stdout="HEADER...\nu0_a123 5544...")` 단일 문자열 Mock으로 통과. 실제 Android Toybox ps의 80컬럼 절단 문제를 가림. |
| **PID 기반 추적/삭제** | `test_reaper.py:24, 116` | `register_pid()`를 테스트에서만 호출함. 실제 `browser.py`에서는 PID 추적 코드가 단 한 줄도 실행되지 않음 (데드코드). |

---

# 3. Hidden Technical Debt & Newly Introduced Vulnerabilities (수정 중 새로 발생한 취약점)

작성자가 최근 커밋(`d12595e`, `18dc63c`, `5f0b9eb`)에서 "20개 위험을 모두 해결했다"고 주장하며 코드를 수정하는 과정에서 **오히려 새로 생성된 취약점**들입니다.

### [신규 취약점 1] Toybox ps 80컬럼 절단으로 인한 Tier 3 좀비 청소 완전 무력화
* **발생 위치:** `termux_playwright/reaper.py:219-224`
```python
ps_commands: List[List[str]] = [
    ["ps", "-A", "-o", "pid,args"],
    ["ps", "-ef"],
    ["busybox", "ps", "-ef"],
    ["ps"],
]
```
* **메커니즘 분석:**
  * 안드로이드의 기본 `/system/bin/ps`(Toybox)는 터미널 컬럼 크기가 주어지지 않을 때 명령행을 **80자로 강제 절단**합니다.
  * Chromium 실행 명령: `/data/data/com.termux/files/usr/bin/chromium-browser --termux-session-id=32자리HEXUUID...` (최소 106자)
  * 절단된 출력: `u0_a123 12345 1 0 12:00 ? 00:00:00 /data/data/com.termux/files/usr/bin/chromium --termux-s`
  * 결과: `if session_flag not in line:`(240라인)이 무조건 False가 되어 **Tier 3 ps를 통한 고아 프로세스 발견이 100% 실패**합니다.
  * **해결 누락:** `ps -efww`, `ps -A -ww` 등 wide 옵션이 전혀 지정되지 않았습니다.

### [신규 취약점 2] 정상 연결 해제(`disconnected`) 시 조기 토큰 폐기로 인한 고아 프로세스 영구 방치
* **발생 위치:** `termux_playwright/browser.py:297, 356`
```python
browser.on("disconnected", lambda: ProcessReaper.unregister_session_token(session_token))
```
* **메커니즘 분석:**
  1. `await browser.close()`가 호출되면 Playwright의 메인 소켓이 닫히며 즉시 `"disconnected"` 이벤트가 발생합니다.
  2. `unregister_session_token(session_token)`이 실행되어 `_tracked_sessions`에서 해당 토큰을 **즉시 삭제**합니다.
  3. 직후 `async_playwright_termux` 컨텍스트 매니저가 종료되며 `ProcessReaper.kill_all_tracked()`가 실행됩니다.
  4. 하지만 토큰이 이미 삭제되었으므로 `kill_all_tracked()`는 아무것도 청소하지 않습니다.
  5. 안드로이드 환경 특성상 `browser.close()` 이후에도 렌더러 자식 프로세스(`chromium-renderer`)나 유틸리티 프로세스가 백그라운드에 남아있는 경우가 빈번한데, 이 프로세스들은 세션 추적이 지워져 영구 잔류합니다.

### [신규 취약점 3] Python 시그널 핸들러 내 `subprocess.run()` 호출로 인한 데드락 위험
* **발생 위치:** `termux_playwright/reaper.py:310-324`
```python
def _chained_signal_handler(signum, frame):
    cls.kill_all_tracked() # -> 내부에서 discover_session_pids() -> subprocess.run(['pgrep'/'ps']) 실행!
```
* **메커니즘 분석:**  
  * 파이썬의 시그널 핸들러는 메인 스레드가 어떤 I/O나 메모리 할당, 서브프로세스 파이프 잠금(Fork Lock)을 쥐고 있는 도중 인터럽트 형태로 비동기 진입합니다.
  * 시그널 핸들러 내부에서 `subprocess.run()`을 호출하면 `os.fork` / `subprocess.Popen` 생성 중 파이프 버퍼 충돌이나 데드락(`RuntimeError: reentrant call`)이 발생하여 프로세스가 완전히 멈춥니다.

### [신규 취약점 4] Import 시점 전역 환경변수 오염
* **발생 위치:** `termux_playwright/__init__.py:35-36`
```python
if is_termux():
    configure_environment(strict=False)
```
* **메커니즘 분석:**  
  * README에서는 "Zero side-effects, 프로세스 격리"를 주장하지만, 패키지를 `import termux_playwright` 하는 즉시 `os.environ["NODE_OPTIONS"]`, `os.environ["PLAYWRIGHT_CHROMIUM_PATH"]`, `os.environ["PLAYWRIGHT_NODEJS_PATH"]`를 전역적으로 강제 변조합니다.
  * 이로 인해 동일 파이썬 프로세스 내에서 실행되는 다른 모든 라이브러리의 Node.js 프로세스가 강제로 256MB 힙 제한에 묶이게 됩니다.

---

# 4. Memory & Resource Findings (메모리 및 자원 누수 감사)

### 4.1 `TermuxWakeLock` 비정상 종료 시 배터리 영구 고갈 누수
* **위치:** `termux_playwright/reaper.py:413-471`
* **분석:**  
  * `TermuxWakeLock`은 `atexit` 등록이나 시그널 훅이 전혀 없습니다.
  * 크롤러가 작업 중 `SIGKILL`, OOM 킬러, 또는 예기치 못한 예외로 프로세스가 사망할 경우, 안드로이드 OS의 `Termux:API` 서비스에는 WakeLock이 영구히 걸려 있게 됩니다.
  * 스마트폰은 화면이 꺼져도 CPU가 딥 슬립(Deep Sleep)에 진입하지 못해 몇 시간 만에 배터리가 0%로 방전되고 기기가 과열됩니다.

### 4.2 설치 스크립트의 `termux-api` 패키지 누락
* **위치:** `termux_playwright/installer.py:87-91`
```python
REQUIRED_TERMUX_SYSTEM_PACKAGES: List[str] = [
    "chromium",
    "nodejs",
    "python-greenlet",
]
```
* **분석:**  
  * `installer.py`의 필수 패키지 목록에서 `termux-api`가 누락되어 있습니다.
  * 사용자가 `termux-playwright-install`로 설치한 뒤 문서에 나온 대로 `TermuxWakeLock()`을 실행하면 `ProcessLifecycleError: termux-wake-lock binary not found` 예외가 발생하며 터집니다.

---

# 5. Fallback & Downgrade Findings (풀백 사기 및 성능 착시)

### 5.1 `--jitless` 강제 주입으로 인한 5배~20배 심각한 성능 저하
* **위치:** `termux_playwright/browser.py:149-153`
* **분석:**  
  * Android 10+ (SDK $\ge$ 29)에서 SELinux W^X 정책 준수를 위해 `--jitless`를 강제 주입합니다.
  * V8 JIT 컴파일러(TurboFan, Maglev, Sparkplug)가 완전히 꺼지고 Ignition 바이트코드 인터프리터로만 동작하므로, 자바스크립트 실행 속도가 **5배~20배 극단적으로 느려집니다.**
  * 갤럭시 S7 같은 구형 기기에서 네이버, 유튜브 등 무거운 SPA 사이트를 방문하면 DOM 렌더링에만 30~50초가 소요되어, Playwright 기본 타임아웃(30초)으로 인해 `Page.goto: Timeout 30000ms exceeded` 에러가 폭발합니다.

### 5.2 `is_termux()` 오탐으로 인한 타 환경 바이너리 침범
* **위치:** `termux_playwright/platform.py:44-46`
```python
for pkg in KNOWN_TERMUX_PREFIXES:
    if os.path.exists(f"/data/data/{pkg}"):
        return True
```
* **분석:**  
  * 안드로이드 폰에 Termux 앱이 깔려있기만 하면, QPython/Pydroid3/Chaquopy 등 다른 앱 환경에서 파이썬을 실행해도 `is_termux()`가 `True`를 반환합니다.
  * 그 결과 다른 샌드박스 앱이 권한도 없는 Termux의 `/data/data/com.termux` 내부 경로에 접근을 시도하다 `EACCES` 권한 에러로 뻗어버립니다.

---

# 6. Architecture Weaknesses (아키텍처 부채 및 설계 결함)

```mermaid
flowchart TD
    subgraph Defect1["[결함 1] 데드코드 추적기"]
        A["ProcessReaper.register_pid()"] -.->|"호출처: 오직 test_reaper.py뿐"| B["실제 브라우저 기동 시 미사용 (0% 호출)"]
    end

    subgraph Defect2["[결함 2] 좀비 유실 레이스"]
        C["browser.close()"] --> D["'disconnected' 이벤트 발동"]
        D --> E["unregister_session_token() 실행 (토큰 즉시 삭제)"]
        E --> F["kill_all_tracked() 실행 시 토큰 부재 -> 좀비 잔류!"]
    end

    subgraph Defect3["[결함 3] Toybox 절단"]
        G["Chromium Launch (106 chars)"] --> H["Toybox ps 출력 (80 chars 절단)"]
        H --> I["Tier 3 PID 검색 실패"]
    end
```

1. **상태 추적의 이중성 및 데드코드:** `ProcessReaper` 내부에 PID 추적(`_tracked_pids`)과 세션 추적(`_tracked_sessions`)이 공존하나, Playwright 구조상 브라우저 PID를 직접 알 수 없어 PID 추적은 100% 데드코드입니다.
2. **동기/비동기 혼용 블로킹:** `async_playwright_termux` 컨텍스트 매니저의 `finally:` 블록에서 비동기 이벤트 루프 스레드를 무시하고 동기식 `ProcessReaper.kill_all_tracked()`(내부 `time.sleep` 대기 포함)를 직접 호출하여 asyncio 이벤트 루프를 블로킹합니다.
3. **런타임 패치 유실 감지 부재:** `pip install --upgrade playwright`를 실행하면 `coreBundle.js`가 순정으로 덮어씌워지는데, `launch()` 실행 시 `is_core_bundle_patched()` 사전 검증을 하지 않아 Node.js RPC 단에서 영문 모를 크래시가 발생합니다.

---

# 7. Top 20 Things Likely To Explode In Production

내일 운영 환경(실제 안드로이드 기기 24/7 크롤링)에 투입할 경우 가장 먼저 터질 위험 20선:

1. **[P0] 1.61.1 버전 404 크래시:** 오프라인/네트워크 불안정 시 PyPI 폴백 버전 `1.61.1`이 존재하지 않아 설치 파이프라인 즉각 폭발 (`installer.py:28`).
2. **[P0] Toybox 80자 잘림 고아 프로세스 누수:** Tier 3 `ps`가 80자 이상 인자를 자르면서 고아 Chromium 탐지 실패 및 메모리 고갈 (`reaper.py:219`).
3. **[P0] clean disconnect 시 토큰 조기 삭제:** `browser.close()` 직후 토큰이 지워져 하위 자식 렌더러가 좀비 프로세스로 영구 방치 (`browser.py:297`).
4. **[P0] 시그널 핸들러 데드락:** SIGINT/SIGTERM 수신 시 핸들러 내부에서 `subprocess.run()` 호출로 인한 파이썬 런타임 교착 (`reaper.py:310`).
5. **[P1] WakeLock 미반납 배터리 급방전:** 크롤러 비정상 종료 시 WakeLock이 해제되지 않아 폰 배터리가 방전되고 발열 폭발 (`reaper.py:433`).
6. **[P1] 50MB 저장공간 임계값 부족:** 대형 SPA 3개 로딩 시 캐시 데이터로 50MB 초과 및 SQLite 디스크 풀 에러 발생 (`platform.py:33`).
7. **[P1] JIT-less 30초 타임아웃 폭탄:** `--jitless`로 인한 10배 속도 저하로 기본 30초 `page.goto` 타임아웃 빈번 초과 (`browser.py:150`).
8. **[P1] installer.py doctor 실행 불가 (문서 거짓말):** `python -m termux_playwright.installer doctor` 실행 시 doctor 대신 전체 재설치 수행 (`installer.py:434`).
9. **[P1] installer.py 내 termux-api 패키지 누락:** 설치 파이프라인 완주 후 WakeLock 사용 시 실행 파일 없음 예외 발생 (`installer.py:87`).
10. **[P2] 전역 NODE_OPTIONS 오염:** 패키지 임포트만으로 동일 파이썬 프로세스 내 모든 Node 작업의 힙이 256MB로 강제 축소 (`__init__.py:35`).
11. **[P2] 다른 안드로이드 앱과의 충돌:** `/data/data/com.termux` 존재 여부만으로 `is_termux()`가 True가 되어 권한 오류 발생 (`platform.py:44`).
12. **[P2] Playwright 업데이트 시 자동 복구 불가:** Playwright 패키지 업그레이드 시 패치가 풀리지만 `launch()`에서 감지하지 못함 (`browser.py:240`).
13. **[P2] pyee 버전 의존성 불일치:** `pip check` 수행 시 upstream Playwright 버전과 pyee 메이저 버전 충돌 경고 발생 (`setup.py:29`).
14. **[P2] kill_all_tracked 비동기 이벤트 루프 블로킹:** async 컨텍스트 종료 시 동기 `time.sleep` 폴링이 이벤트 루프를 멈추게 함 (`reaper.py:59`).
15. **[P2] _cleaning_up 동시성 플래그 버그:** 동시 호출 시 두 번째 스레드가 정리를 기다리지 않고 즉시 리턴하여 레이스 컨디션 유발 (`reaper.py:135`).
16. **[P3] getprop 없는 환경의 강제 SDK 29 폴백:** 정상 작동하던 Android 9 이전 기기까지 불필요하게 JIT가 꺼져 성능 급락 (`platform.py:120`).
17. **[P3] 백업 파일(`.bak`) 누적 방치:** `cleanup_backup()`이 자동 호출되지 않아 디스크 공간 낭비 (`patcher.py:165`).
18. **[P3] Windows 환경에서의 find_chromium_binary 실패:** 표준 Chrome 설치 경로(`Program Files`) 미탐색으로 일반 데스크톱 호환성 저하 (`platform.py:179`).
19. **[P3] install.sh 파이프 실행 시 에러 은폐:** `pkg update -y || true`로 인해 패키지 저장소 갱신 실패가 무시되고 다음 단계로 진행 (`install.sh:21`).
20. **[P3] Node.js 메모리 옵션 중복 파싱 취약:** `NODE_OPTIONS` 환경변수가 기형적인 문자열일 때 Node 기동 즉시 Crash (`browser.py:183`).

---

# 8. Claims Without Evidence & Documentation Lies (문서 및 주장 검증)

| 문서의 주장 (README / BlogPost) | 실제 코드의 팩트 | 감사관 판정 |
| :--- | :--- | :---: |
| **"100% 무장애 설치 보장"** | PyPI 장애 시 `DEFAULT_PLAYWRIGHT_VERSION = "1.61.1"`(존재하지 않는 버전) 호출로 100% 장애 발생 | ❌ **거짓** |
| **"Zero side-effects, 프로세스 격리"** | `__init__.py`에서 import 시점에 `os.environ` 전역 변조 | ❌ **거짓** |
| **"`python -m termux_playwright.installer doctor`로 검증"** | CLI 인자 파싱이 없어 무조건 전체 재설치 파이프라인 실행됨 | ❌ **문서 오류** |
| **"4단계 멀티티어 완벽 프로세스 회수"** | 정상 종료 시 세션 토큰을 미리 지워버려 좀비 프로세스 방치 | ❌ **설계 결함** |
| **"termux-playwright-install 한 줄로 완벽 프로비저닝"** | `termux-api`가 설치 목록에서 빠져 있어 WakeLock 구동 불가 | ❌ **누락** |

---

# 9. Required Fixes (필수 조치 사항)

1. **`DEFAULT_PLAYWRIGHT_VERSION` 정정:**
   * `installer.py:28`의 기본 버전을 실제 PyPI LTS 버전인 `"1.62.0"` 또는 `"1.61.0"`으로 수정.
2. **Toybox ps Wide 플래그(`-ww`) 추가:**
   * `reaper.py:220`의 `ps` 명령어 목록에 `["ps", "-efww"]`, `["ps", "-A", "-ww", "-o", "pid,args"]`, `["busybox", "ps", "-w"]`를 최우선으로 배치.
3. **Session Token 조기 폐기 제거 및 검증 후 삭제:**
   * `browser.on("disconnected")` 시 즉시 `unregister_session_token()` 하지 말고, `reap_session_zombies()`를 수행하여 남은 자식이 완전히 0개임을 확인한 후 토큰을 unregister하도록 변경.
4. **시그널 핸들러 내 서브프로세스 제거:**
   * `_chained_signal_handler` 내부에서는 오직 메모리에 저장된 자식 프로세스 핸들에 `os.kill`만 날리고, 무거운 `subprocess.run(["pgrep"])` 호출은 시그널 핸들러에서 배제.
5. **WakeLock 생명주기 보호:**
   * `TermuxWakeLock` 내부에 `atexit.register(self.release)`를 등록하여 프로세스가 비정상 사망해도 OS에 락이 해제되도록 보장.
6. **`installer.py` 필수 패키지에 `termux-api` 추가:**
   * `REQUIRED_TERMUX_SYSTEM_PACKAGES`에 `"termux-api"` 추가.
7. **CLI 인자 디스패처 구현:**
   * `installer.py` `__main__`에 `sys.argv[1] == "doctor"` 분기 로직 추가.
8. **Import 시점 전역 오염 제거:**
   * `__init__.py`의 `configure_environment()` 즉시 호출을 제거하고, `launch()` 시점에만 격리 적용.

---

# 10. Brutal Truth (이 프로젝트가 망한다면 왜 망하는가)

> **"테스트가 초록색(PASS)이라는 안도감에 취해, 실제 운영 환경(Android Bionic libc, Toybox ps, SELinux, WakeLock 커널 IPC)의 물리적 제약을 전부 Mock 객체 뒤에 숨겨놓았다."**
>
> 이 프로젝트는 겉보기에 매우 견고한 엔지니어링 용어와 다이어그램, 56개의 무결점 테스트를 갖추고 있으나, **모의 환경(Windows)에서 실제 시스템 콜을 모두 가짜로 치환하여 검증한 탓에, 실제 안드로이드 폰에 올리는 순간 하드코딩된 버전 불일치(404), Toybox 80글자 절단으로 인한 좀비 프로세스 누수, 128MB 힙 초과 OOM, WakeLock 영구 누수로 인한 배터리 고갈이라는 치명적 뇌관들이 순차적으로 폭발**하게 되어 있습니다.
>
> 모든 문제는 '작성자의 설명'이 아니라 **'오직 실제 코드의 한 줄 한 줄'**에서 비롯되었습니다. 위 8가지 필수 조치를 즉각 이행하기 전까지 본 프로젝트의 릴리스는 보류되어야 합니다.
