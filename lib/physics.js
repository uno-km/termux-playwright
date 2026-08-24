/**
 * Termux-Playwright Node.js Physics & Human Interaction Engine
 * Cubic Bézier curves, Fitts's Law easing, muscle jitter, and Gaussian typing delays.
 * @license MIT
 */

'use strict';

/**
 * Standard normal distribution generator using Box-Muller transform.
 * @param {number} mean
 * @param {number} stdDev
 * @returns {number}
 */
function randomGaussian(mean = 0, stdDev = 1) {
    let u = 0, v = 0;
    while (u === 0) u = Math.random();
    while (v === 0) v = Math.random();
    const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
    return mean + z * stdDev;
}

/**
 * Sleep helper utility.
 * @param {number} ms
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class CubicBezierTrajectory {
    static calculateBezierPoint(p0, p1, p2, p3, t) {
        const u = 1.0 - t;
        const tt = t * t;
        const uu = u * u;
        const uuu = uu * u;
        const ttt = tt * t;

        const x = uuu * p0.x + 3 * uu * t * p1.x + 3 * u * tt * p2.x + ttt * p3.x;
        const y = uuu * p0.y + 3 * uu * t * p1.y + 3 * u * tt * p2.y + ttt * p3.y;
        return { x, y };
    }

    static fittsEasing(t) {
        return 0.5 * (1.0 - Math.cos(t * Math.PI));
    }

    /**
     * Generates an array of {x, y} coordinate points simulating human hand movement.
     * @param {{x: number, y: number}|number[]} start
     * @param {{x: number, y: number}|number[]} target
     * @param {Object} [options]
     * @param {number} [options.steps=30]
     * @param {boolean} [options.jitter=true]
     * @param {boolean} [options.overshoot=true]
     * @param {number} [options.deviation=0.25]
     * @returns {Array<{x: number, y: number}>}
     */
    static generateTrajectory(start, target, options = {}) {
        const p0 = Array.isArray(start) ? { x: start[0], y: start[1] } : { x: start.x, y: start.y };
        const p3 = Array.isArray(target) ? { x: target[0], y: target[1] } : { x: target.x, y: target.y };

        const steps = options.steps !== undefined ? options.steps : 30;
        const jitter = options.jitter !== false;
        const overshoot = options.overshoot !== false;
        const deviation = options.deviation || 0.25;

        if (steps <= 1) {
            return [p0, p3];
        }

        const dx = p3.x - p0.x;
        const dy = p3.y - p0.y;
        const dist = Math.hypot(dx, dy);

        const perpX = -dy;
        const perpY = dx;
        const sign1 = Math.random() > 0.5 ? 1 : -1;
        const sign2 = Math.random() > 0.5 ? 1 : -1;

        const dev1 = (Math.random() * (deviation - 0.1) + 0.1) * sign1;
        const dev2 = (Math.random() * (deviation - 0.1) + 0.1) * sign2;

        const p1 = {
            x: p0.x + dx * 0.25 + perpX * dev1,
            y: p0.y + dy * 0.25 + perpY * dev1
        };
        const p2 = {
            x: p0.x + dx * 0.75 + perpX * dev2,
            y: p0.y + dy * 0.75 + perpY * dev2
        };

        const trajectory = [];

        if (overshoot && dist > 40) {
            const overshootDist = Math.random() * Math.min(8.0, dist * 0.08 - 2.0) + 2.0;
            const angle = Math.atan2(dy, dx);
            const overshootP = {
                x: p3.x + Math.cos(angle) * overshootDist,
                y: p3.y + Math.sin(angle) * overshootDist
            };

            const mainSteps = Math.max(2, Math.floor(steps * 0.85));
            const correctSteps = steps - mainSteps;

            for (let i = 0; i < mainSteps; i++) {
                const rawT = i / (mainSteps - 1);
                const easedT = this.fittsEasing(rawT);
                const pt = this.calculateBezierPoint(p0, p1, p2, overshootP, easedT);
                if (jitter && i > 0 && i < mainSteps - 1) {
                    pt.x += randomGaussian(0, 0.4);
                    pt.y += randomGaussian(0, 0.4);
                }
                trajectory.push(pt);
            }

            for (let i = 1; i <= correctSteps; i++) {
                const rawT = i / correctSteps;
                const easedT = this.fittsEasing(rawT);
                const cx = overshootP.x + (p3.x - overshootP.x) * easedT;
                const cy = overshootP.y + (p3.y - overshootP.y) * easedT;
                trajectory.push({ x: cx, y: cy });
            }
        } else {
            for (let i = 0; i < steps; i++) {
                const rawT = i / (steps - 1);
                const easedT = this.fittsEasing(rawT);
                const pt = this.calculateBezierPoint(p0, p1, p2, p3, easedT);
                if (jitter && i > 0 && i < steps - 1) {
                    pt.x += randomGaussian(0, 0.4);
                    pt.y += randomGaussian(0, 0.4);
                }
                trajectory.push(pt);
            }
        }

        trajectory[trajectory.length - 1] = { x: p3.x, y: p3.y };
        return trajectory;
    }
}

class HumanMouse {
    /**
     * @param {any} pageOrMouse
     * @param {number} [currentX=0]
     * @param {number} [currentY=0]
     */
    constructor(pageOrMouse, currentX = 0, currentY = 0) {
        this.pageOrMouse = pageOrMouse;
        this.currentX = currentX;
        this.currentY = currentY;
    }

