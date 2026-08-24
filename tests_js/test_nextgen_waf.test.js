'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
    WafChallengeType,
    TurnstileEvaluator,
    CLOUDFLARE_SELECTORS
} = require('../lib/waf');

test('waf: challenge detection for Cloudflare Turnstile and title challenge', async () => {
    const cfPage = {
        locator: (sel) => ({
            first: () => ({
                count: async () => (sel.includes('challenges.cloudflare.com') ? 1 : 0),
                boundingBox: async () => ({ x: 50, y: 100, width: 250, height: 60 })
            })
        }),
        title: async () => 'Cloudflare Verification'
    };

    const detected = await TurnstileEvaluator.detectChallenge(cfPage);
    assert.equal(detected, WafChallengeType.CLOUDFLARE_TURNSTILE);

    const managedPage = {
        locator: () => ({
            first: () => ({
                count: async () => 0
            })
        }),
        title: async () => 'Just a moment...'
    };

    const detectedManaged = await TurnstileEvaluator.detectChallenge(managedPage);
    assert.equal(detectedManaged, WafChallengeType.CLOUDFLARE_MANAGED);
});

test('waf: solveTurnstile on mock page', async () => {
    let downs = 0;
    let ups = 0;
    const moves = [];

    const mockMouse = {
        move: async (x, y) => { moves.push({ x, y }); },
        down: async () => { downs++; },
        up: async () => { ups++; }
    };

    const cfPage = {
        locator: (sel) => ({
            first: () => ({
                count: async () => (sel.includes('challenges.cloudflare.com') ? 1 : 0),
                boundingBox: async () => ({ x: 50, y: 100, width: 250, height: 60 })
            })
        }),
        mouse: mockMouse
    };

    const solved = await TurnstileEvaluator.solveTurnstile(cfPage, { timeoutMs: 1000 });
    assert.equal(solved, true);
    assert.equal(downs, 1);
    assert.equal(ups, 1);
});
