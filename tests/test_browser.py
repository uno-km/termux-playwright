import pytest
from termux_playwright.browser import (
    build_chromium_args,
    configure_environment,
    CORE_ANDROID_CHROMIUM_ARGS,
    LOW_MEMORY_CHROMIUM_ARGS,
    JITLESS_CHROMIUM_ARGS,
)
from termux_playwright.exceptions import BinaryNotFoundError

def test_build_chromium_args_default():
    args = build_chromium_args()
    for core_arg in CORE_ANDROID_CHROMIUM_ARGS:
        assert core_arg in args
    assert "--disable-dev-shm-usage" in args
    assert "--disk-cache-dir=/dev/null" in args
    assert "--ignore-certificate-errors" in args
    assert "--no-sandbox" in args

def test_build_chromium_args_low_memory():
    args = build_chromium_args(low_memory_mode=True)
    for low_arg in LOW_MEMORY_CHROMIUM_ARGS:
        assert low_arg in args

def test_build_chromium_args_jitless():
    args = build_chromium_args(jitless=True)
    for jit_arg in JITLESS_CHROMIUM_ARGS:
        assert jit_arg in args

def test_build_chromium_args_with_session_and_custom():
    custom = ["--window-size=1920,1080"]
    args = build_chromium_args(custom, session_token="test_sess_123")
    assert "--termux-session-id=test_sess_123" in args
    assert "--window-size=1920,1080" in args

def test_configure_environment_sets_node_memory_and_checks_strict(monkeypatch):
    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")
    monkeypatch.setattr("termux_playwright.browser.find_node_binary", lambda: "/mock/node")
    
    cfg = configure_environment(strict=True)
    assert cfg["NODE_OPTIONS"] == "--max-old-space-size=256"
    assert cfg["PLAYWRIGHT_CHROMIUM_PATH"] == "/mock/chromium"
    assert cfg["PLAYWRIGHT_NODEJS_PATH"] == "/mock/node"
