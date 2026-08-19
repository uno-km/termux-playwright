#!/bin/sh
set -e
echo "================================================================="
echo "   Termux-Playwright Automated Installer"
echo "================================================================="
if [ -z "${PREFIX:-}" ] && [ ! -d "/data/data/com.termux" ]; then
    echo "[*] Non-Termux environment detected. Installing standard Playwright..."
    python3 -m pip install --upgrade pip setuptools --quiet
    python3 -m pip install termux-playwright --quiet
    termux-playwright-install
    termux-playwright-doctor
    echo "[+] Installation complete."
    exit 0
fi
ARCH=$(uname -m)
echo "[*] Termux environment detected (Architecture: ${ARCH})"
if [ "${ARCH}" != "aarch64" ] && [ "${ARCH}" != "arm64" ]; then
    echo "[!] Warning: Architecture is not aarch64. Running in compatibility mode."
fi
echo "[1/4] Installing Termux system packages..."
pkg update -y || apt update -y || true
pkg install -y chromium nodejs python python-greenlet procps termux-api || apt-get install -y --fix-missing chromium nodejs python python-greenlet procps termux-api
echo "[2/4] Installing Python base dependencies..."
python3 -m pip install --upgrade pip setuptools --quiet
python3 -m pip install pyee typing-extensions termux-playwright --prefer-binary --quiet
echo "[3/4] Installing Playwright wheel and applying core patch..."
termux-playwright-install
echo "[4/4] Verifying system readiness..."
termux-playwright-doctor
echo "================================================================="
echo "   Termux-Playwright Installation Completed Successfully"
echo "================================================================="
