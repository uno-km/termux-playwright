/**
 * Termux-Playwright Node.js coreBundle.js Atomic Patcher
 * @license MIT
 */

'use strict';

const fs = require('fs');
const path = require('path');

const PATCH_SIGNATURE = 'Object.defineProperty(process, "platform"';
const PATCH_PAYLOAD = `// [Termux-Playwright Bionic Bypass]
try {
  Object.defineProperty(process, "platform", { value: "linux", configurable: true });
  Object.defineProperty(require("os"), "platform", { value: () => "linux", configurable: true });
} catch (e) {}
`;

function findCoreBundlePaths() {
    const candidates = [];
    const searchRoots = [
        process.cwd(),
        __dirname,
        path.join(__dirname, '..'),
        path.join(__dirname, '../..')
    ];

    for (const root of searchRoots) {
        const potentialPaths = [
            path.join(root, 'node_modules', 'playwright-core', 'lib', 'coreBundle.js'),
            path.join(root, 'node_modules', 'playwright', 'lib', 'coreBundle.js'),
            path.join(root, 'node_modules', 'playwright-core', 'lib', 'server', 'coreBundle.js'),
            path.join(root, 'node_modules', 'playwright', 'lib', 'server', 'coreBundle.js')
        ];
        for (const p of potentialPaths) {
            if (fs.existsSync(p) && !candidates.includes(p)) {
                candidates.push(p);
            }
        }
    }
    return candidates;
}

function applyCoreBundlePatch() {
    const bundlePaths = findCoreBundlePaths();
    let patchedCount = 0;

    for (const bundlePath of bundlePaths) {
        try {
            const content = fs.readFileSync(bundlePath, 'utf8');
            if (!content.includes(PATCH_SIGNATURE)) {
                fs.writeFileSync(bundlePath, PATCH_PAYLOAD + '\n' + content, 'utf8');
                patchedCount++;
            }
        } catch (e) {
            // Ignore permission error if read-only
        }
    }
    return patchedCount;
}

module.exports = {
    findCoreBundlePaths,
    applyCoreBundlePatch
};
