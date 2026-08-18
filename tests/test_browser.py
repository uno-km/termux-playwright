from termux_playwright.browser import build_chromium_args, CORE_ANDROID_CHROMIUM_ARGS

def test_build_chromium_args_default():
    args = build_chromium_args()
    for core_arg in CORE_ANDROID_CHROMIUM_ARGS:
        assert core_arg in args
    assert "--disable-dev-shm-usage" in args
    assert "--no-sandbox" in args

def test_build_chromium_args_with_custom():
    custom = ["--window-size=1920,1080", "--user-agent=CustomUA"]
    args = build_chromium_args(custom)
    assert "--window-size=1920,1080" in args
    assert "--user-agent=CustomUA" in args
    # Ensure no duplicates if passed duplicate
    args_with_dup = build_chromium_args(["--no-sandbox", "--custom-flag"])
    assert args_with_dup.count("--no-sandbox") == 1
    assert "--custom-flag" in args_with_dup
