# 👻 Complete Guide: Disabling Android Phantom Process Killer

This comprehensive guide provides step-by-step instructions for permanently disabling the **Phantom Process Killer** on **Android 12, 13, 14, and newer** devices to ensure 24/7 uninterrupted web crawling with Chromium and Termux.

---

## 🧐 What is the Phantom Process Killer?

Starting with **Android 12 (API level 31)**, Google introduced the *Phantom Process Killer* subsystem inside the Android Activity Manager.

### How It Works:
1. When an application (such as **Termux**) runs in the background, it can spawn child sub-processes (such as Chromium browser, Node.js RPC server, Python worker threads).
2. Android OS monitors all child processes spawned by background apps.
3. If an application's total child process count **exceeds 32 processes**, the Android kernel's Activity Manager automatically and silently terminates excess processes using `SIGKILL` (`kill -9`).
4. In Chromium, each tab, renderer, audio service, and GPU worker is a separate process. Visiting complex Single-Page Applications (SPAs) quickly spawns 35+ processes, causing the Android OS to abruptly assassinate Chromium renderers with `Page crashed` / `Target closed` errors.

---

## 🛠️ Method 1: Disabling via USB Debugging from PC / Mac / Linux (Recommended)

This is the standard and most reliable method. It requires a computer and a USB cable.

### Step 1: Enable Developer Options on Android
1. Open Android **Settings**.
2. Navigate to **About Phone** (or **System** $\rightarrow$ **About Device**).
3. Locate **Build Number** and tap it **7 times consecutively**.
4. You will see a toast notification: *"You are now a developer!"*

### Step 2: Enable USB Debugging
1. Go back to **Settings** $\rightarrow$ **System** $\rightarrow$ **Developer Options** (or search for "Developer Options").
2. Scroll down to the **Debugging** section.
3. Toggle **USB Debugging** to **ON**.
4. *(Optional for some OEM devices)*: Also enable **"USB Debugging (Security settings)"** if prompted.

### Step 3: Install ADB (Android Debug Bridge) on your Computer
If you do not have ADB installed on your computer, install it with one command:

* **Windows (via winget or Chocolatey):**
  ```powershell
  winget install Google.PlatformTools
  # or: choco install adb
  ```
* **macOS (via Homebrew):**
  ```bash
  brew install android-platform-tools
  ```
* **Linux (Ubuntu / Debian / Arch / Fedora):**
  ```bash
  sudo apt install adb       # Ubuntu / Debian
  sudo pacman -S android-tools # Arch Linux
  sudo dnf install android-tools # Fedora
  ```

### Step 4: Connect Smartphone and Authorize Connection
1. Connect your smartphone to your computer using a USB cable.
2. Open a terminal (Terminal / Command Prompt / PowerShell) on your computer and run:
   ```bash
   adb devices
   ```
3. A popup will appear on your smartphone screen: **"Allow USB debugging from this computer?"**.
4. Check **"Always allow from this computer"** and tap **Allow**.
5. Run `adb devices` again. Your device should be listed as `device` (not `unauthorized`):
   ```text
   List of devices attached
   RFCW10ABCDE    device
   ```

### Step 5: Execute the Phantom Killer Disable Commands
Run the following two commands in your computer's terminal:

```bash
# 1. Raise the phantom process ceiling to maximum integer (2.14 billion)
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"

# 2. Prevent Android OS from periodically resetting the configuration
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"
```

### Step 6: Verify Successful Application
Confirm that the new setting is active by running:

```bash
adb shell "/system/bin/device_config get activity_manager max_phantom_processes"
```

**Expected Output:**
```text
2147483647
```

---

## 📶 Method 2: Disabling Directly on Android via Wireless Debugging (No PC Required)

If your device runs **Android 11+** and is connected to Wi-Fi, you can disable the Phantom Killer directly on the smartphone without a PC using Termux and Android's native Wireless Debugging.

### Step 1: Install ADB inside Termux
Open Termux and install the android-tools package:
```bash
pkg install -y android-tools
```

### Step 2: Enable Wireless Debugging
1. Connect your smartphone to a Wi-Fi network.
2. Open **Settings** $\rightarrow$ **Developer Options** $\rightarrow$ **Wireless Debugging**.
3. Toggle **Wireless Debugging** to **ON**.
4. Tap on **"Pair device with pairing code"**.
5. You will see:
   * **Wi-Fi pairing code** (e.g. `123456`)
   * **IP address & Port** (e.g. `192.168.1.50:37123`)

### Step 3: Pair and Connect in Termux
1. Split-screen or use Termux notification to view the code, then run:
   ```bash
   adb pair 127.0.0.1:<pairing_port>
   # Enter the 6-digit pairing code when prompted
   ```
2. Check the main Wireless Debugging screen for the active connection port (e.g. `192.168.1.50:41234`) and connect:
   ```bash
   adb connect 127.0.0.1:<connection_port>
   ```

### Step 4: Run the Disable Command
```bash
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"
```

---

## 🛡️ Method 3: Software-Level Mitigation (`single_process=True`) (Zero Setup)

If you cannot access ADB or do not wish to modify device settings, `termux-playwright` provides a built-in software mitigation:

```python
import asyncio
from termux_playwright import async_playwright_termux, launch

async def main():
    async with async_playwright_termux() as p:
        # single_process=True collapses all Chromium tabs into 1 process,
        # bypassing the 32-process limit completely!
        browser = await launch(p, headless=True, single_process=True)
        page = await browser.new_page()
        await page.goto("https://example.com")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## ❓ Frequently Asked Questions (FAQ)

### Q1: Does this setting persist after restarting the phone?
On **Android 12L, 13, and 14**, running `/system/bin/device_config set_sync_disabled_for_tests persistent` ensures the setting persists across device restarts on most standard Android builds. On some aggressive OEM ROMs, if the setting resets after a major system update, simply rerun the command or use `single_process=True`.

### Q2: Does disabling the Phantom Process Killer drain battery?
No. The Phantom Process Killer only monitors background sub-process counts. It does not alter CPU clock speeds, GPU performance, or deep sleep behavior.

### Q3: How do I revert back to the default setting?
To restore default Android OS behavior, run:
```bash
adb shell "/system/bin/device_config delete activity_manager max_phantom_processes"
adb shell "/system/bin/device_config set_sync_disabled_for_tests none"
```
