import os
import sys
import shutil
import json
import urllib.request
import tempfile
import subprocess
import importlib.util
from typing import Optional, Tuple

FALLBACK_PLAYWRIGHT_VERSION = "1.61.0"
FALLBACK_WHL_URL = (
    "https://files.pythonhosted.org/packages/b7/eb/e3f922348ec17c315f98c463f72faa1181a1c3de0bfe31a8d2edf6561723/"
    "playwright-1.61.0-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl"
)
FALLBACK_WHL_NAME = "playwright-1.61.0-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl"

def is_termux_env() -> bool:
    return "com.termux" in os.environ.get("PREFIX", "") or os.path.exists("/data/data/com.termux")

def get_playwright_dir() -> Optional[str]:
    """가상환경(venv), conda, global 어디서든 안전하게 설치된 playwright 디렉토리를 반환합니다."""
    # 1. importlib.util.find_spec 사용 (가장 표준적인 방법)
    try:
        spec = importlib.util.find_spec("playwright")
        if spec and spec.submodule_search_locations:
            return list(spec.submodule_search_locations)[0]
    except Exception:
        pass

    # 2. 직접 import 시도
    try:
        import playwright
        if hasattr(playwright, "__file__") and playwright.__file__:
            return os.path.dirname(playwright.__file__)
    except Exception:
        pass

    # 3. sysconfig purelib/platlib 검색
    try:
        import sysconfig
        for scheme in ["purelib", "platlib"]:
            path = sysconfig.get_path(scheme)
            candidate = os.path.join(path, "playwright")
            if os.path.isdir(candidate):
                return candidate
    except Exception:
        pass

    # 4. site-packages 폴백
    try:
        import site
        if hasattr(site, "getsitepackages"):
            for sp in site.getsitepackages():
                candidate = os.path.join(sp, "playwright")
                if os.path.isdir(candidate):
                    return candidate
    except Exception:
        pass

    return None

def fetch_pypi_wheel_info(version: str = FALLBACK_PLAYWRIGHT_VERSION) -> Tuple[str, str]:
    """PyPI JSON API를 조회하여 aarch64 휠 URL과 파일명을 동적으로 획득합니다."""
    api_url = f"https://pypi.org/pypi/playwright/{version}/json"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "termux-playwright-installer"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            urls = data.get("urls", [])
            for item in urls:
                filename = item.get("filename", "")
                if "aarch64" in filename and filename.endswith(".whl"):
                    download_url = item.get("url")
                    if download_url:
                        return download_url, filename
    except Exception as e:
        print(f"[!] PyPI API 실시간 휠 탐색 실패 ({e}). 기본 백업 URL로 다운로드를 진행합니다.")
        
    return FALLBACK_WHL_URL, FALLBACK_WHL_NAME

def patch_core_bundle() -> bool:
    """Playwright coreBundle.js 파일에 Android 플랫폼 체크 우회 코드를 주입합니다."""
    pw_dir = get_playwright_dir()
    if not pw_dir:
        print("[-] Playwright 패키지 경로를 찾을 수 없습니다. 먼저 패키지가 설치되었는지 확인하세요.")
        return False

    core_bundle_path = os.path.join(pw_dir, "driver", "package", "lib", "coreBundle.js")
    if not os.path.exists(core_bundle_path):
        print(f"[!] coreBundle.js 파일을 찾을 수 없습니다: {core_bundle_path}")
        return False

    try:
        with open(core_bundle_path, "r", encoding="utf-8") as f:
            content = f.read()

        injection = (
            'Object.defineProperty(process, "platform", {value: "linux"});\n'
            'Object.defineProperty(require("os"), "platform", {value: () => "linux"});\n'
        )

        if injection.split("\n")[0] in content:
            print("[+] coreBundle.js: 이미 패치되어 있습니다.")
            return True

        with open(core_bundle_path, "w", encoding="utf-8") as f:
            f.write(injection + content)
        print("[+] coreBundle.js: 안드로이드 플랫폼 검증 우회 패치 성공!")
        return True
    except Exception as e:
        print(f"[-] coreBundle.js 패치 중 에러 발생: {e}")
        return False

