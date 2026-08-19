"""
Generate clean technical docs/blog_post.md and docs/tistory_post.html.
"""
import os

blog_markdown = """# [오픈소스] 안드로이드 Termux 환경에서 Playwright와 Chromium을 구동하는 기술 아키텍처 및 라이브러리 개발기 (termux-playwright)

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
"""

# Tistory HTML with rich AI & Multilingual SEO Metadata
tistory_html = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[오픈소스] 안드로이드 Termux 환경에서 Playwright와 Chromium을 구동하는 기술 아키텍처 및 라이브러리 개발기</title>
    
    <!-- AI Crawlers & Global Multi-language SEO Honeytrap -->
    <meta name="description" content="안드로이드 Termux 환경에서 Playwright와 Chromium 브라우저를 루팅 없이 네이티브로 구동하는 termux-playwright 오픈소스 기술 아키텍처 및 개발기">
    <meta name="keywords" content="Termux, Playwright, Android, Web Scraping, Chromium, Python, termux-playwright, Crawler, Bionic libc, Anti-bot, Cloudflare Turnstile, 自动化, 爬虫, 安卓, ブラウザ自動化, クローラー, كشط الويب, 파이썬 크롤링, 터먹스 크롬">
    <meta name="author" content="uno-km (쌩초보코딩단)">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
    
    <!-- Open Graph / Facebook / Kakao -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="[오픈소스] 안드로이드 Termux 환경에서 Playwright/Chromium 구동 기술 아키텍처 (termux-playwright)">
    <meta property="og:description" content="루팅, PRoot 없이 안드로이드 기기에서 24시간 무인 Playwright 웹 크롤러를 구동하는 완전한 아키텍처 가이드">
    <meta property="og:url" content="https://uno-km.github.io/termux-playwright-demo/">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Termux-Playwright: Production Browser Automation on Android">
    <meta name="twitter:description" content="Production-grade Playwright & Chromium automation toolkit for Android Termux.">
    
    <!-- Schema.org JSON-LD Structured Data for AI & Search Engines -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "TechArticle",
      "headline": "[오픈소스] 안드로이드 Termux 환경에서 Playwright와 Chromium을 구동하는 기술 아키텍처 및 개발기",
      "description": "How to run native Playwright and Chromium on Android Termux without root or PRoot using termux-playwright.",
      "author": {
        "@type": "Person",
        "name": "uno-km"
      },
      "publisher": {
        "@type": "Organization",
        "name": "Termux-Playwright Project",
        "url": "https://uno-km.github.io/termux-playwright-demo/"
      },
      "mainEntityOfPage": "https://uno-km.github.io/termux-playwright-demo/",
      "keywords": "Playwright, Termux, Android, Python, Web Scraping, Chromium, Stealth",
      "articleBody": "Production-grade automated Playwright integration and runtime optimizer for Android Termux..."
    }
    </script>
</head>
<body style="margin: 0; padding: 20px; background-color: #ffffff; color: #222222; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.7; font-size: 16px;">

