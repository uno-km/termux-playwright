from setuptools import setup, find_packages
from setuptools.command.install import install
import sys
import os

class TermuxInstallCommand(install):
    def run(self):
        # 1. 일반적인 설치 진행
        install.run(self)
        
        # 2. Termux 환경일 때만 커스텀 설치 스크립트 실행 (빌드 환경 오염 방지)
        if "com.termux" in os.environ.get("PREFIX", "") or os.path.exists("/data/data/com.termux"):
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from termux_playwright.installer import run_post_install
                run_post_install()
            except Exception as e:
                print(f"[!] Termux 커스텀 설치 로직 실행 중 에러 발생 (무시됨): {e}")

long_description = ""
if os.path.exists("README.md"):
    try:
        with open("README.md", encoding="utf-8") as f:
            long_description = f.read()
    except Exception:
        long_description = "Automated Playwright installer and runtime optimizer for Android Termux (aarch64)"

setup(
    name="termux-playwright",
    version="1.61.1",
    description="Automated Playwright installer and runtime optimizer for Android Termux (aarch64)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="uno-km (쌩초보코딩단)",
    author_email="hosequelbo@gmail.com",
    url="https://github.com/uno-km/termux-playwright-demo",
    packages=find_packages(),
    install_requires=[
        "greenlet",
        "pyee",
        "typing-extensions",
    ],
    entry_points={
        'console_scripts': [
            'termux-playwright-install=termux_playwright.installer:run_post_install',
            'termux-playwright-patch=termux_playwright.installer:patch_core_bundle',
            'termux-playwright-doctor=termux_playwright.installer:doctor',
        ],
    },
    cmdclass={
        'install': TermuxInstallCommand,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Android",
        "Environment :: Console",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    python_requires=">=3.8",
)
