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
    version="1.80.4",
    description="Production-grade Playwright & Chromium browser automation and stealth runtime optimizer for Android Termux (Dual-Engine Python & Node.js)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="uno-km (AMEVA Foundation)",
    author_email="hosequelbo@gmail.com",
    url="https://github.com/uno-km/termux-playwright",
    project_urls={
        "Documentation": "https://uno-km.github.io/termux-playwright/",
        "npm Package": "https://www.npmjs.com/package/termux-playwright",
        "Bug Tracker": "https://github.com/uno-km/termux-playwright/issues",
        "Source": "https://github.com/uno-km/termux-playwright",
    },
    license="MIT",
    keywords=["playwright", "termux", "android", "chromium", "automation", "web-scraping"],
    packages=find_packages(),
    package_data={
        "termux_playwright": ["py.typed"],
    },
    include_package_data=True,
    install_requires=[
        "pyee>=8.1.0,<=13.0.0",
        "typing-extensions>=4.0.0,<5.0.0",
    ],
    extras_require={
        "greenlet": ["greenlet>=3.1.1,<4.0.0"],
        "playwright": ["playwright>=1.40.0"],
    },
    entry_points={
        'console_scripts': [
            'termux-playwright-install=termux_playwright.installer:run_installation_pipeline',
            'termux-playwright-patch=termux_playwright.patcher:cli_patch_core_bundle',
            'termux-playwright-doctor=termux_playwright.installer:doctor',
            'termux-playwright-reap=termux_playwright.reaper:cli_reap_orphans',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.8",
)
