# [개발문서-3] #11. 남는 안드로이드 공기계(S7)를 24시간 무인 크롤링 서버로 개조하기! (Termux + Playwright 극한의 세팅)

안녕하세요!!! 쌩초보 코딩단입니다. 천천히 앞으로 나아가는 개발자입니다!

이전 포스팅에서는 AI 음성 모델을 깎고 분석하는 작업들을 해봤는데요,
데이터 분석과 AI 학습에서 **"가장 중요한 건 양질의 데이터"** 아니겠습니까?

그런데 매번 크롤러를 제 노트북에서 돌리자니 리소스도 많이 먹고 컴퓨터를 꺼둘 수가 없더라고요.
그래서 서랍 속에 잠들어있던 **갤럭시 S7 (공기계)**를 **24시간 크롤링 전용 리눅스 서버**로 개조해 보았습니다!! 📱🔥

이번 포스팅에서는 남들은 "안드로이드(Termux)에서는 안 돌아간다"며 포기하는 **Playwright(플레이라이트)**와 **Chromium(크로미움)** 브라우저를, S7 기기 내부에서 완벽하게 구동시키는 과정을 초보자의 시선에서 공유해보려 합니다.

진짜 며칠 밤새면서 뚫어낸 눈물의 노하우입니다... 😅

---

## 🚀 Git Source (전체 소스코드 및 인프라 스크립트)

제가 세팅한 모든 셋업 파일과 크롤링 샘플 코드는 아래 깃허브에 퍼블릭(Public)으로 배포해두었습니다!
필요하신 분들은 그냥 가져다가 `node_manager.sh setup` 한번만 치시면 됩니다!

