/**
 * Example: Production JavaScript/Node.js Web Scraping on Termux
 * Run with: node examples/crawler.js
 */

const { launch, setupStealthContext, blockHeavyResources } = require('../lib');

async function run() {
    console.log('[Termux-Playwright JS] Launching optimized Chromium...');
    
    const browser = await launch({
        headless: true,
        stealth: true,
        lowMemoryMode: true,
        wakeLock: true
    });

    try {
        const context = await setupStealthContext(browser, {
            locale: 'en-US',
            timezoneId: 'America/New_York'
        });

        const page = await context.newPage();
        
        // Block heavy media to save mobile data and CPU
        await blockHeavyResources(page, { images: true, media: true, fonts: true });

        console.log('[Termux-Playwright JS] Navigating to target website...');
        await page.goto('https://news.ycombinator.com', { timeout: 45000, waitUntil: 'domcontentloaded' });
        
        const title = await page.title();
        console.log(`[Termux-Playwright JS] Harvested Page Title: "${title}"`);
    } finally {
        await browser.close();
        console.log('[Termux-Playwright JS] Browser closed and session ledger cleaned up.');
    }
}

run().catch(console.error);