<!-- Tistory Ready Article Wrapper (Inline CSS for 100% Rendering Fidelity) -->
<div class="article-container" style="max-width: 860px; margin: 0 auto; color: #24292f;">

    <h1 style="color: #004499; font-size: 26px; border-bottom: 2px solid #004499; padding-bottom: 12px; margin-top: 0; line-height: 1.4;">
        [오픈소스] 안드로이드 Termux 환경에서 Playwright와 Chromium을 구동하는 기술 아키텍처 및 개발기 (termux-playwright)
    </h1>

    <p style="color: #57606a; font-size: 15px; margin-bottom: 24px;">
        안드로이드 스마트폰(ARM64/x86_64) 환경에서 24시간 가동 가능한 무인 웹 자동화 및 데이터 파이프라인 노드를 구축하기 위해, 공식 Playwright 및 Chromium 브라우저를 Bionic libc 상에서 네이티브로 오케스트레이션하는 오픈소스 라이브러리(<strong>termux-playwright</strong>)를 개발하고 배포한 과정을 기술합니다.
    </p>

    <!-- Callout Box -->
    <div style="background-color: #f0f7ff; border-left: 4px solid #0055cc; padding: 16px 20px; border-radius: 4px; margin: 20px 0;">
        <strong style="color: #004499; display: block; margin-bottom: 6px; font-size: 15px;">1줄 초간단 설치 (PyPI 공식 배포)</strong>
        <p style="margin: 0 0 10px 0; font-size: 14px;">Termux 터미널에서 다음 명령어를 실행하면 모든 C-바이너리와 플랫폼 패치가 자동 프로비저닝됩니다:</p>
        <div style="background-color: #1e293b; color: #f8fafc; padding: 12px 16px; border-radius: 6px; font-family: Consolas, monospace; font-size: 14px; overflow-x: auto;">
            <code>pip install termux-playwright &amp;&amp; termux-playwright-install</code>
        </div>
    </div>

    <h2 style="color: #003366; font-size: 20px; border-bottom: 1px solid #d0d7de; padding-bottom: 8px; margin-top: 36px;">
        1. 배경 및 기술적 문제 정의
    </h2>

    <h3 style="color: #0969da; font-size: 17px; margin-top: 20px;">
        1.1 공식 Playwright의 안드로이드 미지원 원인
    </h3>
    <p>공식 Playwright는 데스크톱 Linux(glibc 기반), macOS, Windows만을 공식 타겟으로 지원합니다. Android Termux 환경에서 표준 <code>pip install playwright</code>를 시도할 경우 다음과 같은 치명적인 병목 현상과 크래시가 발생합니다:</p>

    <ul style="padding-left: 20px; color: #333;">
        <li style="margin-bottom: 8px;"><strong>플랫폼 식별자 차단:</strong> Playwright 내부 <code>coreBundle.js</code> 드라이버에 <code>process.platform !== 'android'</code> 검증 로직이 하드코딩되어 있어 즉시 예외를 발생시키고 중단됩니다.</li>
        <li style="margin-bottom: 8px;"><strong>C-확장 빌드 폭탄 (Greenlet 컴파일 병목):</strong> 비동기 루프를 구동하는 <code>greenlet</code> C-확장 모듈을 <code>pip</code>로 빌드하려다 1.2GB 이상의 Clang 리소스를 소모하며 메모리 부족(OOM)으로 프로세스가 즉사합니다.</li>
        <li style="margin-bottom: 8px;"><strong>공유 메모리(/dev/shm) 고갈:</strong> 안드로이드 커널의 <code>/dev/shm</code> 부재로 인해 크로미움 멀티 프로세스가 렌더링 도중 <code>Bus Error (SIGBUS)</code>로 강제 종료됩니다.</li>
        <li style="margin-bottom: 8px;"><strong>고아 좀비 프로세스 누수:</strong> 파이썬 종료 시 크로미움 자식 프로세스가 살아남아 init(PID 1)으로 재부모화되어 모바일 RAM을 영구 점유합니다.</li>
        <li style="margin-bottom: 8px;"><strong>Android 12~14+ Phantom Process Killer:</strong> 백그라운드 프로세스가 32개를 초과할 때 안드로이드 커널이 Termux 전체를 <code>SIGKILL (signal 9)</code>로 강제 사살합니다.</li>
    </ul>

    <h2 style="color: #003366; font-size: 20px; border-bottom: 1px solid #d0d7de; padding-bottom: 8px; margin-top: 36px;">
        2. 아키텍처 및 시스템 레벨 해결 방안
    </h2>

    <h3 style="color: #0969da; font-size: 17px; margin-top: 20px;">
        2.1 런타임 의존성 분리 및 전수조사
    </h3>

    <div style="overflow-x: auto; margin: 16px 0;">
        <table style="width: 100%; border-collapse: collapse; font-size: 14px; text-align: left;">
            <thead>
                <tr style="background-color: #f6f8fa; border-bottom: 2px solid #d0d7de;">
                    <th style="padding: 10px 12px; border: 1px solid #d0d7de;">계층 (Layer)</th>
                    <th style="padding: 10px 12px; border: 1px solid #d0d7de;">구성 요소</th>
                    <th style="padding: 10px 12px; border: 1px solid #d0d7de;">제공 관리자</th>
                    <th style="padding: 10px 12px; border: 1px solid #d0d7de;">핵심 역할</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><strong>0. OS 런타임</strong></td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><code>python</code> (3.8+)</td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de; color: #0969da; font-weight: bold;">pkg</td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;">파이썬 실행 엔진</td>
                </tr>
                <tr style="background-color: #fafbfc;">
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><strong>1. 브라우저</strong></td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><code>chromium</code></td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de; color: #0969da; font-weight: bold;">pkg</td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;">네이티브 ARM64 웹 브라우저</td>
                </tr>
                <tr>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><strong>2. RPC 드라이버</strong></td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><code>nodejs</code></td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de; color: #0969da; font-weight: bold;">pkg</td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;">Playwright-Chromium 통신 중계</td>
                </tr>
                <tr style="background-color: #fafbfc;">
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><strong>3. C-확장 모듈</strong></td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><code>python-greenlet</code></td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de; color: #0969da; font-weight: bold;">pkg</td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;">사전 컴파일된 Bionic 비동기 코루틴 루프</td>
                </tr>
                <tr>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><strong>4. 최적화 도구</strong></td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;"><code>termux-playwright</code></td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de; color: #1a7f37; font-weight: bold;">pip</td>
                    <td style="padding: 9px 12px; border: 1px solid #d0d7de;">디스크 세션 장부, 스텔스 주입, eMMC 보호</td>
                </tr>
            </tbody>
        </table>
    </div>

    <h3 style="color: #0969da; font-size: 17px; margin-top: 20px;">
        2.2 디스크 기반 세션 영속 장부 (Persistent Disk Ledger)
    </h3>
    <p>안드로이드 LMK(Low Memory Killer)나 <code>kill -9</code>로 파이썬이 강제 종료되면 RAM 상의 추적 장부는 즉시 증발합니다. <strong>termux-playwright</strong>는 세션 시작 시 <code>$TMPDIR/.tp_ledger/{token}.session</code>에 원자적으로 PID를 기록하며, 다음번 기동 시 이전 크래시로 방치된 고아 프로세스를 실시간 OS 검증 후 100% 추적 사살합니다.</p>

    <h3 style="color: #0969da; font-size: 17px; margin-top: 20px;">
        2.3 프로토타입 체인 안전 안티봇 스텔스 (Stealth Evasion)
    </h3>
    <p>Cloudflare Turnstile과 DataDome은 <code>navigator.hasOwnProperty('webdriver')</code> 및 함수 <code>toString()</code>을 정밀 감사하여 봇을 감지합니다. termux-playwright는 <code>delete Object.getPrototypeOf(navigator).webdriver</code>로 프로토타입 체인에서 원천 제거하고, 네이티브 C++ 바인딩 형태의 <code>permissions.query</code>와 <code>window.chrome.runtime</code>을 에뮬레이션합니다.</p>

    <h2 style="color: #003366; font-size: 20px; border-bottom: 1px solid #d0d7de; padding-bottom: 8px; margin-top: 36px;">
        3. 실전 프로덕션 코드 예제
    </h2>

    <h3 style="color: #0969da; font-size: 17px; margin-top: 20px;">
        3.1 스텔스 우회 크롤러 (Cloudflare 회피)
    </h3>

    <div style="background-color: #1e293b; color: #f8fafc; padding: 16px 20px; border-radius: 6px; font-family: Consolas, monospace; font-size: 14px; overflow-x: auto; margin: 16px 0;">
