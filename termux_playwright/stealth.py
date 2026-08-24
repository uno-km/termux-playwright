"""Anti-bot stealth and evasion engine for termux-playwright.

Provides prototype-safe fingerprint masking, Sub-pixel Canvas 2D LSB noise injection,
AudioContext frequency deviation noise injection, and WebGL hardware masking.
All features are individually toggleable via parameters.
"""

import logging
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)


def generate_stealth_script(
    enable_canvas_noise: bool = True,
    enable_audio_noise: bool = True,
    enable_webgl_mask: bool = True,
    enable_webdriver_mask: bool = True,
    enable_chrome_mock: bool = True,
    enable_permissions_mock: bool = True,
    enable_plugins_mock: bool = True,
    canvas_noise_seed: Optional[int] = None,
) -> str:
    """Generates the customizable JavaScript payload for anti-bot browser initialization.

    Args:
        enable_canvas_noise: Injects 1-bit LSB noise into 10x10 top-left pixels of Canvas 2D.
        enable_audio_noise: Injects micro frequency noise into AudioBuffer / AnalyserNode.
        enable_webgl_mask: Spoofs WebGL unmasked vendor and renderer.
        enable_webdriver_mask: Deletes navigator.webdriver from prototype chain.
        enable_chrome_mock: Mocks window.chrome runtime and app APIs.
        enable_permissions_mock: Spoofs Notification query with native toString.
        enable_plugins_mock: Injects standard Chrome PDF plugins.
        canvas_noise_seed: Optional integer seed for deterministic noise testing.

    Returns:
        JavaScript string to be passed to context.add_init_script or page.add_init_script.
    """
    parts = ["(() => {", "  'use strict';"]

    if enable_webdriver_mask:
        parts.append("""
  // 1. Prototype-safe navigator.webdriver cleaning
  try {
    const proto = Object.getPrototypeOf(navigator);
    if ('webdriver' in proto) {
      delete proto.webdriver;
    }
    if (navigator.hasOwnProperty('webdriver')) {
      delete navigator.webdriver;
    }
  } catch (e) {}
""")

    if enable_chrome_mock:
        parts.append("""
  // 2. Mock realistic window.chrome runtime & app objects
  try {
    if (!window.chrome) {
      window.chrome = {};
    }
    if (!window.chrome.app) {
      window.chrome.app = {
        isInstalled: false,
        InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
        RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
      };
    }
    if (!window.chrome.runtime) {
      window.chrome.runtime = {
        OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
        OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
        PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
        PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
        PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
        RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' }
      };
    }
  } catch (e) {}
""")

    if enable_permissions_mock:
        parts.append("""
  // 3. Fix navigator.permissions.query with native-looking toString
  try {
    if (window.navigator && window.navigator.permissions && window.navigator.permissions.query) {
      const originalQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
      const patchedQuery = (parameters) => (
        parameters && parameters.name === 'notifications' ?
          Promise.resolve({ state: Notification.permission }) :
          originalQuery(parameters)
      );
      try {
        patchedQuery.toString = () => 'function query() { [native code] }';
      } catch (e) {}
      window.navigator.permissions.query = patchedQuery;
    }
  } catch (e) {}
""")

    if enable_plugins_mock:
        parts.append("""
  // 4. Standard Chrome PDF Viewer plugin definitions
  try {
    if (!navigator.plugins || navigator.plugins.length === 0) {
      const pluginArray = [
        { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
        { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
        { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }
      ];
      Object.defineProperty(navigator, 'plugins', {
        get: () => pluginArray,
        configurable: true
      });
    }
  } catch (e) {}
""")

    if enable_webgl_mask:
        parts.append("""
  // 5. WebGL context proxy & UNMASKED_VENDOR/RENDERER spoofing
  try {
    const origGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, attributes) {
      const ctx = origGetContext.apply(this, arguments);
      if (ctx && (type === 'webgl' || type === 'experimental-webgl' || type === 'webgl2')) {
        const origGetParam = ctx.getParameter ? ctx.getParameter.bind(ctx) : null;
        if (origGetParam) {
          ctx.getParameter = function(param) {
            if (param === 37445) return 'Google Inc. (Intel)';
            if (param === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            if (param === 7936) return 'WebKit';
            if (param === 7937) return 'WebKit WebGL';
            if (param === 7938) return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
            if (param === 35724) return 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)';
            return origGetParam(param);
          };
        }
      }
      return ctx;
    };
    if (typeof WebGLRenderingContext !== 'undefined') {
      const origGetParam = WebGLRenderingContext.prototype.getParameter;
      WebGLRenderingContext.prototype.getParameter = function(param) {
        if (param === 37445) return 'Google Inc. (Intel)';
        if (param === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)';
        return origGetParam.apply(this, arguments);
      };
    }
  } catch (e) {}
""")

    if enable_canvas_noise:
        seed_clause = f"const SEED_OFFSET = {canvas_noise_seed if canvas_noise_seed is not None else 'Math.floor(Math.random() * 1000) + 1'};"
        parts.append(f"""
  // 6. Sub-pixel Canvas 2D LSB Noise Injector
  try {{
    {seed_clause}
    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;

    CanvasRenderingContext2D.prototype.getImageData = function(sx, sy, sw, sh) {{
      const imageData = origGetImageData.apply(this, arguments);
      try {{
        const data = imageData.data;
        const len = Math.min(data.length, 400); // 10x10 pixel bounding box
        for (let i = 0; i < len; i += 4) {{
          // Mutate the Least Significant Bit (LSB) of RGBA channels
          data[i] = data[i] ^ ((SEED_OFFSET + i) % 2);
          data[i + 1] = data[i + 1] ^ (((SEED_OFFSET >> 1) + i) % 2);
          data[i + 2] = data[i + 2] ^ (((SEED_OFFSET >> 2) + i) % 2);
        }}
      }} catch (err) {{}}
      return imageData;
    }};

    HTMLCanvasElement.prototype.toDataURL = function(type, encoderOptions) {{
      try {{
        const ctx = this.getContext('2d');
        if (ctx && this.width > 0 && this.height > 0) {{
          const imgData = ctx.getImageData(0, 0, Math.min(this.width, 10), Math.min(this.height, 10));
          ctx.putImageData(imgData, 0, 0);
        }}
      }} catch (err) {{}}
      return origToDataURL.apply(this, arguments);
    }};
  }} catch (e) {{}}
""")

    if enable_audio_noise:
        parts.append("""
  // 7. AudioContext Frequency Deviation Noise Injector
  try {
    if (typeof AudioBuffer !== 'undefined') {
      const origGetChannelData = AudioBuffer.prototype.getChannelData;
      AudioBuffer.prototype.getChannelData = function(channel) {
        const data = origGetChannelData.apply(this, arguments);
        try {
          const step = Math.max(1, Math.floor(data.length / 100));
          for (let i = 0; i < data.length; i += step) {
            const noise = (Math.random() - 0.5) * 1e-7;
            data[i] = data[i] + noise;
          }
        } catch (err) {}
        return data;
      };
    }

    if (typeof AnalyserNode !== 'undefined') {
      const origGetFloatFreq = AnalyserNode.prototype.getFloatFrequencyData;
      AnalyserNode.prototype.getFloatFrequencyData = function(array) {
        origGetFloatFreq.apply(this, arguments);
        try {
          for (let i = 0; i < array.length; i += 4) {
            array[i] += (Math.random() - 0.5) * 0.1;
          }
        } catch (err) {}
      };
    }
  } catch (e) {}
""")

    parts.append("})();")
    return "\n".join(parts)