    _getMouse() {
        return this.pageOrMouse && this.pageOrMouse.mouse ? this.pageOrMouse.mouse : this.pageOrMouse;
    }

    /**
     * Moves mouse naturally to destination coordinates.
     * @param {number} x
     * @param {number} y
     * @param {Object} [options]
     * @returns {Promise<void>}
     */
    async moveTo(x, y, options = {}) {
        const steps = options.steps || 30;
        const jitter = options.jitter !== false;
        const overshoot = options.overshoot !== false;
        const minStepDelay = options.minStepDelay || 0.003;
        const maxStepDelay = options.maxStepDelay || 0.012;

        const trajectory = CubicBezierTrajectory.generateTrajectory(
            { x: this.currentX, y: this.currentY },
            { x, y },
            { steps, jitter, overshoot }
        );

        const mouse = this._getMouse();
        for (const pt of trajectory) {
            if (mouse && typeof mouse.move === 'function') {
                await mouse.move(pt.x, pt.y);
            }
            this.currentX = pt.x;
            this.currentY = pt.y;
            const delay = Math.random() * (maxStepDelay - minStepDelay) + minStepDelay;
            if (delay > 0) {
                await sleep(delay * 1000);
            }
        }

        this.currentX = x;
        this.currentY = y;
    }

    /**
     * Generates and executes trajectory while recording all coordinates.
     * @param {number} startX
     * @param {number} startY
     * @param {number} targetX
     * @param {number} targetY
     * @param {Object} [options]
     * @returns {Promise<Array<{x: number, y: number}>>}
     */
    async moveAndRecord(startX, startY, targetX, targetY, options = {}) {
        this.currentX = startX;
        this.currentY = startY;
        const trajectory = CubicBezierTrajectory.generateTrajectory(
            { x: startX, y: startY },
            { x: targetX, y: targetY },
            options
        );
        const mouse = this._getMouse();
        for (const pt of trajectory) {
            if (mouse && typeof mouse.move === 'function') {
                await mouse.move(pt.x, pt.y);
            }
        }
        this.currentX = targetX;
        this.currentY = targetY;
        return trajectory;
    }

    /**
     * Moves to target coordinates or selector and clicks like a human.
     * @param {string|{x: number, y: number}|number[]} target
     * @param {Object} [options]
     * @returns {Promise<void>}
     */
    async click(target, options = {}) {
        const mouse = this._getMouse();
        let targetX = 0;
        let targetY = 0;

        if (typeof target === 'string') {
            if (this.pageOrMouse && typeof this.pageOrMouse.locator === 'function') {
                const loc = this.pageOrMouse.locator(target).first();
                const box = await loc.boundingBox();
                if (box) {
                    const offX = Math.random() * (box.width * 0.5) + box.width * 0.25;
                    const offY = Math.random() * (box.height * 0.5) + box.height * 0.25;
                    targetX = box.x + offX;
                    targetY = box.y + offY;
                }
            }
        } else if (Array.isArray(target)) {
            targetX = target[0];
            targetY = target[1];
        } else if (target && typeof target.x === 'number') {
            targetX = target.x;
            targetY = target.y;
        }

        await this.moveTo(targetX, targetY, options);

        await sleep(Math.random() * 40 + 20);
        if (mouse && typeof mouse.down === 'function') {
            await mouse.down();
        }
        const holdMs = Math.random() * 100 + 60;
        await sleep(holdMs);
        if (mouse && typeof mouse.up === 'function') {
            await mouse.up();
        }
    }
}

class HumanKeyboard {
    static getGaussianDelay(mean = 0.12, stdDev = 0.035, minD = 0.02, maxD = 0.4) {
        const delay = randomGaussian(mean, stdDev);
        return Math.max(minD, Math.min(maxD, delay));
    }

    /**
     * Types text character by character with human-like Gaussian delays.
     * @param {any} pageOrKeyboard
     * @param {string} text
     * @param {Object} [options]
     * @param {string} [options.selector]
     * @param {number} [options.meanDelay=0.12]
     * @param {number} [options.stdDev=0.035]
     * @param {number} [options.minDelay=0.02]
     * @param {number} [options.maxDelay=0.4]
     * @returns {Promise<void>}
     */
    static async typeText(pageOrKeyboard, text, options = {}) {
        const {
            selector = null,
            meanDelay = 0.12,
            stdDev = 0.035,
            minDelay = 0.02,
            maxDelay = 0.4
        } = options;

        if (selector && pageOrKeyboard && typeof pageOrKeyboard.locator === 'function') {
            await pageOrKeyboard.locator(selector).first().focus();
        }

        const keyboard = pageOrKeyboard && pageOrKeyboard.keyboard ? pageOrKeyboard.keyboard : pageOrKeyboard;

        for (const char of text) {
            if (keyboard && typeof keyboard.type === 'function') {
                await keyboard.type(char);
            }
            let delay = this.getGaussianDelay(meanDelay, stdDev, minDelay, maxDelay);
            if (' ,.!?\n'.includes(char)) {
                delay += Math.random() * 0.1 + 0.05;
            }
            await sleep(delay * 1000);
        }
    }
}

module.exports = {
    CubicBezierTrajectory,
    HumanMouse,
    HumanKeyboard,
    randomGaussian
};