<pre style="margin: 0; padding: 0;"><code>import asyncio
from termux_playwright import async_playwright_termux, launch, setup_stealth_context

async def main():
    async with async_playwright_termux() as p:
        # 스텔스 플래그 주입 및 크로미움 기동
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
    asyncio.run(main())</code></pre>
    </div>

    <h2 style="color: #003366; font-size: 20px; border-bottom: 1px solid #d0d7de; padding-bottom: 8px; margin-top: 36px;">
        4. 공식 오픈소스 리소스
    </h2>

    <ul style="padding-left: 20px; font-size: 15px;">
        <li style="margin-bottom: 8px;"><strong>PyPI 패키지:</strong> <a href="https://pypi.org/project/termux-playwright/" target="_blank" style="color: #0969da; text-decoration: underline;">https://pypi.org/project/termux-playwright/</a></li>
        <li style="margin-bottom: 8px;"><strong>GitHub 저장소:</strong> <a href="https://github.com/uno-km/termux-playwright-demo" target="_blank" style="color: #0969da; text-decoration: underline;">https://github.com/uno-km/termux-playwright-demo</a></li>
        <li style="margin-bottom: 8px;"><strong>공식 문서 사이트:</strong> <a href="https://uno-km.github.io/termux-playwright-demo/" target="_blank" style="color: #0969da; text-decoration: underline;">https://uno-km.github.io/termux-playwright-demo/</a></li>
        <li style="margin-bottom: 8px;"><strong>AI LLM 규격서:</strong> <a href="https://uno-km.github.io/termux-playwright-demo/llms.txt" target="_blank" style="color: #0969da; text-decoration: underline;">https://uno-km.github.io/termux-playwright-demo/llms.txt</a></li>
    </ul>

</div>
</body>
</html>"""

with open('docs/blog_post.md', 'w', encoding='utf-8') as f:
    f.write(blog_markdown)
print('Generated docs/blog_post.md')

with open('docs/tistory_post.html', 'w', encoding='utf-8') as f:
    f.write(tistory_html)
print('Generated docs/tistory_post.html')
