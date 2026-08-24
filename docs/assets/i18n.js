/**
 * AMEVA Ecosystem - Multilingual (i18n) Core Engine (SSOT)
 * Version: 1.0.0
 * Zero-dependency, client-side internationalization manager with auto-detection,
 * multi-tab code switcher, and 1-click code copying.
 */

(function(global) {
  'use strict';

  const SUPPORTED_LANGUAGES = {
    'en': { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
    'ko': { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
    'ja': { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
    'zh': { code: 'zh', name: 'Chinese', nativeName: '简体中文', flag: '🇨🇳' },
    'es': { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
    'de': { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' }
  };

  const DEFAULT_LANG = 'en';
  const STORAGE_KEY = 'ameva_lib_doc_lang';

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
      this._setupTabs();
      this.applyLanguage(this.currentLang);
      this.initialized = true;
    }

    registerTranslations(dict) {
      this.translations = dict || {};
      if (this.initialized) {
        this.applyLanguage(this.currentLang);
      }
    }

    _getSavedLang() {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const langParam = urlParams.get('lang');
        if (langParam && SUPPORTED_LANGUAGES[langParam]) return langParam;
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
        if (val !== undefined && val !== null) {
          el.textContent = val;
        }
      });

      document.querySelectorAll('[data-i18n-html]').forEach(el => {
        const key = el.getAttribute('data-i18n-html');
        const val = this._lookup(dict, key);
        if (val !== undefined && val !== null) {
          el.innerHTML = val;
        }
      });

      document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const val = this._lookup(dict, key);
        if (val !== undefined && val !== null) {
          el.setAttribute('placeholder', val);
        }
      });

      document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const val = this._lookup(dict, key);
        if (val !== undefined && val !== null) {
          el.setAttribute('title', val);
        }
      });
    }

    _lookup(dict, keyPath) {
      if (!dict || !keyPath) return undefined;
      const keys = keyPath.split('.');
      let current = dict;
      for (const k of keys) {
        if (current === undefined || current === null) return undefined;
        current = current[k];
      }
      return current;
    }

    _setupLanguageSelectors() {
      const wrappers = document.querySelectorAll('.lang-selector-wrapper');
      wrappers.forEach(wrapper => {
        if (wrapper.querySelector('select')) return; // already has one

        const select = document.createElement('select');
        select.className = 'lang-select';
        select.setAttribute('aria-label', 'Select Language');

        Object.values(SUPPORTED_LANGUAGES).forEach(lang => {
          const opt = document.createElement('option');
          opt.value = lang.code;
          opt.textContent = `${lang.flag} ${lang.nativeName}`;
          if (lang.code === this.currentLang) {
            opt.selected = true;
          }
          select.appendChild(opt);
        });

        select.addEventListener('change', (e) => {
          this.setLanguage(e.target.value);
        });

        wrapper.appendChild(select);
      });
    }

    _setupCodeCopyButtons() {
      document.querySelectorAll('pre').forEach(pre => {
        if (pre.querySelector('.copy-code-btn')) return;

        const btn = document.createElement('button');
        btn.className = 'copy-code-btn';
        btn.textContent = 'Copy';
        btn.setAttribute('type', 'button');
        btn.setAttribute('aria-label', 'Copy code snippet');

        btn.addEventListener('click', () => {
          const code = pre.querySelector('code') || pre;
          const text = code.innerText.replace(/^Copy\n/, '').trim();
          navigator.clipboard.writeText(text).then(() => {
            const orig = btn.textContent;
            btn.textContent = 'Copied!';
            btn.style.backgroundColor = '#16a34a';
            btn.style.color = '#ffffff';
            setTimeout(() => {
              btn.textContent = orig;
              btn.style.backgroundColor = '';
              btn.style.color = '';
            }, 2000);
          });
        });

        pre.appendChild(btn);
      });
    }

    _setupTabs() {
      document.querySelectorAll('.code-tab-group').forEach(group => {
        const buttons = group.querySelectorAll('.code-tab-btn');
        const contents = group.querySelectorAll('.code-tab-content');

        buttons.forEach((btn, index) => {
          btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            contents.forEach(c => c.style.display = 'none');

            btn.classList.add('active');
            if (contents[index]) {
              contents[index].style.display = 'block';
            }
          });
        });
      });
    }
  }

  const instance = new I18nManager();
  global.i18nManager = instance;
  global.I18n = instance;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => instance.init());
  } else {
    instance.init();
  }

})(typeof window !== 'undefined' ? window : this);
