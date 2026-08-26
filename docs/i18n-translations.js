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
                'releaseTag': 'v1.80.1 (Dual Engine)',
                'pypiBtn': 'PyPI (Python)',
                'npmBtn': 'npm (Node.js)',
                'githubBtn': 'GitHub Repository',
                'nav': {
                    'overview': 'Overview',
                    'home': 'Home / Architecture',
                    'installation': 'Installation Guide',
                    'quickstart': 'Quickstart & Recipes',
                    'nodejs': 'Node.js & Memory Guide',
                    'apiReference': 'API Reference',
                    'versions': 'Version Archive & Notes',
                    'phantomProcess': 'Android 14+ Phantom Killer',
                    'koreanBlog': 'Engineering Deep-Dive'
                },
                'footerText': '© 2026 Termux-Playwright Project. Released under the MIT License.'
            },
            'home': {
                'title': 'Production-Grade Playwright Automation on Android Termux',
                'subtitle': 'Dual-engine (Python & Node.js) Chromium browser automation on ARM64 mobile hardware without root, PRoot, or X11 virtualization.',
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
                'quickInstallTitle': '1-Line Quick Installation (Choose Language)',
                'quickInstallDesc': 'Select your preferred runtime and run the 1-line installation command in Termux:'
            },
            'nodejs': {
                'title': 'Dual-Engine Architecture: Node.js & Memory Management',
                'subtitle': 'Deep-dive on CPython vs V8 Garbage Collection, libuv stream buffers, and Android LMK survival strategies.',
                'divergenceTitle': '1. CPython vs V8 Memory & GC Divergence on Android',
                'divergenceDesc': 'Python relies on deterministic Reference Counting to immediately free memory upon scope exit. In contrast, Node.js V8 uses Generational Scavenge & Mark-Sweep-Compact with Lazy GC, keeping heap allocated until pressure builds. On mobile devices with 1GB-4GB RAM, default V8 heap limits (1.4GB) trigger Android Low Memory Killer (LMK) execution.',
                'actionsTitle': '2. Hardened Runtime Protections (Audit Actions Applied)',
                'action1Title': 'Synchronous Signal & Exit Reaper',
                'action1Desc': 'In Node.js, process.on("exit") permanently shuts down the event loop—async calls are ignored. ProcessReaper uses pure synchronous C-level process.kill and fs.unlinkSync to guarantee zero zombie leaks.',
                'action2Title': 'Uncaught Crash Handlers (uncaughtException & unhandledRejection)',
                'action2Desc': 'Unhandled Promise rejections and uncaught exceptions automatically trigger synchronous ProcessReaper.killAllTracked() before process termination.',
                'action3Title': 'V8 Heap Capping & forceGarbageCollection()',
                'action3Desc': 'Low-memory mode caps V8 heap at 128MB. The forceGarbageCollection() helper flushes V8 young/old generation heaps during long-running crawler cycles.',
                'recipesTitle': '3. Node.js / TypeScript Production Recipes',
                'pm2Title': '4. 24/7 Unattended Mobile Daemon with PM2'
            }
        },
        'zh': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.61.3 (双引擎版)',
                'pypiBtn': 'PyPI (Python)',
                'npmBtn': 'npm (Node.js)',
                'githubBtn': 'GitHub 仓库',
                'nav': {
                    'overview': '概览',
                    'home': '首页与架构',
                    'installation': '安装指南',
                    'quickstart': '快速入门与示例',
                    'nodejs': 'Node.js 与内存管理',
                    'apiReference': 'API 参考手册',
                    'versions': '版本历史档案',
                    'phantomProcess': 'Android 14 幽灵杀手',
                    'koreanBlog': '深度工程博客'
                },
                'footerText': '© 2026 Termux-Playwright 项目。遵循 MIT 开源许可证。'
            },
            'home': {
                'title': '适用于 Android Termux 的生产级 Playwright 自动化工具',
                'subtitle': '双引擎（Python 与 Node.js）直接在 ARM64 移动硬件上运行 Chromium 浏览器自动化，无需 root、PRoot 或 X11。',
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
                'quickInstallTitle': '单行命令极速安装（选择语言）',
                'quickInstallDesc': '选择您的运行环境并在 Termux 终端中运行以下单行命令：'
            },
            'nodejs': {
                'title': '双引擎架构：Node.js 与内存管理深度解析',
                'subtitle': 'CPython 与 V8 垃圾回收差异、libuv 流缓冲区及安卓 LMK 内存保活策略。',
                'divergenceTitle': '1. CPython 与 V8 内存机制在安卓上的差异',
                'divergenceDesc': 'Python 依靠引用计数在作用域结束时立即释放内存；而 Node.js V8 采用惰性分代垃圾回收，容易导致内存膨胀，触发安卓 LMK 查杀。',
                'actionsTitle': '2. 加固运行防护措施（审计措施已落地）',
                'action1Title': '同步信号与退出清理器',
                'action1Desc': 'Node.js process.on("exit") 触发时事件循环已停止。ProcessReaper 采用纯同步 C 级调用，确保无僵尸进程残留。',
                'action2Title': '全局异常守护（uncaughtException 与 unhandledRejection）',
                'action2Desc': '发生未捕获 Promise 错误时，自动触发 ProcessReaper.killAllTracked() 同步清理。',
                'action3Title': 'V8 堆上限约束与 forceGarbageCollection()',
                'action3Desc': '低内存模式将 V8 堆限制在 128MB，配合 forceGarbageCollection() 保持长周期爬虫内存纯净。',
                'recipesTitle': '3. Node.js / TypeScript 生产代码示例',
                'pm2Title': '4. 使用 PM2 打造 24 小时无人值守移动守护进程'
            }
        },
        'ja': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.61.3 (デュアルエンジン)',
                'pypiBtn': 'PyPI (Python)',
                'npmBtn': 'npm (Node.js)',
                'githubBtn': 'GitHub リポジトリ',
                'nav': {
                    'overview': '概要',
                    'home': 'ホーム / アーキテクチャ',
                    'installation': 'インストールガイド',
                    'quickstart': 'クイックスタート＆レシピ',
                    'nodejs': 'Node.js とメモリ管理',
                    'apiReference': 'API リファレンス',
                    'versions': 'バージョン履歴',
                    'phantomProcess': 'Android 14+ ファントムキラー',
                    'koreanBlog': '技術詳細ブログ'
                },
                'footerText': '© 2026 Termux-Playwright Project. MIT License の下で公開。'
            },
            'home': {
                'title': 'Android Termux 向け本番対応 Playwright 自動化',
                'subtitle': 'デュアルエンジン（Python & Node.js）対応。root や PRoot、X11 なしで ARM64 上で Chromium を直接操作。',
                'whyTitle': '問題定義：公式 Playwright が Android でクラッシュする理由',
                'whyText': '公式 Playwright はデスクトップ glibc 専用です。Android Termux で実行すると、Bionic libc の相違、/dev/shm 欠如、メモリ不足（OOM）により強制終了します。',
                'solTitle': 'アーキテクチャによる根本的解決',
                'solText': 'Termux-Playwright はネイティブ Bionic バイナリ連携、セッションプロセス隔離（ProcessReaper）、ディスク台帳復旧（.tp_ledger）、ステルス回避、eMMC 寿命保護を提供します。',
                'capTitle': '主な機能と堅牢化メカニズム',
                'cap1': 'Zero-Root ネイティブ実行：PRoot オーバーヘッドなしで Termux ネイティブの Chromium/Node.js を直接駆動。',
                'cap2': '永続ディスクセッション台帳：カーネル強制終了（SIGKILL / LMK）時も孤立プロセスを 100% 追跡回収。',
                'cap3': 'プロトタイプセーフ・ステルス：navigator.webdriver を削除し Cloudflare や DataDome を回避。',
                'cap4': 'ハードウェア寿命保護：RAM キャッシュ（/dev/shm）を注入し、スマホの eMMC 摩耗を防止。',
                'cap5': '仮想環境（venv）の完全サポート：--system-site-packages の自動診断とガイダンス。',
                'quickInstallTitle': '1 行クイックインストール（言語選択）',
                'quickInstallDesc': 'お好みの言語を選択し、Termux ターミナルで実行してください：'
            },
            'nodejs': {
                'title': 'デュアルエンジン設計：Node.js とメモリ管理の深層',
                'subtitle': 'CPython と V8 GC の違い、libuv バッファ、Android LMK 対策。',
                'divergenceTitle': '1. CPython vs V8 メモリおよび GC の相違点',
                'divergenceDesc': 'Python は参照カウントにより即座にメモリを解放しますが、Node.js V8 は遅延 GC のためメモリが膨張しやすく、スマホの LMK に終了されるリスクがあります。',
                'actionsTitle': '2. 堅牢化対策（適用済みのアクション項目）',
                'action1Title': '完全同期型シグナル＆終了リーパー',
                'action1Desc': 'Node.js の process.on("exit") は非同期コードを実行できません。純粋な同期 C レベル kill によりゾンビプロセスを皆殺しにします。',
                'action2Title': '未処理例外ガード（uncaughtException & unhandledRejection）',
                'action2Desc': '予期せぬ例外時にも自動で ProcessReaper.killAllTracked() を同期実行します。',
                'action3Title': 'V8 ヒープ制限と forceGarbageCollection()',
                'action3Desc': '低メモリモードでヒープを 128MB に制限し、手動 GC 呼び出しで 24 時間安定稼働を実現。',
                'recipesTitle': '3. Node.js / TypeScript レシピ',
                'pm2Title': '4. PM2 による 24 時間無人デーモン運用'
            }
        },
        'ko': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.80.1 (Dual Engine)',
                'pypiBtn': 'PyPI (Python)',
                'npmBtn': 'npm (Node.js)',
                'githubBtn': 'GitHub 저장소',
                'nav': {
                    'overview': '개요',
                    'home': '홈 / 아키텍처',
                    'installation': '설치 가이드',
                    'quickstart': '퀵스타트 & 레시피',
                    'nodejs': 'Node.js 및 메모리 아키텍처',
                    'apiReference': 'API 레퍼런스',
                    'versions': '버전별 변경 아카이브',
                    'phantomProcess': '안드로이드 14 팬텀 킬러',
                    'koreanBlog': '엔지니어링 개발기'
                },
                'footerText': '© 2026 Termux-Playwright Project. MIT 라이선스 하에 배포됩니다.'
            },
            'home': {
                'title': '안드로이드 Termux 프로덕션급 Playwright 브라우저 자동화',
                'subtitle': '듀얼 엔진(Python & Node.js) 완벽 지원. 루팅, PRoot, X11 가상화 없이 ARM64 스마트폰에서 크로미움을 네이티브로 직접 구동합니다.',
                'whyTitle': '문제 정의: 공식 Playwright가 안드로이드에서 폭발하는 이유',
                'whyText': '공식 Playwright는 데스크톱 Linux glibc만을 지원하도록 하드코딩되어 있습니다. 안드로이드 Termux 환경에서는 Bionic libc 시스템 콜 불일치, 공유 메모리(/dev/shm) 부재, C-확장 모듈 빌드 폭탄 및 좀비 프로세스 누수로 인해 즉시 크래시됩니다.',
                'solTitle': '시스템 레벨 아키텍처 솔루션',
                'solText': 'Termux-Playwright는 네이티브 Bionic 바이너리 오케스트레이션, 세션 격리 좀비 사살기(ProcessReaper), 영속 디스크 세션 장부(.tp_ledger), 프로토타입 체인 안전 스텔스, eMMC 플래시 마모 방지 기술을 탑재하여 문제를 완벽 해결합니다.',
                'capTitle': '핵심 기능 및 빌트인 하드닝 아키텍처',
                'cap1': 'Zero-Root 네이티브 실행: PRoot 가상화 오버헤드 없이 Termux 네이티브 Chromium과 Node.js를 0초 만에 직접 구동.',
                'cap2': '영속 디스크 세션 장부: 안드로이드 커널의 강제 사살(SIGKILL / LMK) 후에도 다음 기동 시 고아 프로세스를 100% 추적 사살.',
                'cap3': '프로토타입 체인 안전 스텔스: navigator.webdriver를 원천 삭제하여 Cloudflare Turnstile 및 DataDome 무력화.',
                'cap4': '하드웨어 플래시 수명 보호: RAM 기반 캐시(/dev/shm) 강제 주입으로 스마트폰 eMMC 플래시 메모리 마모 원천 방지.',
                'cap5': '가상환경(venv) 완벽 호환: --system-site-packages 자가 진단 및 원클릭 복구 가이드 제공.',
                'quickInstallTitle': '1줄 초간단 설치 (언어 선택)',
                'quickInstallDesc': '원하는 프로그래밍 언어(Python / Node.js)를 선택하고 Termux 터미널에서 다음 명령어를 실행하세요:'
            },
            'nodejs': {
                'title': '듀얼 엔진 아키텍처: Node.js & 메모리 수명주기 관리',
                'subtitle': 'CPython vs V8 가비지 컬렉션 차이, libuv 스트림 버퍼, 안드로이드 LMK 완벽 방어 전략.',
                'divergenceTitle': '1. CPython vs V8 메모리 및 GC 차이 분석',
                'divergenceDesc': '파이썬은 참조 카운팅(Ref-Counting)으로 스코프 종료 즉시 메모리를 반환하지만, Node.js V8은 메모리가 찰 때까지 GC를 미루는 Lazy GC 특성이 있어 모바일 LMK에 사살될 위험이 큽니다. termux-playwright는 V8 힙 상한선(128MB)과 forceGarbageCollection()으로 이를 완벽히 통제합니다.',
                'actionsTitle': '2. 철옹성 런타임 방어 조치 (감사 보고서 조치 완료)',
                'action1Title': '100% 동기식 시그널 & Exit 사살 가드',
                'action1Desc': 'Node.js의 process.on("exit") 훅은 이벤트 루프가 정지되므로 비동기 코드가 무시됩니다. ProcessReaper는 순수 동기식 C-레벨 process.kill과 fs.unlinkSync만 사용하여 단 1마리의 좀비 프로세스도 남기지 않습니다.',
                'action2Title': '전역 크래시 가드 (uncaughtException & unhandledRejection)',
                'action2Desc': '처리되지 않은 Promise 에러나 예외 발생 시에도 프로세스 종료 직전 ProcessReaper.killAllTracked()를 자동 실행합니다.',
                'action3Title': 'V8 힙 캡핑 & forceGarbageCollection() 헬퍼',
                'action3Desc': '저메모리 모드 시 V8 힙을 128MB로 제한하며, 24시간 루프 크롤링 중 메모리를 즉각 정화하는 forceGarbageCollection() 함수를 제공합니다.',
                'recipesTitle': '3. Node.js / TypeScript 실전 프로덕션 레시피',
                'pm2Title': '4. PM2 프로세스 매니저를 통한 24시간 무중단 백그라운드 구동'
            }
        },
        'es': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.61.3 (Motor Dual)',
                'pypiBtn': 'PyPI (Python)',
                'npmBtn': 'npm (Node.js)',
                'githubBtn': 'Repositorio GitHub',
                'nav': {
                    'overview': 'Resumen',
                    'home': 'Inicio / Arquitectura',
                    'installation': 'Guía de Instalación',
                    'quickstart': 'Inicio Rápido y Recetas',
                    'nodejs': 'Node.js y Memoria',
                    'apiReference': 'Referencia de API',
                    'versions': 'Archivo de Versiones',
                    'phantomProcess': 'Android 14+ Phantom Killer',
                    'koreanBlog': 'Blog de Ingeniería'
                },
                'footerText': '© 2026 Proyecto Termux-Playwright. Publicado bajo Licencia MIT.'
            },
            'home': {
                'title': 'Automatización Playwright de Nivel de Producción en Android Termux',
                'subtitle': 'Automatización Chromium con motor dual (Python y Node.js) en ARM64 sin root ni PRoot.',
                'whyTitle': 'El Problema: Por qué Playwright Oficial Falla en Android',
                'whyText': 'Playwright oficial requiere glibc de escritorio. En Termux falla por llamadas Bionic libc incompatibles, falta de /dev/shm y fugas de procesos zombis.',
                'solTitle': 'La Solución Arquitectónica',
                'solText': 'Termux-Playwright proporciona orquestación binaria Bionic nativa, aislamiento de procesos, libro mayor persistente (.tp_ledger) y evasión stealth.',
                'capTitle': 'Capacidades Clave y Blindaje',
                'cap1': 'Ejecución Nativa Sin Root: Ejecuta Chromium y Node.js nativos sin sobrecarga de PRoot.',
                'cap2': 'Libro Mayor Persistente en Disco: Garantiza la eliminación de procesos huérfanos tras caídas forzadas (SIGKILL / LMK).',
                'cap3': 'Modo Sigiloso: Elimina navigator.webdriver para eludir Cloudflare Turnstile y DataDome.',
                'cap4': 'Protección Flash: Caché en RAM (/dev/shm) para evitar desgaste del almacenamiento eMMC.',
                'cap5': 'Integración Virtualenv: Diagnóstico y reparación automática para entornos venv.',
                'quickInstallTitle': 'Instalación Rápida en 1 Línea (Elegir Lenguaje)',
                'quickInstallDesc': 'Elija su lenguaje y ejecute el comando en Termux:'
            },
            'nodejs': {
                'title': 'Arquitectura de Motor Dual: Node.js y Memoria',
                'subtitle': 'Diferencias entre CPython y V8 GC, buffers de libuv y supervivencia ante LMK de Android.',
                'divergenceTitle': '1. Divergencia de Memoria y GC entre CPython y V8',
                'divergenceDesc': 'Python libera memoria de inmediato mediante conteo de referencias; Node.js V8 usa recolección perezosa que puede provocar cierres por LMK en móviles.',
                'actionsTitle': '2. Protecciones en Tiempo de Ejecución Aplicadas',
                'action1Title': 'Segador Síncrono de Señales y Salida',
                'action1Desc': 'ProcessReaper usa llamadas síncronas a nivel C para garantizar cero procesos zombis al salir.',
                'action2Title': 'Manejadores de Fallos Globales (uncaughtException y unhandledRejection)',
                'action2Desc': 'Limpia automáticamente los procesos huérfanos antes de que el proceso termine.',
                'action3Title': 'Límite de Heap V8 y forceGarbageCollection()',
                'action3Desc': 'Limita el heap a 128MB y ofrece una función para purgar memoria durante ciclos largos.',
                'recipesTitle': '3. Recetas de Producción para Node.js / TypeScript',
                'pm2Title': '4. Servicio Móvil Desatendido 24/7 con PM2'
            }
        },
        'hi': {
            'common': {
                'brand': 'Termux-Playwright',
                'releaseTag': 'v1.80.1 (Dual Engine)',
                'pypiBtn': 'PyPI (Python)',
                'npmBtn': 'npm (Node.js)',
                'githubBtn': 'GitHub रिपॉजिटरी',
                'nav': {
                    'overview': 'अवलोकन',
                    'home': 'होम / आर्किटेक्चर',
                    'installation': 'इंस्टॉलेशन गाइड',
                    'quickstart': 'त्वरित शुरुआत',
                    'nodejs': 'Node.js और मेमोरी',
                    'apiReference': 'API संदर्भ',
                    'versions': 'संस्करण पुरालेख',
                    'phantomProcess': 'Android 14+ फैंटम किलर',
                    'koreanBlog': 'इंजीनियरिंग ब्लॉग'
                },
                'footerText': '© 2026 Termux-Playwright Project. MIT लाइसेंस के तहत जारी।'
            },
            'home': {
                'title': 'Android Termux पर प्रोडक्शन-ग्रेड Playwright ऑटोमेशन',
                'subtitle': 'बिना root या PRoot के ARM64 पर Python और Node.js डुअल इंजन ब्राउज़र ऑटोमेशन।',
                'whyTitle': 'समस्या: Playwright Android पर क्रैश क्यों होता है',
                'whyText': 'आधिकारिक Playwright केवल डेस्कटॉप glibc का समर्थन करता है। Termux पर Bionic libc अंतर और /dev/shm की कमी के कारण यह क्रैश हो जाता है।',
                'solTitle': 'आर्किटेक्चरल समाधान',
                'solText': 'Termux-Playwright नेटिव Bionic बाइनरी ऑर्케स्ट्रेशन, प्रोसेस लेजर (.tp_ledger) और स्टेल्थ एंटी-बॉट सुरक्षा प्रदान करता है।',
                'capTitle': 'मुख्य क्षमताएं और सुरक्षा',
                'cap1': 'Zero-Root नेटिव निष्पादन: PRoot ओवरहेड के बिना Chromium और Node.js का संचालन।',
                'cap2': 'स्थिर डिस्क लेजर: SIGKILL या LMK क्रैश के बाद 100% ज़ॉम्비 प्रोसेस की सफाई।',
                'cap3': 'प्रोटोटाइप स्टेल्थ: Cloudflare और DataDome को बायपास करने के लिए navigator.webdriver को हटाना।',
                'cap4': 'फ्लैश सुरक्षा: eMMC लाइफ की सुरक्षा के लिए RAM कैशिंग (/dev/shm) का उपयोग।',
                'cap5': 'Virtualenv एकीकरण: venv वातावरण के लिए स्वचालित निदान और मार्गदर्शन।',
                'quickInstallTitle': '1-लाइन त्वरित इंस्टॉलेशन (भाषा चुनें)',
                'quickInstallDesc': 'अपनी पसंदीदा भाषा चुनें और Termux टर्मिनल में चलाएं:'
            },
            'nodejs': {
                'title': 'डुअल-इंजन आर्किटेक्चर: Node.js और मेमोरी प्रबंधन',
                'subtitle': 'CPython बनाम V8 GC अंतर और Android LMK सुरक्षा रणनीतियाँ।',
                'divergenceTitle': '1. CPython बनाम V8 मेमोरी और GC का अंतर',
                'divergenceDesc': 'Python तुरंत मेमोरी खाली करता है जबकि V8 लेजी GC का उपयोग करता है। termux-playwright मेमोरी कैप और forceGarbageCollection() द्वारा इसे नियंत्रित करता है।',
                'actionsTitle': '2. मजबूत रनटाइम सुरक्षात्मक उपाय',
                'action1Title': 'सिंक्रोनस सिग्नल और एग्जिट रीपर',
                'action1Desc': 'Node.js एग्जिट पर शुद्ध सिंक्रोनस C-लेवल कॉल्स का उपयोग करके ज़ॉम्비 प्रोसेस को रोकता है।',
                'action2Title': 'ग्लोबल क्रैश हैंडलर (uncaughtException & unhandledRejection)',
                'action2Desc': 'अप्रत्याशित क्रैश के समय भी स्वचालित रूप से प्रोसेस की सफाई सुनिश्चित करता है।',
                'action3Title': 'V8 हीप कैपिंग और forceGarbageCollection()',
                'action3Desc': 'मेमोरी को 128MB पर सीमित करता है और 24/7 क्रॉलर में मेमोरी फ्लश की अनुमति देता है।',
                'recipesTitle': '3. Node.js / TypeScript प्रोडक्शन रेसिपी',
                'pm2Title': '4. PM2 के साथ 24/7 बैकग्राउंड डेमन'
            }
        }
    };

    global.I18N_DICT = DICT;
})(typeof window !== 'undefined' ? window : global);