- **GitHub Repository**: [uno-km/termux-playwright-demo](https://github.com/uno-km/termux-playwright-demo)

---

## 🛠️ [환경설정] 안드로이드 Termux 환경에서 Playwright 억지 설치하기!

원래 Playwright는 Windows, Mac, 일반적인 Linux 환경을 공식 지원하지만, 스마트폰 내부의 리눅스 에뮬레이터인 **Termux (Android aarch64)** 환경은 공식적으로 지원하지 않습니다. 
그냥 `pip install playwright`를 치면 에러를 뿜으며 뻗어버리죠.

하지만 쌩초보 코딩단은 포기하지 않았습니다. 다음과 같은 3단계 꼼수(?)로 정면 돌파했습니다!

### 1. Chromium과 Node.js 강제 수동 설치
Playwright가 자체적으로 다운로드하는 브라우저 대신, Termux 패키지 저장소에 있는 순정 `chromium`과 `nodejs`를 강제로 설치했습니다.

### 2. 안드로이드 차단 로직(coreBundle.js) 우회 패치
Playwright의 심장부 소스코드는 안드로이드(Android)를 감지하면 즉시 실행을 중단합니다. 
그래서 파이썬 스크립트를 써서 핵심 코어인 `coreBundle.js` 파일에 **"나는 안드로이드가 아니라 리눅스다!"** 라고 거짓말을 치는(?) 코드를 강제로 주입했습니다.

### 3. 환경변수(.env) 설정
Playwright가 아까 설치한 Termux 전용 Chromium과 Node.js 경로를 정확히 바라보도록 환경변수를 강제 지정해줬습니다.

### 💡 이 모든 과정을 자동화한 쉘 스크립트 (node_manager.sh)
이 복잡한 과정을 수동으로 입력하다 보면 꼭 오타가 나거나 꼬이기 마련입니다. 그래서 깃허브에 올려둔 소스코드에는 이를 한 번에 해결하는 **통합 설치 스크립트(`node_manager.sh`)**가 포함되어 있습니다.

내부 핵심 로직을 살짝 들여다보면 이렇습니다:

```bash
# 1. 휠(Wheel) 우회 다운로드 및 설치
WHL_ORIGINAL="playwright-1.61.0-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl"
WHL_RENAMED="playwright-1.61.0-py3-none-any.whl"
wget -q --show-progress "$DOWNLOAD_URL" -O "$WHL_ORIGINAL"
mv "$WHL_ORIGINAL" "$WHL_RENAMED"  # OS 플랫폼 검사를 우회하기 위해 파일명 위장!
pip install "$WHL_RENAMED" --force-reinstall --no-deps -q

# 2. 파이썬을 이용한 coreBundle.js 자동 패치 (핵심!)
python - <<'PYEOF'
import sys, os, site
SITE_PACKAGES = [p for p in site.getsitepackages() if os.path.isdir(p)][0]
COREBUNDLE = f"{SITE_PACKAGES}/playwright/driver/package/lib/coreBundle.js"
with open(COREBUNDLE, 'r', encoding='utf-8') as f:
    content = f.read()
# "난 안드로이드가 아니라 리눅스야" 라고 세뇌시키는 자바스크립트 코드 주입
INJECTION = 'Object.defineProperty(process, "platform", {value: "linux"});\nObject.defineProperty(require("os"), "platform", {value: () => "linux"});\n'
with open(COREBUNDLE, 'w', encoding='utf-8') as f:
    f.write(INJECTION + content)
PYEOF
```

플랫폼 종속성 검사를 속이기 위해 `.whl` 파일 이름을 강제로 변경(`none-any.whl`)해서 설치하고, Playwright 내부 엔진에 리눅스 환경 변수를 강제로 때려 박는(Injection) 야생의 로직입니다. 이 스크립트 덕분에 기기를 초기화하더라도 명령어 한 줄이면 완벽하게 세팅이 끝납니다!

---

## 💻 코드 설명 및 로직 (termux_crawler_demo.py)

자, 그럼 이제 환경이 구축되었으니 실제로 크롤링을 수행하는 샘플 코드를 보겠습니다.

```python
import asyncio
import os
import sys

# [핵심 로직 1] 
# 실행하기 전에 Termux 내부의 브라우저와 Node.js 경로를 강제로 쥐어줍니다.
os.environ["PLAYWRIGHT_CHROMIUM_PATH"] = "/data/data/com.termux/files/usr/bin/chromium-browser"
os.environ["PLAYWRIGHT_NODEJS_PATH"] = "/data/data/com.termux/files/usr/bin/node"

from playwright.async_api import async_playwright

async def run_crawler():
    print("🚀 [Termux] Playwright 크롤러 초기화 중...")
    
    async with async_playwright() as p:
        # [핵심 로직 2]
        # 안드로이드에서는 브라우저 샌드박스가 충돌을 일으키므로 --no-sandbox 옵션이 필수입니다!
        browser = await p.chromium.launch(
            executable_path=os.environ["PLAYWRIGHT_CHROMIUM_PATH"],
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]
        )
        
        print("🌐 브라우저 실행 완료! 네이버(Naver)로 접속합니다...")
        page = await browser.new_page()
        
        await page.goto("https://www.naver.com", timeout=60000)
        
        # 페이지 제목 추출! (Javascript 렌더링이 다 끝난 동적 데이터 수집 확인)
        title = await page.title()
        print(f"\n✅ [접속 성공] 추출된 페이지 제목: {title}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_crawler())
```

### 코드 요약 (쌩초보를 위한 해설)
1. 파이썬 코드 최상단에서 **"내가 설치한 크로미움 브라우저 위치"**를 알려줍니다.
2. Playwright를 비동기(`async`)로 가동하고 브라우저를 엽니다. 이때 **`--no-sandbox`** 옵션을 안 주면 폰에서 뻗어버리니 주의하세요!
3. 네이버에 접속해서 브라우저 타이틀을 정상적으로 긁어오면 끝! 동적 웹페이지(SPA) 크롤링이 스마트폰에서 되는 겁니다!

---

## 🧪 테스트 및 실구동 화면

자, 이제 떨리는 마음으로 갤럭시 S7 Termux 콘솔에서 명령어를 쳐봅니다.

```bash
$ python termux_crawler_demo.py
```

**(실행 결과 로그)**
> 🚀 [Termux] Playwright 크롤러 초기화 중...
> 🌐 브라우저 실행 완료! 네이버(Naver)로 접속합니다...
>
> ✅ [접속 성공] 추출된 페이지 제목: 네이버

와... 진짜 됩니다. 😭
이제 이 작은 갤럭시 S7이, 제 방구석 와이파이를 타고 24시간 내내 무인으로 전 세계 웹사이트를 돌아다니며 데이터를 긁어와 주는 **저만의 미니 AI 데이터 센터**가 되었습니다.

---

## 🏁 마치며...

서랍 속 낡은 스마트폰을 리눅스 서버로 바꾸고, 거기에 동적 크롤링의 끝판왕인 Playwright까지 구동시켰습니다.
"이게 될까?" 싶었던 게 하나씩 풀릴 때마다 코딩의 참맛을 느끼네요. 

데이터 수집이 자동화되었으니, 다음 포스팅부터는 이 폰이 밤새 모아준 엄청난 양의 텍스트 데이터를 가지고 저번 포스팅에서 실패했던 **LLM 튜닝과 정밀한 분석 작업**을 다시 시작해 보겠습니다.

제가 비전공자에 쌩초보라 돌아가는 길도 많고 삽질도 많지만, 저처럼 천천히 배우시는 분들에게 이 글이 작은 희망과 팁이 되었으면 좋겠습니다.

긴 글 읽어주셔서 감사합니다. 오늘도 열의를 가지고 성장하는 개발자가 되겠습니다! 
화이팅!! 💪🔥
