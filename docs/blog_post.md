# [개발문서-3] #11. 남는 안드로이드 공기계(S7)를 24시간 무인 크롤링 서버로 개조하기! (Termux + Playwright 극한의 세팅)

안녕하세요!!! 쌩초보 코딩단입니다. 천천히 앞으로 나아가는 개발자입니다!

이전 포스팅에서는 AI 음성 모델을 깎고 분석하는 작업들을 해봤는데요,
데이터 분석과 AI 학습에서 **"가장 중요한 건 양질의 데이터"** 아니겠습니까?

그런데 매번 크롤러를 제 노트북에서 돌리자니 리소스도 많이 먹고 컴퓨터를 꺼둘 수가 없더라고요.
그래서 서랍 속에 잠들어있던 **갤럭시 S7 (공기계)**를 **24시간 크롤링 전용 리눅스 서버**로 개조해 보았습니다!! 📱🔥

이번 포스팅에서는 남들은 "안드로이드(Termux)에서는 안 돌아간다"며 포기하는 **Playwright(플레이라이트)**와 **Chromium(크로미움)** 브라우저를, S7 기기 내부에서 완벽하게 구동시키는 과정을 초보자의 시선에서 공유해보려 합니다.

진짜 며칠 밤새면서 뚫어낸 눈물의 노하우입니다... 😅

---

## 🚀 전 세계 어디서든 1초 만에 설치하기 (PyPI 공식 배포)

이 삽질의 결정체를 저만 쓰기 아까워서, 아예 파이썬 공식 패키지 저장소(PyPI)에 등록해버렸습니다!! 
이제 폰을 초기화하거나 새 폰을 가져오셔도 복잡한 스크립트 칠 필요 없이 아래 명령어 **두 줄**이면 설치가 끝납니다.

```bash
pip install termux-playwright
termux-playwright-install
```

> **🔥 이 설치 명령어가 백그라운드에서 해주는 일:**
> 1. Termux용 `chromium`, `nodejs` 자동 설치
> 2. OS 플랫폼 우회용 휠(Wheel) 다운로드 및 강제 패키징
> 3. Playwright 코어 엔진(`coreBundle.js`)에 리눅스 강제 인식 패치 주입

모든 소스코드와 데모 코드는 깃허브에도 공개해두었습니다!
- **GitHub Repository**: [uno-km/termux-playwright-demo](https://github.com/uno-km/termux-playwright-demo)
- **PyPI Package**: [termux-playwright](https://pypi.org/project/termux-playwright/)

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

---

## 💻 코드 설명 및 로직 (`examples/basic_crawler.py`)

자, 그럼 이제 환경이 구축되었으니 실제로 크롤링을 수행하는 샘플 코드를 보겠습니다.

```python
import asyncio
from playwright.async_api import async_playwright
import termux_playwright

async def run_crawler():
    print("🚀 [Termux] Playwright 크롤러 초기화 중...")
    
    async with async_playwright() as p:
        # termux_playwright.launch()가 자동으로 환경변수, 샌드박스 완화, eMMC 마모 방지 인자를 주입합니다!
        browser = await termux_playwright.launch(p, headless=True)
        
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

## 🧪 실물 기기(S7) 라이브 테스트 화면

**1. 테스트용 폴더 만들고 들어가기**
```bash
mkdir test-playwright
cd test-playwright
```

**2. 대망의 파이썬 패키지 갈기기! (설치)**
```bash
pip install termux-playwright
termux-playwright-install
```

**3. 예제 코드 가져오기**
```bash
wget https://raw.githubusercontent.com/uno-km/termux-playwright-demo/main/examples/basic_crawler.py
```

**4. 결과 보기 (크롤링 구동!)**
```bash
python basic_crawler.py
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

제가 비전공자에 쌩초보라 돌아가는 길도 많고 삽질도 많지만, 저처럼 천천히 배우시는 분들에게 이 글이 작은 희망과 팁이 되었으면 좋겠습니다.
화이팅!! 💪🔥
