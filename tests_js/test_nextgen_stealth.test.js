'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
    generateStealthScript,
    CanvasNoiseInjector,
    AudioNoiseInjector,
    StealthEngine
} = require('../lib/stealth');

test('stealth: generateStealthScript default outputs full evasion payload', () => {
    const script = generateStealthScript();
    assert.ok(script.includes('navigator.webdriver'));
    assert.ok(script.includes('window.chrome'));
    assert.ok(script.includes('Canvas 2D LSB Noise Injector'));
    assert.ok(script.includes('AudioContext Frequency Deviation'));
    assert.ok(script.includes('WebGL context proxy'));
});

test('stealth: generateStealthScript granular feature toggles', () => {
    const scriptDisabled = generateStealthScript({
        enableCanvasNoise: false,
        enableAudioNoise: false,
        enableWebglMask: false
    });
    assert.ok(!scriptDisabled.includes('Canvas 2D LSB Noise Injector'));
    assert.ok(!scriptDisabled.includes('AudioContext Frequency Deviation'));
    assert.ok(!scriptDisabled.includes('WebGL context proxy'));
    assert.ok(scriptDisabled.includes('window.chrome'));

    const scriptCanvasOnly = generateStealthScript({
        enableCanvasNoise: true,
        enableAudioNoise: false,
        enableWebglMask: false,
        enableWebdriverMask: false,
        enableChromeMock: false,
        canvasNoiseSeed: 777
    });
    assert.ok(scriptCanvasOnly.includes('Canvas 2D LSB Noise Injector'));
    assert.ok(scriptCanvasOnly.includes('const SEED_OFFSET = 777;'));
    assert.ok(!scriptCanvasOnly.includes('navigator.webdriver'));
});

test('stealth: CanvasNoiseInjector and AudioNoiseInjector execution with mock page', async () => {
    const injected = [];
    const mockPage = {
        addInitScript: async (s) => { injected.push(s); }
    };

    await CanvasNoiseInjector.inject(mockPage, 555);
    assert.equal(injected.length, 1);
    assert.ok(injected[0].includes('SEED_OFFSET = 555;'));

    await AudioNoiseInjector.inject(mockPage);
    assert.equal(injected.length, 2);
    assert.ok(injected[1].includes('AudioBuffer'));
});
