/**
 * AMEVA Ecosystem - Multilingual (i18n) Core Engine
 * Zero-dependency, client-side internationalization manager with auto-detection.
 */

(function(global) {
  'use strict';

  const SUPPORTED_LANGUAGES = {
    'en': { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
    'ko': { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
    'ja': { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
    'zh': { code: 'zh', name: 'Chinese', nativeName: '简体中文', flag: '🇨🇳' },
    'es': { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
    'hi': { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' }
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
      this.translations = dict;
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

    _lookup(dict, keyPath) {
      return keyPath.split('.').reduce((acc, part) => (acc && acc[part] !== undefined) ? acc[part] : undefined, dict);
    }

    _setupLanguageSelectors() {
      const containers = document.querySelectorAll('.lang-selector-wrapper');
      containers.forEach(container => {
        const select = document.createElement('select');
        select.className = 'lang-select';
        select.setAttribute('aria-label', 'Select Language');

        Object.values(SUPPORTED_LANGUAGES).forEach(lang => {
          const opt = document.createElement('option');
          opt.value = lang.code;
          opt.textContent = `${lang.nativeName} (${lang.name})`;
          if (lang.code === this.currentLang) opt.selected = true;
          select.appendChild(opt);
        });

        select.addEventListener('change', (e) => {
          this.setLanguage(e.target.value);
        });

        container.innerHTML = '';
        container.appendChild(select);
      });
    }

    _setupCodeCopyButtons() {
      document.querySelectorAll('pre').forEach(pre => {
        if (pre.parentElement.classList.contains('code-wrapper')) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'code-wrapper';
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);

        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.textContent = 'Copy';
        btn.setAttribute('aria-label', 'Copy code to clipboard');

        btn.addEventListener('click', async () => {
          const code = pre.querySelector('code') ? pre.querySelector('code').innerText : pre.innerText;
          try {
            await navigator.clipboard.writeText(code);
            btn.textContent = 'Copied! ✓';
            setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
          } catch (err) {
            btn.textContent = 'Failed';
          }
        });

        wrapper.appendChild(btn);
      });
    }

    _setupTabs() {
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const parent = btn.closest('.tabs-container');
          if (!parent) return;
          const target = btn.getAttribute('data-tab');

          parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
          parent.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

          btn.classList.add('active');
          const targetContent = parent.querySelector(`.tab-content[data-tab-content="${target}"]`);
          if (targetContent) targetContent.classList.add('active');
        });
      });
    }
  }

  global.I18n = new I18nManager();
  document.addEventListener('DOMContentLoaded', () => {
    global.I18n.init();
  });
})(window);
