import os
from setuptools import setup, find_packages

long_description = ""
if os.path.exists("README.md"):
    try:
        with open("README.md", encoding="utf-8") as f:
            long_description = f.read()
    except Exception:
        long_description = "Production-grade automated Playwright integration and runtime optimizer for Android Termux"

setup(
    name="termux-playwright",
    version="1.61.1",
    description="Production-grade automated Playwright integration and runtime optimizer for Android Termux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="uno-km (쌩초보코딩단)",
    author_email="hosequelbo@gmail.com",
    url="https://github.com/uno-km/termux-playwright-demo",
    packages=find_packages(),
    install_requires=[
        "greenlet>=3.1.1",
        "pyee>=13.0.0",
        "typing-extensions>=4.12.0",
    ],
    entry_points={
        'console_scripts': [
            'termux-playwright-install=termux_playwright.installer:run_installation_pipeline',
            'termux-playwright-patch=termux_playwright.patcher:apply_core_bundle_patch',
            'termux-playwright-doctor=termux_playwright.installer:doctor',
            'termux-playwright-reap=termux_playwright.reaper:ProcessReaper.reap_zombie_chromium',
        ],
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
