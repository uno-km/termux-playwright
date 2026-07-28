# Termux-Playwright Automated Integration (S7 Edge Crawler)

## 1. 개요 (Overview)
본 프로젝트는 자원이 제한적인 안드로이드 디바이스(Samsung Galaxy S7)의 가상 리눅스 환경(Termux)에서 최신 동적 웹 스크래핑 프레임워크인 **Playwright**를 구동하기 위한 인프라 구축 및 자동화 데모 프로젝트입니다. 
일반적으로 aarch64 안드로이드 환경에서는 공식 Playwright 바이너리가 호환되지 않아 구동이 불가능하지만, 본 프로젝트는 의존성 우회 설치 및 코어 엔진 패치를 통해 이 한계를 극복하고 24/7 무인 자동화 데이터 수집(Crawling)을 가능하게 합니다.

## 2. 기술 (Technology Stack)
* **OS & Environment**: Android 8.0 (Termux), Linux (aarch64)
* **Language**: Python 3.11+, Node.js (v20+)
* **Framework**: Playwright (Async API)
* **Browser**: Chromium (Termux native package)
* **Infrastructure**: Bash Shell Scripting (`node_manager.sh`)

## 3. 로직 (Architecture & Logic)
본 시스템은 안드로이드 아키텍처의 한계를 우회하기 위해 다음과 같은 3단계 핵심 로직으로 구성됩니다.

1. **의존성(Dependency) 속임수 기법 (Wheel Renaming)**
   - PyPI에서 제공하는 `manylinux_2_17_aarch64` 규격의 Playwright 휠(Wheel) 파일을 강제로 다운로드합니다.
   - 단말기의 OS 종속성 검사를 피하기 위해 파일명을 `none-any.whl`로 변조하여 강제 설치(`--force-reinstall --no-deps`)를 수행합니다.

2. **코어 엔진 런타임 패치 (Runtime Injection)**
   - Playwright 내부의 Node.js 구동 엔진(`coreBundle.js`)은 시스템 환경이 `android`로 식별될 경우 즉시 `process.exit(1)`을 호출하여 실행을 중단합니다.
   - Python 스크립트를 통해 `coreBundle.js` 내부 최상단에 `Object.defineProperty(process, "platform", {value: "linux"});` 코드를 주입(Inject)하여 플랫폼 검증 로직을 무력화합니다.

3. **환경 변수 매핑 및 브라우저 샌드박스 비활성화**
   - Playwright가 내장 브라우저가 아닌 Termux 패키지의 순정 Chromium(`PLAYWRIGHT_CHROMIUM_PATH`)과 Node.js(`PLAYWRIGHT_NODEJS_PATH`)를 사용하도록 환경변수를 바인딩합니다.
   - 런타임 실행 시 안드로이드 커널과의 충돌을 방지하기 위해 샌드박스 해제 플래그(`--no-sandbox`, `--disable-setuid-sandbox`)를 반드시 포함합니다.

## 4. 트러블슈팅 및 롤백 히스토리 (History of Failures)
본 인프라가 안정화되기까지 겪었던 기술적 실패와 해결 과정의 기록입니다.

* **[실패 1] 순정 `pip install playwright` 시도**
  - **현상**: 컴파일 에러 및 브라우저 바이너리 다운로드 실패.
  - **원인**: Playwright가 지원하는 aarch64 빌드는 Ubuntu/Debian 베이스를 상정하며, 안드로이드 Bionic libc와 호환되지 않음.
  - **해결**: Termux 패키지 관리자(`pkg`)가 제공하는 네이티브 `chromium`을 사용하도록 경로를 수동 할당함.

* **[실패 2] Node.js 실행 거부 (Platform Exception)**
  - **현상**: Python 스크립트 실행 시 `Error: Unsupported platform: android` 발생 후 크래시.
  - **원인**: Playwright의 Node.js 브릿지가 안드로이드를 식별하여 명시적으로 차단함.
  - **해결**: 런타임 환경에서 `process.platform`을 `linux`로 강제 오버라이딩하는 자바스크립트 주입 패치 고안.

* **[실패 3] 브라우저 Launch 시 Zombie Process 생성 및 타임아웃**
  - **현상**: 브라우저 인스턴스는 생성되나 페이지 이동이 불가능하고 30초 후 타임아웃 됨.
  - **원인**: 안드로이드 OS 커널의 권한 통제 메커니즘이 Chromium의 샌드박스(Sandbox) 프로세스 생성을 차단함.
  - **해결**: Launch Args에 `--no-sandbox` 및 `--disable-setuid-sandbox` 플래그를 추가하여 권한 충돌 해소.

이러한 수많은 시행착오 끝에, 단일 스크립트(`node_manager.sh`) 실행만으로 안드로이드 디바이스를 완전한 무인 크롤링 서버로 변환할 수 있는 파이프라인이 완성되었습니다.
