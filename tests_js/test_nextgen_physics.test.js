'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
    CubicBezierTrajectory,
    HumanMouse,
    HumanKeyboard,
    randomGaussian
} = require('../lib/physics');

test('physics: fittsEasing monotonic boundary conditions', () => {
    assert.equal(CubicBezierTrajectory.fittsEasing(0.0), 0.0);
    assert.ok(Math.abs(CubicBezierTrajectory.fittsEasing(1.0) - 1.0) < 1e-6);
    const mid = CubicBezierTrajectory.fittsEasing(0.5);
    assert.ok(mid >= 0.0 && mid <= 1.0);
});

test('physics: CubicBezierTrajectory generation curvature', () => {
    const trajectory = CubicBezierTrajectory.generateTrajectory(
        { x: 0, y: 0 },
        { x: 400, y: 400 },
        { steps: 30, jitter: true, overshoot: false }
    );

    assert.equal(trajectory.length, 30);
    assert.equal(trajectory[0].x, 0);
    assert.equal(trajectory[0].y, 0);
    assert.equal(trajectory[29].x, 400);
    assert.equal(trajectory[29].y, 400);

    const isNonLinear = trajectory.slice(5, 25).some(pt => Math.abs(pt.x - pt.y) > 0.5);
    assert.ok(isNonLinear, 'Trajectory should be curved and non-linear');
});

test('physics: HumanMouse moveAndRecord and click', async () => {
    const moves = [];
    let downs = 0;
    let ups = 0;

    const mockMouse = {
        move: async (x, y) => { moves.push({ x, y }); },
        down: async () => { downs++; },
        up: async () => { ups++; }
    };

    const mouse = new HumanMouse(mockMouse);
    const trajectory = await mouse.moveAndRecord(10, 10, 100, 150, { steps: 20 });

    assert.equal(trajectory.length, 20);
    assert.equal(moves.length, 20);
    assert.equal(mouse.currentX, 100);
    assert.equal(mouse.currentY, 150);

    await mouse.click([120, 180], { steps: 5 });
    assert.equal(downs, 1);
    assert.equal(ups, 1);
    assert.equal(mouse.currentX, 120);
    assert.equal(mouse.currentY, 180);
});

test('physics: HumanKeyboard typing characters', async () => {
    const typed = [];
    const mockKeyboard = {
        type: async (c) => { typed.push(c); }
    };

    await HumanKeyboard.typeText(mockKeyboard, 'Playwright', {
        meanDelay: 0.001,
        stdDev: 0.0005,
        minDelay: 0.0005,
        maxDelay: 0.002
    });

    assert.equal(typed.join(''), 'Playwright');
});
