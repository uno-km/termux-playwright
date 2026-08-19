/**
 * Termux-Playwright Documentation - Multilingual Translation Dictionary
 * Languages: English (en), Chinese (zh), Japanese (ja), Korean (ko), Spanish (es), Hindi (hi)
 * @license MIT
 */

(function(global) {
    'use strict';

    const DICT = {
        'en': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.61.2 (Resilient Phantom)',
                'pypiBtn': 'PyPI Package',
                'githubBtn': 'GitHub Repository',
                'nav': {
                    'overview': 'Overview',
                    'home': 'Home / Architecture',
                    'installation': 'Installation Guide',
                    'quickstart': 'Quickstart & Recipes',
                    'apiReference': 'API Reference',
                    'advanced': 'Advanced & Deep Dives',
                    'versions': 'Version Archive & Notes',
                    'phantomProcess': 'Android 14+ Phantom Killer',
                    'koreanBlog': 'Engineering Deep-Dive'
                },
                'footerText': '© 2026 Termux-Playwright Project. Released under the MIT License.'
            },
            'home': {
                'title': 'Production-Grade Playwright Automation on Android Termux',
                'subtitle': 'Run genuine Chromium browser automation directly on ARM64 mobile hardware without root, PRoot, or X11 virtualization.',
                'whyTitle': 'The Problem: Why Upstream Playwright Fails on Android',
                'whyText': 'Upstream Playwright is hardcoded to strictly support desktop Linux glibc, macOS, and Windows. When invoked on Android Termux, it fails due to incompatible pre-compiled binaries, Bionic libc syscall differences, dynamic shared memory (/dev/shm) crashes, and Android kernel process reaping.',
                'solTitle': 'The Architectural Solution',
                'solText': 'Termux-Playwright provides native Bionic binary orchestration, targeted session process isolation (ProcessReaper), persistent disk ledger recovery (.tp_ledger), prototype-safe anti-bot stealth, and flash memory wear protection.',
                'capTitle': 'Key Capabilities & Built-in Hardening',
                'cap1': 'Zero-Root Native Execution: Orchestrates Termux-compiled Chromium and Node.js without PRoot overhead.',
                'cap2': 'Persistent Disk Session Ledger: Guarantees 100% orphan process reaping across hard kernel crashes (SIGKILL / LMK).',
                'cap3': 'Prototype-Safe Stealth: Deletes navigator.webdriver from prototype to bypass Cloudflare Turnstile & DataDome.',
                'cap4': 'Hardware Flash Wear Protection: Injects RAM-based caching to prevent eMMC mobile flash wear.',
                'cap5': 'Virtualenv System Integration: Pre-flight diagnostics and auto-repair guidance for venv environments.',
                'quickInstallTitle': '1-Line Quick Installation',
                'quickInstallDesc': 'Run this single command inside your Termux terminal to install and configure dependencies automatically:'
            }
        },
        'zh': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.61.2 (强韧幽灵)',
                'pypiBtn': 'PyPI 软件包',
                'githubBtn': 'GitHub 仓库',
                'nav': {
                    'overview': '概览',
                    'home': '首页与架构',
                    'installation': '安装指南',
                    'quickstart': '快速入门与示例',
                    'apiReference': 'API 参考手册',
                    'advanced': '高级进阶',
                    'versions': '版本历史档案',
                    'phantomProcess': 'Android 14+ 幽灵进程限制',
                    'koreanBlog': '工程深度解析'
                },
                'footerText': '© 2026 Termux-Playwright 项目。遵循 MIT 开源许可证。'
            },
            'home': {
                'title': '适用于 Android Termux 的生产级 Playwright 自动化工具',
                'subtitle': '无需 Root、无需 PRoot 或 X11 桌面虚拟化，直接在 ARM64 移动设备上运行真实的 Chromium 浏览器自动化。',
                'whyTitle': '核心痛点：为什么原生 Playwright 在 Android 上无法运行',
                'whyText': '官方 Playwright 仅支持桌面级 Linux (glibc)、macOS 和 Windows。在 Android Termux 上运行时，会因缺少预编译二进制、Bionic libc 系统调用差异、共享内存崩溃以及 Android 内核进程清理机制而直接崩溃。',
                'solTitle': '系统级架构解决方案',
                'solText': 'Termux-Playwright 提供原生 Bionic 二进制编排、基于 Session 的精准进程回收 (ProcessReaper)、持久化磁盘台账 (.tp_ledger)、原型链安全的反爬虫隐身技术以及 eMMC 闪存防磨损保护。',
                'capTitle': '核心功能与加固特性',
                'cap1': '无需 Root 原生执行：直接调度 Termux 编译的 Chromium 与 Node.js，零 PRoot 性能损耗。',
                'cap2': '持久化磁盘会话台账：在发生内核硬崩溃 (SIGKILL/LMK) 时仍能 100% 自动清理残留僵尸进程。',
                'cap3': '原型链安全隐身：彻底从原型链移除 navigator.webdriver，轻松绕过 Cloudflare Turnstile 与 DataDome。',
                'cap4': '硬件闪存防磨损：强制使用 RAM 内存缓存，防止移动设备 eMMC 寿命损耗。',
                'cap5': '虚拟环境深度集成：自动检测 venv 环境并提供 --system-site-packages 修复指引。',
                'quickInstallTitle': '单行命令极速安装',
                'quickInstallDesc': '在 Termux 终端中运行以下单行命令即可自动完成安装与依赖配置：'
            }
        },
        'ja': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.61.2 (レジリエント・ファントム)',
                'pypiBtn': 'PyPI パッケージ',
                'githubBtn': 'GitHub リポジトリ',
                'nav': {
                    'overview': '概要',
                    'home': 'ホーム / アーキテクチャ',
                    'installation': 'インストールガイド',
                    'quickstart': 'クイックスタート & レシピ',
                    'apiReference': 'API リファレンス',
                    'advanced': '高度な機能',
                    'versions': 'バージョン履歴アーカイブ',
                    'phantomProcess': 'Android 14+ ファントム制限',
                    'koreanBlog': '技術ディープダイブ'
                },
                'footerText': '© 2026 Termux-Playwright Project. MITライセンスの下で公開されています。'
            },
            'home': {
                'title': 'Android Termux向け本番グレードPlaywright自動化ツール',
                'subtitle': 'Root権限やPRoot、X11デスクトップ仮想化なしで、ARM64端末上でChromiumブラウザ自動化を直接実行。',
                'whyTitle': '背景課題：公式PlaywrightがAndroidで動作しない理由',
                'whyText': '公式PlaywrightはデスクトップLinux(glibc)、macOS、Windows向けに設計されています。Android Termux上では、Bionic libcの差異、共有メモリ(/dev/shm)クラッシュ、OSのプロセス制限により動作しません。',
                'solTitle': 'アーキテクチャによる解決策',
                'solText': 'Termux-Playwrightは、Bionicバイナリの自動検出、セッション単位のゾンビプロセス回収(ProcessReaper)、ディスク台帳による永続的復旧(.tp_ledger)、反検知ステルス機能、eMMC寿命保護を提供します。',
                'capTitle': '主要機能と堅牢化メカニズム',
                'cap1': 'Root不要のネイティブ実行：Termux環境のChromiumとNode.jsを直接制御しオーバーヘッドゼロ。',
                'cap2': '永続的ディスク台帳：カーネル強制終了(SIGKILL/LMK)後も孤立プロセスを100%自動回収。',
                'cap3': '安全なステルス偽装：navigator.webdriverを完全に偽装しCloudflare Turnstile等を回避。',
                'cap4': 'eMMCフラッシュ保護：RAMディスクキャッシュを活用しスマホのストレージ劣化を防止。',
                'cap5': '仮想環境完全サポート：venv環境におけるシステムライブラリ自動診断と修復ガイダンス。',
                'quickInstallTitle': '1行クイックインストール',
                'quickInstallDesc': 'Termuxターミナルで以下のコマンドを実行するだけで自動セットアップが完了します：'
            }
        },
        'ko': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.61.2 (Resilient Phantom)',
                'pypiBtn': 'PyPI 패키지',
                'githubBtn': 'GitHub 저장소',
                'nav': {
                    'overview': '개요',
                    'home': '홈 및 아키텍처',
                    'installation': '설치 가이드',
                    'quickstart': '빠른 시작 및 레시피',
                    'apiReference': 'API 레퍼런스',
                    'advanced': '심화 기능',
                    'versions': '버전별 기술 문서 아카이브',
                    'phantomProcess': '안드로이드 14+ 프로세스 제한 해제',
                    'koreanBlog': '한국어 기술 블로그'
                },
                'footerText': '© 2026 Termux-Playwright 프로젝트. MIT 라이선스에 따라 배포됩니다.'
            },
            'home': {
                'title': '안드로이드 Termux 전용 프로덕션급 Playwright 브라우저 자동화 툴킷',
                'subtitle': '루팅(Root), PRoot 컨테이너, X11 가상화 없이 스마트폰에서 정품 크로미움 브라우저를 24/7 백그라운드로 안전하게 구동합니다.',
                'whyTitle': '기존 Playwright가 안드로이드에서 폭발하는 이유',
                'whyText': '공식 Playwright는 데스크톱 glibc 환경만 지원합니다. 안드로이드 Bionic libc 환경에서는 바이너리 불일치, /dev/shm 공유 메모리 고갈, 프로세스 누수 및 LMK 강제 사살 문제가 발생합니다.',
                'solTitle': '시스템 레벨 아키텍처 해결책',
                'solText': 'Termux-Playwright는 네이티브 바이너리 연결, 세션 태그 기반 프로세스 정밀 사살(ProcessReaper), 디스크 영속성 장부(.tp_ledger), 프로토타입 기반 안티봇 스텔스 우회 및 eMMC 수명 보호를 제공합니다.',
                'capTitle': '주요 기능 및 하드닝 핵심',
                'cap1': '루팅 없는 네이티브 구동: Termux 크로미움 및 Node.js를 직접 제어하여 성능 손실 제로.',
                'cap2': '파일 기반 디스크 영속 장부: LMK나 SIGKILL 강제 종료 후에도 좀비 크로미움을 100% 자동 추적 사살.',
                'cap3': '프로토타입 안전 스텔스: navigator.webdriver를 완벽 제거하여 Cloudflare Turnstile 및 DataDome 우회.',
                'cap4': 'eMMC 플래시 메모리 보호: RAM 캐시를 강제 주입하여 모바일 저장장치 수명 마모 방지.',
                'cap5': '가상환경(venv) 완벽 호환: --system-site-packages 진단 및 원클릭 복구 가이드 제공.',
                'quickInstallTitle': '1초 원클릭 자동 설치',
                'quickInstallDesc': 'Termux 터미널에서 다음 명령어를 입력하면 모든 패키지와 의존성이 자동으로 세팅됩니다:'
            }
        },
        'es': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.61.2 (Fantasma Resiliente)',
                'pypiBtn': 'Paquete PyPI',
                'githubBtn': 'Repositorio GitHub',
                'nav': {
                    'overview': 'Resumen',
                    'home': 'Inicio y Arquitectura',
                    'installation': 'Guía de Instalación',
                    'quickstart': 'Inicio Rápido y Recetas',
                    'apiReference': 'Referencia de la API',
                    'advanced': 'Avanzado',
                    'versions': 'Archivo de Versiones',
                    'phantomProcess': 'Límites en Android 14+',
                    'koreanBlog': 'Documentación Técnica'
                },
                'footerText': '© 2026 Proyecto Termux-Playwright. Publicado bajo Licencia MIT.'
            },
            'home': {
                'title': 'Automatización de Playwright para Android Termux',
                'subtitle': 'Ejecute automatización real de navegadores Chromium en hardware móvil ARM64 sin root, sin PRoot y sin X11.',
                'whyTitle': 'El Problema: Por qué Playwright falla en Android',
                'whyText': 'Playwright oficial solo soporta Linux glibc, macOS y Windows. En Termux falla debido a diferencias en Bionic libc, memoria compartida (/dev/shm) y restricciones del kernel de Android.',
                'solTitle': 'La Solución Arquitectónica',
                'solText': 'Termux-Playwright proporciona orquestación binaria nativa, aislamiento de procesos por sesión (ProcessReaper), registro persistente en disco (.tp_ledger) y protección de memoria eMMC.',
                'capTitle': 'Capacidades Clave',
                'cap1': 'Ejecución Nativa Sin Root: Controla Chromium y Node.js compilados para Termux sin sobrecarga.',
                'cap2': 'Registro Persistente en Disco: Garantiza la limpieza total de procesos huérfanos incluso tras caídas del kernel (SIGKILL / LMK).',
                'cap3': 'Evasión Anti-Bot: Elimina navigator.webdriver para eludir Cloudflare Turnstile y DataDome.',
                'cap4': 'Protección de Memoria Flash: Caché forzada en RAM para evitar el desgaste de la memoria eMMC.',
                'cap5': 'Integración con Venv: Diagnóstico y guía de configuración con --system-site-packages.',
                'quickInstallTitle': 'Instalación Rápida en 1 Línea',
                'quickInstallDesc': 'Ejecute este comando en su terminal Termux para instalar y configurar automáticamente:'
            }
        },
        'hi': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.61.2 (Resilient Phantom)',
                'pypiBtn': 'PyPI पैकेज',
                'githubBtn': 'GitHub रिपॉजिटरी',
                'nav': {
                    'overview': 'अवलोकन',
                    'home': 'होम / आर्किटेक्चर',
                    'installation': 'स्थापना गाइड',
                    'quickstart': 'त्वरित शुरुआत और कोड',
                    'apiReference': 'एपीआई संदर्भ',
                    'advanced': 'उन्नत सुविधाएँ',
                    'versions': 'संस्करण पुरालेख',
                    'phantomProcess': 'Android 14+ फैंटम किलर',
                    'koreanBlog': 'तकनीकी विश्लेषण'
                },
                'footerText': '© 2026 Termux-Playwright प्रोजेक्ट। MIT लाइसेंस के तहत जारी किया गया।'
            },
            'home': {
                'title': 'Android Termux के लिए प्रोडक्शन-ग्रेड Playwright ऑटोमेशन',
                'subtitle': 'बिना रूट, बिना PRoot या X11 के ARM64 मोबाइल हार्डवेयर पर वास्तविक Chromium ब्राउज़र ऑटोमेशन चलाएं।',
                'whyTitle': 'समस्या: Playwright Android पर क्यों विफल होता है',
                'whyText': 'मूल Playwright केवल डेस्कटॉप Linux, macOS और Windows का समर्थन करता है। Android Bionic libc, साझा मेमोरी और प्रोसेस किलिंग के कारण यह Termux पर क्रैश हो जाता है।',
                'solTitle': 'वास्तुशिल्प समाधान',
                'solText': 'Termux-Playwright मूल Bionic बाइनरी आर्केस्ट्रा, सटीक प्रोसेस रीपर, डिस्क लेज़र (.tp_ledger), और एंटी-बॉट स्टील्थ तकनीक प्रदान करता है।',
                'capTitle': 'मुख्य क्षमताएं',
                'cap1': 'बिना रूट निष्पादन: Termux-संकलित Chromium और Node.js का उपयोग करता है।',
                'cap2': 'स्थायी डिस्क लेज़र: सिस्टम क्रैश (SIGKILL/LMK) के बाद भी अवांछित प्रोसेस को 100% साफ करता है।',
                'cap3': 'एंटी-बॉट स्टील्थ: Cloudflare Turnstile और DataDome को बायपास करने के लिए navigator.webdriver को हटाता है।',
                'cap4': 'हार्डवेयर फ्लैश सुरक्षा: मोबाइल स्टोरेज के घिसाव को रोकने के लिए RAM डिस्क कैश का उपयोग करता है।',
                'cap5': 'वर्चुअल पर्यावरण समर्थन: venv के लिए --system-site-packages का स्वत: निदान।',
                'quickInstallTitle': '1-लाइन त्वरित स्थापना',
                'quickInstallDesc': 'स्वचालित स्थापना के लिए अपने Termux टर्मिनल में यह कमांड चलाएं:'
            }
        }
    };

    if (global.TermuxPlaywrightI18n) {
        global.TermuxPlaywrightI18n.registerTranslations(DICT);
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            if (global.TermuxPlaywrightI18n) {
                global.TermuxPlaywrightI18n.registerTranslations(DICT);
            }
        });
    }

})(typeof window !== 'undefined' ? window : this);
