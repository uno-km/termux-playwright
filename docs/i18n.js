/**
 * Termux-Playwright Documentation - Multilingual (i18n) Core Engine
 * Client-Side Internationalization with Multi-Tier Storage & Auto-Detector
 * @license MIT
 */

(function(global) {
    'use strict';

    const SUPPORTED_LANGUAGES = {
        'en': { code: 'en', name: 'English', nativeName: 'English', flag: 'US' },
        'zh': { code: 'zh', name: 'Chinese', nativeName: '简体中文', flag: 'CN' },
        'ja': { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: 'JP' },
        'ko': { code: 'ko', name: 'Korean', nativeName: '한국어', flag: 'KR' },
        'es': { code: 'es', name: 'Spanish', nativeName: 'Español', flag: 'ES' },
        'hi': { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: 'IN' }
    };

    const DEFAULT_LANG = 'en';
    const STORAGE_KEY = 'termux_playwright_doc_lang';

    class I18nManager {
        constructor() {
            this.currentLang = DEFAULT_LANG;
            this.translations = {};
            this.initialized = false;
        }

        init() {
            this.currentLang = this._getSavedLang() || this._detectBrowserLang();
            if (!SUPPORTED_LANGUAGES[this.currentLang]) {
                this.currentLang = DEFAULT_LANG;
            }

            this._setupLanguageSelectors();
            this._setupCodeCopyButtons();
            this.applyLanguage(this.currentLang);
            this.initialized = true;
        }

        registerTranslations(dict) {
            this.translations = dict;
            if (this.initialized) {
                this.applyLanguage(this.currentLang);
            }
        }

        _getSavedLang() {
            try {
                return localStorage.getItem(STORAGE_KEY);
            } catch (e) {
                return null;
            }
        }

        _saveLang(lang) {
            try {
                localStorage.setItem(STORAGE_KEY, lang);
            } catch (e) {}
        }

        _detectBrowserLang() {
            try {
                const nav = navigator.languages || [navigator.language || ''];
                for (const l of nav) {
                    const code = l.toLowerCase().substring(0, 2);
                    if (SUPPORTED_LANGUAGES[code]) return code;
                }
            } catch (e) {}
            return DEFAULT_LANG;
        }

        setLanguage(lang) {
            if (!SUPPORTED_LANGUAGES[lang]) return;
            this.currentLang = lang;
            this._saveLang(lang);
            this.applyLanguage(lang);

            // Update selector dropdowns
            document.querySelectorAll('.lang-select').forEach(sel => {
                sel.value = lang;
            });

            document.documentElement.lang = lang;
        }

        applyLanguage(lang) {
            const dict = this.translations[lang] || this.translations[DEFAULT_LANG] || {};

            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                const val = this._lookup(dict, key);
                if (val !== undefined) {
                    el.textContent = val;
                }
            });

            document.querySelectorAll('[data-i18n-html]').forEach(el => {
                const key = el.getAttribute('data-i18n-html');
                const val = this._lookup(dict, key);
                if (val !== undefined) {
                    el.innerHTML = val;
                }
            });

            document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                const key = el.getAttribute('data-i18n-placeholder');
                const val = this._lookup(dict, key);
                if (val !== undefined) {
                    el.setAttribute('placeholder', val);
                }
            });
        }

        _lookup(obj, path) {
            if (!obj || !path) return undefined;
            const parts = path.split('.');
            let curr = obj;
            for (const p of parts) {
                if (curr && typeof curr === 'object' && p in curr) {
                    curr = curr[p];
                } else {
                    return undefined;
                }
            }
            return curr;
        }

        _setupLanguageSelectors() {
            document.querySelectorAll('.lang-selector-wrapper').forEach(wrapper => {
                const select = document.createElement('select');
                select.className = 'lang-select';
                select.setAttribute('aria-label', 'Select Language');

                for (const [code, info] of Object.entries(SUPPORTED_LANGUAGES)) {
                    const opt = document.createElement('option');
                    opt.value = code;
                    opt.textContent = `${info.name} (${info.nativeName})`;
                    if (code === this.currentLang) opt.selected = true;
                    select.appendChild(opt);
                }

                select.addEventListener('change', (e) => {
                    this.setLanguage(e.target.value);
                });

                wrapper.innerHTML = '';
                wrapper.appendChild(select);
            });
        }

        _setupCodeCopyButtons() {
            document.querySelectorAll('pre').forEach(pre => {
                if (pre.querySelector('.copy-btn')) return;
                const btn = document.createElement('button');
                btn.className = 'copy-btn';
                btn.textContent = 'Copy';
                btn.addEventListener('click', () => {
                    const code = pre.querySelector('code') ? pre.querySelector('code').innerText : pre.innerText;
                    navigator.clipboard.writeText(code).then(() => {
                        btn.textContent = 'Copied!';
                        setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
                    });
                });
                pre.style.position = 'relative';
                pre.appendChild(btn);
            });
        }
    }

    global.TermuxPlaywrightI18n = new I18nManager();

    document.addEventListener('DOMContentLoaded', () => {
        global.TermuxPlaywrightI18n.init();
    });

})(typeof window !== 'undefined' ? window : this);
