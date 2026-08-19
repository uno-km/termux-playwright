"""
Update docs/i18n-translations.js and docs/build_pages.py to fully incorporate
the Node.js & Memory Architecture deep-dive across all 6 languages.
"""

import os

# 1. Update docs/i18n-translations.js
i18n_content = """/**
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
                    'nodejs': 'Node.js & Memory Guide',
                    'advanced': 'Advanced & Deep Dives',
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
                'quickInstallTitle': '1-Line Quick Installation',
                'quickInstallDesc': 'Choose your preferred programming language and run the 1-line installation command:'
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
                'releaseTag': 'v1.61.2 (强韧幽灵)',
                'pypiBtn': 'PyPI 软件包',
                'githubBtn': 'GitHub 仓库',
                'nav': {
                    'overview': '概览',
                    'home': '首页与架构',
                    'installation': '安装指南',
                    'quickstart': '快速入门与示例',
                    'apiReference': 'API 参考手册',
                    'nodejs': 'Node.js 与内存管理',
                    'advanced': '高级进阶',
                    'versions': '版本历史档案',
                    'phantomProcess': 'Android 14 幽灵杀手',
                    'koreanBlog': '深度工程博客'
                },
                'footerText': '© 2026 Termux-Playwright 项目。基于 MIT 协议开源。'
            },
            'home': {
                'title': '安卓 Termux 生产级 Playwright 自动化',
                'subtitle': '双引擎（Python 与 Node.js）直接在 ARM64 移动硬件上运行 Chromium 浏览器自动化，无需 root、PRoot 或 X11。',
                'whyTitle': '核心痛点：官方 Playwright 为何在安卓崩溃',
                'whyText': '官方 Playwright 仅支持桌面 glibc Linux。在安卓 Termux 运行时，会因 Bionic libc 系统调用差异、/dev/shm 缺失及内核进程查杀而立即崩溃。',
                'solTitle': '系统级架构解决方案',
                'solText': 'Termux-Playwright 提供了原生 Bionic 二进制编排、会话进程隔离、磁盘持久账本恢复（.tp_ledger）、原型链安全防爬虫反检测和 eMMC 闪存保护。',
                'capTitle': '核心功能与加固特性',
                'cap1': '零 Root 原生运行：直接编排 Termux 原生编译的 Chromium 和 Node.js，零 PRoot 开销。',
                'cap2': '持久化磁盘会话账本：在内核强制杀进程（SIGKILL/LMK）后保证 100% 孤儿进程回收。',
                'cap3': '原型链安全隐身：从原型链删除 navigator.webdriver 绕过 Cloudflare 与 DataDome。',
                'cap4': '硬件闪存磨损防护：注入 RAM 缓存（/dev/shm），防止移动 eMMC 闪存磨损。',
                'cap5': '虚拟环境深度适配：针对 venv 自动检测并提示 --system-site-packages。',
                'quickInstallTitle': '一键快速安装',
                'quickInstallDesc': '选择您的编程语言并在 Termux 终端中运行以下单行命令：'
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
                'releaseTag': 'v1.61.2 (堅牢なファントム)',
                'pypiBtn': 'PyPI パッケージ',
                'githubBtn': 'GitHub リポジトリ',
                'nav': {
                    'overview': '概要',
                    'home': 'ホーム / アーキテクチャ',
                    'installation': 'インストールガイド',
                    'quickstart': 'クイックスタート＆レシピ',
                    'apiReference': 'API リファレンス',
                    'nodejs': 'Node.js とメモリ管理',
                    'advanced': '高度な機能',
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
                'quickInstallTitle': '1 行クイックインストール',
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
                'releaseTag': 'v1.61.2 (Resilient Phantom)',
                'pypiBtn': 'PyPI 공식 패키지',
                'githubBtn': 'GitHub 저장소',
                'nav': {
                    'overview': '개요',
                    'home': '홈 / 아키텍처',
                    'installation': '설치 가이드',
                    'quickstart': '퀵스타트 & 레시피',
                    'apiReference': 'API 레퍼런스',
                    'nodejs': 'Node.js 및 메모리 아키텍처',
                    'advanced': '심층 엔지니어링',
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
                'quickInstallTitle': '1줄 초간단 설치',
                'quickInstallDesc': '원하는 프로그래밍 언어를 선택하고 Termux 터미널에서 다음 명령어를 실행하세요:'
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
                'releaseTag': 'v1.61.2 (Fantasma Resiliente)',
                'pypiBtn': 'Paquete PyPI',
                'githubBtn': 'Repositorio GitHub',
                'nav': {
                    'overview': 'Resumen',
                    'home': 'Inicio / Arquitectura',
                    'installation': 'Guía de Instalación',
                    'quickstart': 'Inicio Rápido y Recetas',
                    'apiReference': 'Referencia de API',
                    'nodejs': 'Node.js y Memoria',
                    'advanced': 'Avanzado',
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
                'quickInstallTitle': 'Instalación Rápida en 1 Línea',
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
                'releaseTag': 'v1.61.2 (Resilient Phantom)',
                'pypiBtn': 'PyPI पैकेज',
                'githubBtn': 'GitHub रिपॉजिटरी',
                'nav': {
                    'overview': 'अवलोकन',
                    'home': 'होम / आर्किटेक्चर',
                    'installation': 'इंस्टॉलेशन गाइड',
                    'quickstart': 'त्वरित शुरुआत',
                    'apiReference': 'API संदर्भ',
                    'nodejs': 'Node.js और मेमोरी',
                    'advanced': 'उन्नत सुविधाएँ',
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
                'solText': 'Termux-Playwright नेटिव Bionic बाइनरी ऑर्केस्ट्रेशन, प्रोसेस लेजर (.tp_ledger) और स्टेल्थ एंटी-बॉट सुरक्षा प्रदान करता है।',
                'capTitle': 'मुख्य क्षमताएं और सुरक्षा',
                'cap1': 'Zero-Root नेटिव निष्पादन: PRoot ओवरहेड के बिना Chromium और Node.js का संचालन।',
                'cap2': 'स्थिर डिस्क लेजर: SIGKILL या LMK क्रैश के बाद 100% ज़ॉम्बी प्रोसेस की सफाई।',
                'cap3': 'प्रोटोटाइप स्टेल्थ: Cloudflare और DataDome को बायपास करने के लिए navigator.webdriver को हटाना।',
                'cap4': 'फ्लैश सुरक्षा: eMMC लाइफ की सुरक्षा के लिए RAM कैशिंग (/dev/shm) का उपयोग।',
                'cap5': 'Virtualenv एकीकरण: venv वातावरण के लिए स्वचालित निदान और मार्गदर्शन।',
                'quickInstallTitle': '1-लाइन त्वरित इंस्टॉलेशन',
                'quickInstallDesc': 'अपनी पसंदीदा भाषा चुनें और Termux टर्मिनल में चलाएं:'
            },
            'nodejs': {
                'title': 'डुअल-इंजन आर्किटेक्चर: Node.js और मेमोरी प्रबंधन',
                'subtitle': 'CPython बनाम V8 GC अंतर और Android LMK सुरक्षा रणनीतियाँ।',
                'divergenceTitle': '1. CPython बनाम V8 मेमोरी और GC का अंतर',
                'divergenceDesc': 'Python तुरंत मेमोरी खाली करता है जबकि V8 लेजी GC का उपयोग करता है। termux-playwright मेमोरी कैप और forceGarbageCollection() द्वारा इसे नियंत्रित करता है।',
                'actionsTitle': '2. मजबूत रनटाइम सुरक्षात्मक उपाय',
                'action1Title': 'सिंक्रोनस सिग्नल और एग्जिट रीपर',
                'action1Desc': 'Node.js एग्जिट पर शुद्ध सिंक्रोनस C-लेवल कॉल्स का उपयोग करके ज़ॉम्बी प्रोसेस को रोकता है।',
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
"""