class CanvasNoiseInjector:
    """Canvas 2D sub-pixel LSB noise injector for Playwright pages and contexts."""

    @staticmethod
    async def inject(page_or_context: Any, seed: Optional[int] = None) -> None:
        """Injects Canvas 2D LSB noise into the specified Playwright Page or BrowserContext asynchronously."""
        script = generate_stealth_script(
            enable_canvas_noise=True,
            enable_audio_noise=False,
            enable_webgl_mask=False,
            enable_webdriver_mask=False,
            enable_chrome_mock=False,
            enable_permissions_mock=False,
            enable_plugins_mock=False,
            canvas_noise_seed=seed,
        )
        if hasattr(page_or_context, "add_init_script"):
            await page_or_context.add_init_script(script)
        elif hasattr(page_or_context, "evaluate"):
            await page_or_context.evaluate(script)

    @staticmethod
    def inject_sync(page_or_context: Any, seed: Optional[int] = None) -> None:
        """Injects Canvas 2D LSB noise into the specified Playwright Page or BrowserContext synchronously."""
        script = generate_stealth_script(
            enable_canvas_noise=True,
            enable_audio_noise=False,
            enable_webgl_mask=False,
            enable_webdriver_mask=False,
            enable_chrome_mock=False,
            enable_permissions_mock=False,
            enable_plugins_mock=False,
            canvas_noise_seed=seed,
        )
        if hasattr(page_or_context, "add_init_script"):
            page_or_context.add_init_script(script)
        elif hasattr(page_or_context, "evaluate"):
            page_or_context.evaluate(script)


