import asyncio
import sys
from playwright.async_api import async_playwright
import termux_playwright

async def run_crawler():
    print("🚀 [Termux] Playwright 크롤러 초기화 중...")
    
    async with async_playwright() as p:
        # termux_playwright.launch()가 자동으로 Termux 환경을 감지하고,
        # Chromium/Node.js 경로 할당 및 안드로이드 크래시 방지 필수 플래그(--disable-dev-shm-usage, --no-sandbox 등)를 자동 적용합니다.
        browser = await termux_playwright.launch(p, headless=True)
        
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
    # 비동기 이벤트 루프 실행
    try:
        asyncio.run(run_crawler())
    except Exception as e:
        print(f"❌ [에러 발생] 크롤러 구동 실패: {e}")
        sys.exit(1)
