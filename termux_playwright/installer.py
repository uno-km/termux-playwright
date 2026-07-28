import os
import sys
import subprocess
import urllib.request
import site

def run_post_install():
    print("\n" + "="*50)
    print("🚀 Termux-Playwright (aarch64) 자동 설치 시작...")
    print("="*50)

    # 1. Termux 환경 확인
    if "com.termux" not in os.environ.get("PREFIX", ""):
        print("⚠️ 현재 환경이 Termux가 아닙니다. 기본 Playwright 설치로 진행합니다.")
        os.system(f"{sys.executable} -m pip install playwright==1.61.0")
        return

    # 2. 시스템 패키지 설치 (chromium, nodejs)
    print("📦 1/4: 기본 시스템 패키지(Chromium, Node.js) 설치 중...")
    subprocess.run(["pkg", "install", "-y", "chromium", "nodejs"], check=False)

    # 3. 우회 휠 다운로드 및 설치
    print("📦 2/4: Playwright 1.61.0 휠 다운로드 및 우회 설치 중...")
    whl_original = "playwright-1.61.0-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl"
    whl_renamed = "playwright-1.61.0-py3-none-any.whl"
    url = "https://files.pythonhosted.org/packages/b7/eb/e3f922348ec17c315f98c463f72faa1181a1c3de0bfe31a8d2edf6561723/" + whl_original

    try:
        if not os.path.exists(whl_renamed):
            urllib.request.urlretrieve(url, whl_renamed)
        os.system(f"{sys.executable} -m pip install {whl_renamed} --force-reinstall --no-deps -q")
        os.remove(whl_renamed)
    except Exception as e:
        print(f"❌ 휠 다운로드 또는 설치 실패: {e}")
        return

    # 4. 일반 패키지 종속성 해결
    print("📦 3/4: 파이썬 의존성 패키지 설치 중...")
    os.system(f"{sys.executable} -m pip install greenlet pyee")

    # 5. coreBundle.js 자동 패치 (안드로이드 차단 우회)
    print("🔧 4/4: Playwright 안드로이드 차단 우회(coreBundle.js) 패치 중...")
    try:
        site_packages = [p for p in site.getsitepackages() if os.path.isdir(p)][0]
        core_bundle = os.path.join(site_packages, "playwright", "driver", "package", "lib", "coreBundle.js")
        
        if os.path.exists(core_bundle):
            with open(core_bundle, 'r', encoding='utf-8') as f:
                content = f.read()
            
            injection = 'Object.defineProperty(process, "platform", {value: "linux"});\nObject.defineProperty(require("os"), "platform", {value: () => "linux"});\n'
            
            if injection.split('\n')[0] not in content:
                with open(core_bundle, 'w', encoding='utf-8') as f:
                    f.write(injection + content)
                print("✅ coreBundle.js 패치 성공!")
            else:
                print("✅ 이미 패치되어 있습니다.")
        else:
            print(f"⚠️ coreBundle.js 파일을 찾을 수 없습니다: {core_bundle}")
    except Exception as e:
        print(f"❌ 패치 적용 실패: {e}")

    print("\n🎉 모든 설치가 완료되었습니다!")
    print("💡 사용하실 때 파이썬 코드에서 os.environ['PLAYWRIGHT_CHROMIUM_PATH']를 반드시 지정해 주세요.")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_post_install()
