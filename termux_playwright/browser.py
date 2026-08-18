import os
import shutil
import sys
from typing import List, Optional, Any

DEFAULT_CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--no-zygote",
]

def is_termux() -> bool:
    """Termux 환경인지 확인합니다."""
    return "com.termux" in os.environ.get("PREFIX", "") or os.path.exists("/data/data/com.termux")

def find_chromium() -> Optional[str]:
    """시스템에 설치된 Chromium 바이너리 경로를 탐색합니다."""
    # 1. 환경변수 우선 확인
    if "PLAYWRIGHT_CHROMIUM_PATH" in os.environ and os.path.exists(os.environ["PLAYWRIGHT_CHROMIUM_PATH"]):
        return os.environ["PLAYWRIGHT_CHROMIUM_PATH"]
    
    # 2. PATH 상의 실행 파일 탐색
    for binary_name in ["chromium-browser", "chromium", "google-chrome", "chrome"]:
        path = shutil.which(binary_name)
        if path:
            return path
            
    # 3. Termux 표준 경로 확인
    prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
    termux_candidates = [
        os.path.join(prefix, "bin", "chromium-browser"),
        os.path.join(prefix, "bin", "chromium"),
        "/data/data/com.termux/files/usr/bin/chromium-browser",
        "/data/data/com.termux/files/usr/bin/chromium",
    ]
    for cand in termux_candidates:
        if os.path.exists(cand):
            return cand
            
    return None

def find_nodejs() -> Optional[str]:
    """시스템에 설치된 Node.js 바이너리 경로를 탐색합니다."""
    if "PLAYWRIGHT_NODEJS_PATH" in os.environ and os.path.exists(os.environ["PLAYWRIGHT_NODEJS_PATH"]):
        return os.environ["PLAYWRIGHT_NODEJS_PATH"]
        
    path = shutil.which("node")
    if path:
        return path
        
    prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
    termux_candidates = [
        os.path.join(prefix, "bin", "node"),
        "/data/data/com.termux/files/usr/bin/node",
    ]
    for cand in termux_candidates:
        if os.path.exists(cand):
            return cand
            
    return None

def get_default_args(extra_args: Optional[List[str]] = None) -> List[str]:
    """안드로이드/Termux 환경에 최적화된 Chromium 기본 실행 인자 목록을 반환합니다."""
    args = list(DEFAULT_CHROMIUM_ARGS)
    if extra_args:
        for arg in extra_args:
            if arg not in args:
                args.append(arg)
    return args

def auto_init():
    """Termux 환경인 경우 Playwright 경로 환경변수를 자동으로 설정합니다."""
    if is_termux():
        chromium_path = find_chromium()
        if chromium_path:
            os.environ.setdefault("PLAYWRIGHT_CHROMIUM_PATH", chromium_path)
            
        node_path = find_nodejs()
        if node_path:
            os.environ.setdefault("PLAYWRIGHT_NODEJS_PATH", node_path)

async def launch(playwright_instance: Any, **kwargs) -> Any:
    """Termux 최적화 옵션으로 Playwright Chromium 브라우저를 비동기 실행합니다.
    
    사용 예:
        async with async_playwright() as p:
            browser = await termux_playwright.launch(p, headless=True)
    """
    auto_init()
    
    executable_path = kwargs.pop("executable_path", None) or find_chromium()
    user_args = kwargs.pop("args", [])
    merged_args = get_default_args(user_args)
    
    launch_kwargs = {
        "args": merged_args,
        **kwargs
    }
    if executable_path:
        launch_kwargs["executable_path"] = executable_path
        
    return await playwright_instance.chromium.launch(**launch_kwargs)

def launch_sync(playwright_instance: Any, **kwargs) -> Any:
    """Termux 최적화 옵션으로 Playwright Chromium 브라우저를 동기(Sync) 실행합니다.
    
    사용 예:
        with sync_playwright() as p:
            browser = termux_playwright.launch_sync(p, headless=True)
    """
    auto_init()
    
    executable_path = kwargs.pop("executable_path", None) or find_chromium()
    user_args = kwargs.pop("args", [])
    merged_args = get_default_args(user_args)
    
    launch_kwargs = {
        "args": merged_args,
        **kwargs
    }
    if executable_path:
        launch_kwargs["executable_path"] = executable_path
        
    return playwright_instance.chromium.launch(**launch_kwargs)
