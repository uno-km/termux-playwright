/**
 * Termux-Playwright Node.js WAF & Bot Challenge Evaluator
 * Cloudflare Turnstile, hCaptcha, and reCAPTCHA auto-detection and resolution.
 * @license MIT
 */

'use strict';

const { HumanMouse } = require('./physics');

const WafChallengeType = {
    CLOUDFLARE_TURNSTILE: 'cloudflare_turnstile',
    CLOUDFLARE_MANAGED: 'cloudflare_managed',
    HCAPTCHA: 'hcaptcha',
    RECAPTCHA: 'recaptcha',
    NONE: 'none'
};

const CLOUDFLARE_SELECTORS = [
    "iframe[src*='challenges.cloudflare.com']",
    "iframe[src*='cf-turnstile']",
    '#cf-stage',
    '#turnstile-wrapper',
    "div[class*='cf-turnstile']"
];

const HCAPTCHA_SELECTORS = [
    "iframe[src*='hcaptcha.com']",
    'div.h-captcha'
];

const RECAPTCHA_SELECTORS = [
    "iframe[src*='google.com/recaptcha']",
    "iframe[src*='recaptcha']",
    'div.g-recaptcha'
];

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class TurnstileEvaluator {
    /**
     * Evaluates whether a known bot challenge widget is on the page.
     * @param {any} page
     * @returns {Promise<string>}
     */
    static async detectChallenge(page) {
        try {
            for (const sel of CLOUDFLARE_SELECTORS) {
                if (page.locator && await page.locator(sel).first().count() > 0) {
                    return WafChallengeType.CLOUDFLARE_TURNSTILE;
                }
            }

            const title = typeof page.title === 'function' ? (await page.title()).toLowerCase() : '';
            if (title.includes('just a moment') || title.includes('attention required')) {
                return WafChallengeType.CLOUDFLARE_MANAGED;
            }

            for (const sel of HCAPTCHA_SELECTORS) {
                if (page.locator && await page.locator(sel).first().count() > 0) {
                    return WafChallengeType.HCAPTCHA;
                }
            }

            for (const sel of RECAPTCHA_SELECTORS) {
                if (page.locator && await page.locator(sel).first().count() > 0) {
                    return WafChallengeType.RECAPTCHA;
                }
            }
        } catch (e) {
            // Non-fatal inspection error
        }

        return WafChallengeType.NONE;
    }

    /**
     * Automatically attempts to click the Turnstile checkbox via human mouse physics.
     * @param {any} page
     * @param {Object} [options]
     * @param {HumanMouse} [options.humanMouse]
     * @param {number} [options.timeoutMs=12000]
     * @returns {Promise<boolean>}
     */
    static async solveTurnstile(page, options = {}) {
        const mouse = options.humanMouse || new HumanMouse(page);
        const timeoutMs = options.timeoutMs || 12000;
        const deadline = Date.now() + timeoutMs;

        while (Date.now() < deadline) {
            try {
                for (const frameSel of CLOUDFLARE_SELECTORS) {
                    if (page.locator && await page.locator(frameSel).first().count() > 0) {
                        const box = await page.locator(frameSel).first().boundingBox();
                        if (box && box.width > 20 && box.height > 20) {
                            const targetX = box.x + Math.min(36.0, box.width * 0.2) + (Math.random() * 8 - 4);
                            const targetY = box.y + (box.height * 0.5) + (Math.random() * 8 - 4);

                            await mouse.click({ x: targetX, y: targetY }, {
                                steps: Math.floor(Math.random() * 14) + 25,
                                jitter: true,
                                overshoot: true
                            });

                            await sleep(2000);
                            return true;
                        }
                    }
                }
            } catch (e) {
                // Retry next tick
            }

            await sleep(500);
        }

        return false;
    }
}

module.exports = {
    WafChallengeType,
    TurnstileEvaluator,
    CLOUDFLARE_SELECTORS,
    HCAPTCHA_SELECTORS,
    RECAPTCHA_SELECTORS
};