class AudioNoiseInjector:
    """AudioContext frequency deviation noise injector for Playwright pages and contexts."""

    @staticmethod
    async def inject(page_or_context: Any) -> None:
        """Injects AudioContext frequency noise into the specified Playwright Page or BrowserContext asynchronously."""
        script = generate_stealth_script(
            enable_canvas_noise=False,
            enable_audio_noise=True,
            enable_webgl_mask=False,
            enable_webdriver_mask=False,
            enable_chrome_mock=False,
            enable_permissions_mock=False,
            enable_plugins_mock=False,
        )
        if hasattr(page_or_context, "add_init_script"):
            await page_or_context.add_init_script(script)
        elif hasattr(page_or_context, "evaluate"):
            await page_or_context.evaluate(script)

    @staticmethod
    def inject_sync(page_or_context: Any) -> None:
        """Injects AudioContext frequency noise into the specified Playwright Page or BrowserContext synchronously."""
        script = generate_stealth_script(
            enable_canvas_noise=False,
            enable_audio_noise=True,
            enable_webgl_mask=False,
            enable_webdriver_mask=False,
            enable_chrome_mock=False,
            enable_permissions_mock=False,
            enable_plugins_mock=False,
        )
        if hasattr(page_or_context, "add_init_script"):
            page_or_context.add_init_script(script)
        elif hasattr(page_or_context, "evaluate"):
            page_or_context.evaluate(script)


class StealthEngine:
    """Full-featured stealth orchestration engine."""

    @staticmethod
    def build_script(
        enable_canvas_noise: bool = True,
        enable_audio_noise: bool = True,
        enable_webgl_mask: bool = True,
        enable_webdriver_mask: bool = True,
        enable_chrome_mock: bool = True,
        enable_permissions_mock: bool = True,
        enable_plugins_mock: bool = True,
        canvas_noise_seed: Optional[int] = None,
    ) -> str:
        """Constructs an integrated anti-bot initialization script with granular toggle parameters."""
        return generate_stealth_script(
            enable_canvas_noise=enable_canvas_noise,
            enable_audio_noise=enable_audio_noise,
            enable_webgl_mask=enable_webgl_mask,
            enable_webdriver_mask=enable_webdriver_mask,
            enable_chrome_mock=enable_chrome_mock,
            enable_permissions_mock=enable_permissions_mock,
            enable_plugins_mock=enable_plugins_mock,
            canvas_noise_seed=canvas_noise_seed,
        )
