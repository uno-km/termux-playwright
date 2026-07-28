from setuptools import setup, find_packages
from setuptools.command.install import install
import sys
import os

class TermuxInstallCommand(install):
    def run(self):
        # 1. 일반적인 설치 진행
        install.run(self)
        
        # 2. 패키지가 설치된 경로를 찾아서 커스텀 설치 스크립트 실행
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from termux_playwright.installer import run_post_install
            run_post_install()
        except Exception as e:
            print(f"⚠️ Termux 커스텀 설치 로직 실행 중 에러 발생 (무시됨): {e}")

setup(
    name="termux-playwright",
    version="1.61.0",
    description="Automated Playwright installer for Android Termux (aarch64)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="uno-km (쌩초보코딩단)",
    author_email="hosequelbo@gmail.com",
    url="https://github.com/uno-km/termux-playwright-demo",
    packages=find_packages(),
    cmdclass={
        'install': TermuxInstallCommand,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
)
