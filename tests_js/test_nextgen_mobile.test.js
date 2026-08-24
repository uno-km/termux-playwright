'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
    RotationMode,
    CellularIpRotator,
    DEFAULT_IP_ENDPOINTS
} = require('../lib/mobile');

test('mobile: CellularIpRotator options and command building', () => {
    const rotatorAdb = new CellularIpRotator({
        mode: RotationMode.PC_ADB_BRIDGE,
        deviceId: 'emulator-5554'
    });

    assert.equal(rotatorAdb.mode, RotationMode.PC_ADB_BRIDGE);
    assert.equal(rotatorAdb.deviceId, 'emulator-5554');

    const cmdAdb = rotatorAdb._buildShellCmd('cmd connectivity airplane-mode enable');
    assert.ok(cmdAdb.includes('adb -s emulator-5554 shell'));

    const rotatorTermux = new CellularIpRotator({
        mode: RotationMode.TERMUX_NATIVE
    });
    const cmdTermux = rotatorTermux._buildShellCmd('cmd connectivity airplane-mode enable');
    assert.ok(cmdTermux.startsWith('sh -c'));
});

test('mobile: CellularIpRotator mocked rotateIp execution', async () => {
    const rotator = new CellularIpRotator({
        mode: RotationMode.TERMUX_NATIVE,
        toggleWaitSeconds: 0.01,
        settleWaitSeconds: 0.01
    });

    rotator._executeShell = async () => true;

    const ips = ['203.0.113.1', '203.0.113.2'];
    let count = 0;
    rotator.getPublicIp = async () => {
        const ip = ips[Math.min(count, ips.length - 1)];
        count++;
        return ip;
    };

    const res = await rotator.rotateIp({ verifyIpChange: true });
    assert.equal(res.success, true);
    assert.equal(res.old_ip, '203.0.113.1');
    assert.equal(res.new_ip, '203.0.113.2');
});