def doctor():
    """시스템 환경 및 Playwright 설치/패치 상태를 진단하여 리포트합니다."""
    print("\n" + "=" * 55)
    print("[*] [Termux-Playwright] 시스템 환경 진단 리포트")
    print("=" * 55)

    is_tmx = is_termux_env()
    print(f"[*] 1. Termux 환경: {'[OK] YES' if is_tmx else '[!] NO (일반 Linux/Windows 환경)'}")

    node_bin = shutil.which("node") or ("/data/data/com.termux/files/usr/bin/node" if os.path.exists("/data/data/com.termux/files/usr/bin/node") else None)
    print(f"[*] 2. Node.js 바이너리: {'[OK] ' + str(node_bin) if node_bin else '[X] 미발견 (pkg install nodejs 필요)'}")

    chrome_candidates = ["chromium-browser", "chromium", "google-chrome"]
    chrome_bin = None
    for cand in chrome_candidates:
        chrome_bin = shutil.which(cand)
        if chrome_bin:
            break
    if not chrome_bin and os.path.exists("/data/data/com.termux/files/usr/bin/chromium-browser"):
        chrome_bin = "/data/data/com.termux/files/usr/bin/chromium-browser"
    print(f"[*] 3. Chromium 바이너리: {'[OK] ' + str(chrome_bin) if chrome_bin else '[X] 미발견 (pkg install chromium 필요)'}")

    pw_dir = get_playwright_dir()
    if pw_dir:
        print(f"[*] 4. Playwright 패키지: [OK] 설치됨 ({pw_dir})")
        core_bundle = os.path.join(pw_dir, "driver", "package", "lib", "coreBundle.js")
        if os.path.exists(core_bundle):
            with open(core_bundle, "r", encoding="utf-8") as f:
                c = f.read()
            if 'Object.defineProperty(process, "platform", {value: "linux"});' in c:
                print("[*] 5. coreBundle.js 패치 상태: [OK] 패치 적용 완료")
            else:
                print("[*] 5. coreBundle.js 패치 상태: [!] 미패치 (termux-playwright-patch 필요)")
        else:
            print("[*] 5. coreBundle.js 패치 상태: [!] 파일 미발견")
    else:
        print("[*] 4. Playwright 패키지: [X] 미설치")
        print("[*] 5. coreBundle.js 패치 상태: [X] 확인 불가")

    print("=" * 55 + "\n")

def run_post_install():
    """Termux-Playwright 자동 설치 및 우회 패치 파이프라인을 실행합니다."""
    print("\n" + "=" * 55)
    print("[*] Termux-Playwright (aarch64) 자동 설치 시작...")
    print("=" * 55)

    if not is_termux_env():
        print("[!] 현재 환경이 Termux가 아닙니다. 기본 Playwright 패키지 설치를 시도합니다.")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", f"playwright=={FALLBACK_PLAYWRIGHT_VERSION}"], check=True)
            print("[+] 기본 Playwright 설치가 완료되었습니다.")
        except subprocess.CalledProcessError as e:
            print(f"[-] Playwright 설치 실패: {e}")
        return

    # 1. 시스템 패키지 설치
    print("[*] 1/4: Termux 시스템 패키지(Chromium, Node.js) 설치 중...")
    try:
        subprocess.run(["pkg", "install", "-y", "chromium", "nodejs"], check=False)
    except Exception as e:
        print(f"[!] pkg 실행 경고 (수동 설치 권장 `pkg install chromium nodejs`): {e}")

    # 2. PyPI aarch64 휠 동적 다운로드 및 임시 디렉토리에서 안전하게 우회 설치
    print(f"[*] 2/4: Playwright {FALLBACK_PLAYWRIGHT_VERSION} 휠 다운로드 및 우회 설치 중...")
    url, filename = fetch_pypi_wheel_info(FALLBACK_PLAYWRIGHT_VERSION)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        whl_path = os.path.join(temp_dir, "playwright-aarch64-renamed-any.whl")
        try:
            print(f"[*] 다운로드 중: {url}")
            urllib.request.urlretrieve(url, whl_path)
            
            # --force-reinstall --no-deps 옵션으로 termux 호환 우회 설치
            subprocess.run(
                [sys.executable, "-m", "pip", "install", whl_path, "--force-reinstall", "--no-deps", "-q"],
                check=True
            )
            print("[+] Playwright 우회 휠 설치 성공!")
        except Exception as e:
            print(f"[-] 휠 다운로드 또는 설치 실패: {e}")
            return

    # 3. 파이썬 종속성 패키지 설치
    print("[*] 3/4: 파이썬 필수 의존성 패키지(greenlet, pyee, typing-extensions) 설치 중...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "greenlet", "pyee", "typing-extensions"],
            check=True
        )
    except Exception as e:
        print(f"[!] 의존성 설치 중 경고: {e}")

    # 4. coreBundle.js 자동 패치
    print("[*] 4/4: Playwright 안드로이드 차단 우회(coreBundle.js) 패치 중...")
    patch_core_bundle()

    print("\n[+] 모든 설치 및 패치가 완료되었습니다!")
    doctor()

if __name__ == "__main__":
    run_post_install()