with open('docs/i18n-translations.js', 'w', encoding='utf-8') as f:
    f.write(i18n_content)
print('Updated docs/i18n-translations.js with Node.js keys.')

# 2. Update docs/build_pages.py to generate nodejs.html and include in sidebar
build_pages_py = '''"""
Build all HTML pages for Termux-Playwright GitHub Pages documentation.
Dual-Engine (Python & Node.js / TypeScript) Architecture
"""
import os

def get_header(active_page):
    return f"""    <header>
        <a href="index.html" class="header-brand">
            <img src="favicon.svg" alt="Logo">
            <h1 data-i18n="common.brand">Termux-Playwright</h1>
        </a>
        <div class="header-controls">
            <span class="release-tag" data-i18n="common.releaseTag">v1.61.2 (Resilient Phantom)</span>
            <div class="lang-selector-wrapper"></div>
            <a href="https://pypi.org/project/termux-playwright/" target="_blank" class="header-btn" data-i18n="common.pypiBtn">PyPI Package</a>
            <a href="https://www.npmjs.com/package/termux-playwright" target="_blank" class="header-btn" style="background:#cb3837;color:#fff;">npm Package</a>
            <a href="https://github.com/uno-km/termux-playwright-demo" target="_blank" class="header-btn primary" data-i18n="common.githubBtn">GitHub Repository</a>
        </div>
    </header>"""

def get_sidebar(active_page):
    pages = [
        ('index.html', 'common.nav.home', 'Home / Architecture'),
        ('installation.html', 'common.nav.installation', 'Installation Guide'),
        ('quickstart.html', 'common.nav.quickstart', 'Quickstart & Recipes'),
        ('nodejs.html', 'common.nav.nodejs', 'Node.js & Memory Guide'),
        ('api-reference.html', 'common.nav.apiReference', 'API Reference'),
        ('versions.html', 'common.nav.versions', 'Version Archive & Notes'),
        ('phantom-process.html', 'common.nav.phantomProcess', 'Android 14+ Phantom Killer'),
        ('blog_post.md', 'common.nav.koreanBlog', 'Engineering Deep-Dive (KO)')
    ]
    
    sidebar_html = """        <nav class="sidebar">
            <h3 data-i18n="common.nav.overview">Overview</h3>
            <ul>"""
    
    for href, i18n_key, title in pages:
        active_class = ' class="active"' if href == active_page else ''
        sidebar_html += f"""
                <li><a href="{href}"{active_class} data-i18n="{i18n_key}">{title}</a></li>"""
    
    sidebar_html += """
            </ul>
            <h3 data-i18n="common.nav.advanced">AI Specifications</h3>
            <ul>
                <li><a href="llms.txt" target="_blank">llms.txt (AI Matrix)</a></li>
                <li><a href="llms-full.txt" target="_blank">llms-full.txt (Full Spec)</a></li>
            </ul>
        </nav>"""
    return sidebar_html

def get_footer():
    return """    <footer>
        <span data-i18n="common.footerText">&copy; 2026 Termux-Playwright Project. Released under the MIT License.</span>
    </footer>"""

# 1. index.html
index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Termux-Playwright: Production Browser Automation on Android</title>
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="stylesheet" href="style.css">
    <script src="i18n.js"></script>
    <script src="i18n-translations.js"></script>
</head>
<body>
{get_header('index.html')}

    <div class="container">
{get_sidebar('index.html')}

        <main class="content">
            <h2 data-i18n="home.title">Production-Grade Playwright Automation on Android Termux</h2>
            <p data-i18n="home.subtitle">Dual-engine (Python & Node.js) Chromium browser automation on ARM64 mobile hardware without root, PRoot, or X11 virtualization.</p>

            <div class="badges-bar">
                <a href="https://pypi.org/project/termux-playwright/" target="_blank"><img src="https://img.shields.io/pypi/v/termux-playwright.svg?color=blue" alt="PyPI Version"></a>
                <a href="https://www.npmjs.com/package/termux-playwright" target="_blank"><img src="https://img.shields.io/npm/v/termux-playwright.svg?color=red" alt="npm Version"></a>
                <a href="https://pepy.tech/projects/termux-playwright" target="_blank"><img src="https://img.shields.io/pepy/dt/termux-playwright?color=orange" alt="Total Downloads"></a>
                <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python Version">
                <img src="https://img.shields.io/badge/node-16+-brightgreen.svg" alt="Node Version">
                <img src="https://img.shields.io/badge/platform-Android%20Termux%20(aarch64)-green.svg" alt="Platform">
                <img src="https://img.shields.io/badge/tests-98%20passed%20%7C%20100%25-success" alt="Tests">
            </div>

            <div class="card">
                <h3 data-i18n="home.whyTitle">The Problem: Why Upstream Playwright Fails on Android</h3>
                <p data-i18n="home.whyText">Upstream Playwright is hardcoded to strictly support desktop Linux glibc, macOS, and Windows. When invoked on Android Termux, it fails due to incompatible pre-compiled binaries, Bionic libc syscall differences, dynamic shared memory (/dev/shm) crashes, and Android kernel process reaping.</p>
            </div>

            <div class="card">
                <h3 data-i18n="home.solTitle">The Architectural Solution</h3>
                <p data-i18n="home.solText">Termux-Playwright provides native Bionic binary orchestration, targeted session process isolation (ProcessReaper), persistent disk ledger recovery (.tp_ledger), prototype-safe anti-bot stealth, and flash memory wear protection.</p>
            </div>

            <h3 data-i18n="home.capTitle">Key Capabilities & Built-in Hardening</h3>
            <div class="grid">
                <div class="card">
                    <h4>⚡ Zero-Root Native Speed</h4>
                    <p data-i18n="home.cap1">Directly orchestrates Termux-compiled Chromium and Node.js without PRoot overhead.</p>
                </div>
                <div class="card">
                    <h4>🛡️ Persistent Disk Ledger</h4>
                    <p data-i18n="home.cap2">Guarantees 100% orphan process reaping across hard kernel crashes (SIGKILL / LMK).</p>
                </div>
                <div class="card">
                    <h4>🥷 Prototype-Safe Stealth</h4>
                    <p data-i18n="home.cap3">Deletes navigator.webdriver from prototype to bypass Cloudflare Turnstile & DataDome.</p>
                </div>
                <div class="card">
                    <h4>💾 Flash Wear Protection</h4>
                    <p data-i18n="home.cap4">Injects RAM-based caching to prevent eMMC mobile flash wear.</p>
                </div>
            </div>

            <div class="card highlight">
                <h3 data-i18n="home.quickInstallTitle">1-Line Quick Installation</h3>
                <p data-i18n="home.quickInstallDesc">Choose your preferred programming language and run the 1-line installation command:</p>
                <div class="code-block">
                    <h4>🐍 Python (PyPI):</h4>
                    <pre><code>pip install termux-playwright && termux-playwright-install</code></pre>
                    <h4>☕ Node.js / TypeScript (npm):</h4>
                    <pre><code>pkg install -y chromium nodejs-lts && npm install termux-playwright && npx termux-playwright doctor</code></pre>
                </div>
            </div>
        </main>
    </div>

{get_footer()}
</body>
</html>"""

# 2. nodejs.html
nodejs_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Node.js & Memory Architecture - Termux-Playwright</title>
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="stylesheet" href="style.css">
    <script src="i18n.js"></script>
    <script src="i18n-translations.js"></script>
</head>
<body>
{get_header('nodejs.html')}

    <div class="container">
{get_sidebar('nodejs.html')}

        <main class="content">
            <h2 data-i18n="nodejs.title">Dual-Engine Architecture: Node.js & Memory Management</h2>
            <p data-i18n="nodejs.subtitle">Deep-dive on CPython vs V8 Garbage Collection, libuv stream buffers, and Android LMK survival strategies.</p>

            <div class="card">
                <h3 data-i18n="nodejs.divergenceTitle">1. CPython vs V8 Memory & GC Divergence on Android</h3>
                <p data-i18n="nodejs.divergenceDesc">Python relies on deterministic Reference Counting to immediately free memory upon scope exit. In contrast, Node.js V8 uses Generational Scavenge & Mark-Sweep-Compact with Lazy GC, keeping heap allocated until pressure builds. On mobile devices with 1GB-4GB RAM, default V8 heap limits (1.4GB) trigger Android Low Memory Killer (LMK) execution.</p>
                
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Dimension</th>
                            <th>CPython Runtime (Python)</th>
                            <th>V8 Engine Runtime (Node.js)</th>
                            <th>Mobile Android Termux Impact</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>GC Trigger</strong></td>
                            <td>Deterministic Ref-Count (0-sec deallocation)</td>
                            <td>Generational Lazy GC (waits for heap threshold)</td>
                            <td>Node.js requires explicit memory caps</td>
                        </tr>
                        <tr>
                            <td><strong>Default Heap Cap</strong></td>
                            <td>OS-governed dynamic RAM</td>
                            <td>1.4 GB ~ 4 GB desktop default</td>
                            <td>Can trigger Android LMK OOM on <=4GB phones</td>
                        </tr>
                        <tr>
                            <td><strong>Exit Lifecycle</strong></td>
                            <td>Synchronous / async exit hooks allowed</td>
                            <td>Event loop is dead inside process.on('exit')</td>
                            <td>Reaper MUST use 100% sync C-syscalls</td>
                        </tr>
                        <tr>
                            <td><strong>Crash Propagation</strong></td>
                            <td>Traceback on unhandled exception</td>
                            <td>Unhandled Promise rejection can kill process</td>
                            <td>Requires unhandledRejection global guard</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="card highlight">
                <h3 data-i18n="nodejs.actionsTitle">2. Hardened Runtime Protections (Audit Actions Applied)</h3>
                
                <h4>🛡️ <span data-i18n="nodejs.action1Title">Synchronous Signal & Exit Reaper</span></h4>
                <p data-i18n="nodejs.action1Desc">In Node.js, process.on("exit") permanently shuts down the event loop—async calls are ignored. ProcessReaper uses pure synchronous C-level process.kill and fs.unlinkSync to guarantee zero zombie leaks.</p>

                <h4>🛡️ <span data-i18n="nodejs.action2Title">Uncaught Crash Handlers (uncaughtException & unhandledRejection)</span></h4>
                <p data-i18n="nodejs.action2Desc">Unhandled Promise rejections and uncaught exceptions automatically trigger synchronous ProcessReaper.killAllTracked() before process termination.</p>

                <h4>🛡️ <span data-i18n="nodejs.action3Title">V8 Heap Capping & forceGarbageCollection()</span></h4>
                <p data-i18n="nodejs.action3Desc">Low-memory mode caps V8 heap at 128MB. The forceGarbageCollection() helper flushes V8 young/old generation heaps during long-running crawler cycles.</p>
            </div>

            <div class="card">
                <h3 data-i18n="nodejs.recipesTitle">3. Node.js / TypeScript Production Recipes</h3>
                <div class="code-block">
                    <h4>JavaScript (ESM / CommonJS):</h4>
                    <pre><code>const { launch, setupStealthContext, blockHeavyResources, forceGarbageCollection } = require('termux-playwright');

async function main() {
    // 1. Launch with low memory mode & WakeLock
    const browser = await launch({
        headless: true,
        stealth: true,
        lowMemoryMode: true,
        wakeLock: true
    });

    try {
        const context = await setupStealthContext(browser, {
            locale: 'en-US',
            timezoneId: 'America/New_York'
        });

        const page = await context.newPage();
        
        // 2. Abort heavy media to save mobile data & CPU
        await blockHeavyResources(page, { images: true, media: true, fonts: true });

        await page.goto('https://news.ycombinator.com', { timeout: 45000, waitUntil: 'domcontentloaded' });
        console.log('Page Title:', await page.title());

        // 3. Periodic memory purge for long-running scrapers
        forceGarbageCollection();
    } finally {
        await browser.close();
    }
}

main().catch(console.error);</code></pre>
                </div>
            </div>

            <div class="card">
                <h3 data-i18n="nodejs.pm2Title">4. 24/7 Unattended Mobile Daemon with PM2</h3>
                <p>To run your Node.js crawler 24/7 in Termux without process teardown when Termux is backgrounded, use PM2:</p>
                <div class="code-block">
                    <pre><code># Install PM2 globally in Termux
npm install -g pm2

# Start crawler with V8 memory cap and auto-restart
pm2 start app.js --name "mobile-crawler" --node-args="--max-old-space-size=256 --expose-gc"

# View live logs & memory
pm2 logs mobile-crawler
pm2 monit</code></pre>
                </div>
            </div>
        </main>
    </div>

{get_footer()}
</body>
</html>"""

# Write files
with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(index_html)
print('Generated docs/index.html')

with open('docs/nodejs.html', 'w', encoding='utf-8') as f:
    f.write(nodejs_html)
print('Generated docs/nodejs.html')
'''

with open('docs/update_all_docs.py', 'w', encoding='utf-8') as f:
    f.write(build_pages_py)

print('Created docs/update_all_docs.py')
