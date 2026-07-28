import asyncio
import os
import sys

# Termux 환경 변수 강제 설정 (중요!)
# Playwright가 Termux 내부의 Chromium과 Node.js를 올바르게 찾도록 지정합니다.
os.environ["PLAYWRIGHT_CHROMIUM_PATH"] = "/data/data/com.termux/files/usr/bin/chromium-browser"
os.environ["PLAYWRIGHT_NODEJS_PATH"] = "/data/data/com.termux/files/usr/bin/node"

from playwright.async_api import async_playwright

async def run_crawler():
    print("🚀 [Termux] Playwright 크롤러 초기화 중...")
    
    async with async_playwright() as p:
        # Chromium 브라우저 실행 (안드로이드에서는 반드시 no-sandbox 옵션이 필요합니다)
        browser = await p.chromium.launch(
            executable_path=os.environ["PLAYWRIGHT_CHROMIUM_PATH"],
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]
        )
        
        print("🌐 브라우저 실행 완료! 네이버(Naver)로 접속합니다...")
        page = await browser.new_page()
        
        # 페이지 이동 및 대기
        await page.goto("https://www.naver.com", timeout=60000)
        
        # 페이지 제목 추출 (동적 렌더링 확인용)
        title = await page.title()
        print(f"\n✅ [접속 성공] 추출된 페이지 제목: {title}")
        
        # 실전 적용 예시: 검색창 등 특정 요소 크롤링
        print("🔍 실전 크롤링 테스트 완료!")
        
        await browser.close()

if __name__ == "__main__":
    # Windows/Linux 상관없이 비동기 이벤트 루프 실행
    try:
        asyncio.run(run_crawler())
    except Exception as e:
        print(f"❌ [에러 발생] 크롤러 구동 실패: {e}")
        sys.exit(1)
