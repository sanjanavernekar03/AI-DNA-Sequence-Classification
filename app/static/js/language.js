/**
 * DNAura — Global Language Manager Engine
 * Supporting EXACTLY 5 Languages: English (en), Kannada (kn), Hindi (hi), Telugu (te), Tamil (ta)
 */

(function () {
    const STORAGE_KEY = "genomix_language_preference";
    const SUPPORTED_LANGUAGES = ["en", "kn", "hi", "te", "ta"];
    const DEFAULT_LANG = "en";

    let isTranslating = false;
    let observer = null;

    function getStoredLanguage() {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored && SUPPORTED_LANGUAGES.includes(stored)) {
                return stored;
            }
        } catch (e) {}
        return DEFAULT_LANG;
    }

    function setLanguage(lang) {
        if (!SUPPORTED_LANGUAGES.includes(lang)) {
            lang = DEFAULT_LANG;
        }
        try {
            localStorage.setItem(STORAGE_KEY, lang);
        } catch (e) {}
        
        document.documentElement.setAttribute("lang", lang);
        
        applyTranslations(lang);
        syncDropdowns(lang);

        window.dispatchEvent(new CustomEvent("languageChanged", { detail: { language: lang } }));
    }

    function applyTranslations(lang) {
        if (isTranslating) return;
        
        const targetLang = lang || getStoredLanguage();
        if (typeof window.TRANSLATIONS === "undefined" || !window.TRANSLATIONS[targetLang]) {
            return;
        }

        isTranslating = true;

        // Temporarily pause observer during translation modifications to prevent DOM mutation loop
        if (observer) {
            observer.disconnect();
        }

        try {
            const dict = window.TRANSLATIONS[targetLang];

            // Helper function to resolve key without silent fallback
            function resolveKey(key) {
                if (!key) return null;
                const val = dict[key];
                if (val !== undefined && val !== null) {
                    return val;
                }
                // If translation key is missing in active language, log warning
                if (targetLang !== DEFAULT_LANG) {
                    console.warn(`[i18n] Missing key '${key}' for language '${targetLang}'`);
                }
                // Fallback ONLY if key is completely missing in dictionary
                return (window.TRANSLATIONS[DEFAULT_LANG] && window.TRANSLATIONS[DEFAULT_LANG][key]) || null;
            }

            // Translate text content
            document.querySelectorAll("[data-i18n]").forEach(el => {
                const key = el.getAttribute("data-i18n");
                const translation = resolveKey(key);
                if (!translation) return;

                const iconEl = el.querySelector("i, svg");
                if (iconEl) {
                    const iconHTML = iconEl.outerHTML;
                    const newHTML = iconHTML + " " + translation;
                    if (el.innerHTML !== newHTML) {
                        el.innerHTML = newHTML;
                    }
                } else if (el.children.length === 0) {
                    if (el.textContent !== translation) {
                        el.textContent = translation;
                    }
                } else {
                    // Replace text nodes directly without destroying child badges/elements
                    let hasTextNode = false;
                    el.childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim() !== '') {
                            const newText = " " + translation + " ";
                            if (node.nodeValue !== newText) {
                                node.nodeValue = newText;
                            }
                            hasTextNode = true;
                        }
                    });
                    if (!hasTextNode && el.textContent !== translation) {
                        el.textContent = translation;
                    }
                }
            });

            // Translate placeholders
            document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
                const key = el.getAttribute("data-i18n-placeholder");
                const translation = resolveKey(key);
                if (translation && el.getAttribute("placeholder") !== translation) {
                    el.setAttribute("placeholder", translation);
                }
            });

            // Translate titles
            document.querySelectorAll("[data-i18n-title]").forEach(el => {
                const key = el.getAttribute("data-i18n-title");
                const translation = resolveKey(key);
                if (translation && el.getAttribute("title") !== translation) {
                    el.setAttribute("title", translation);
                }
            });

            // Translate input values (for submit/button inputs or default values)
            document.querySelectorAll("[data-i18n-value]").forEach(el => {
                const key = el.getAttribute("data-i18n-value");
                const translation = resolveKey(key);
                if (translation && el.value !== translation) {
                    el.value = translation;
                }
            });

            // Update document title if page title translation element exists
            const pageTitleEl = document.getElementById("page-i18n-title") || document.querySelector("title[data-i18n]");
            if (pageTitleEl) {
                const key = pageTitleEl.getAttribute("data-i18n");
                const translation = resolveKey(key);
                if (translation) {
                    document.title = translation;
                }
            }

            // Translate flashed messages if present
            document.querySelectorAll(".alert span[data-i18n-flash]").forEach(el => {
                const text = el.getAttribute("data-i18n-flash");
                if (!text) return;
                let matchedKey = text;
                if (!dict[matchedKey]) {
                    const enDict = window.TRANSLATIONS[DEFAULT_LANG] || {};
                    for (const [k, v] of Object.entries(enDict)) {
                        if (v === text) {
                            matchedKey = k;
                            break;
                        }
                    }
                }
                const translation = resolveKey(matchedKey);
                if (translation && el.textContent !== translation) {
                    el.textContent = translation;
                }
            });
        } finally {
            isTranslating = false;
            // Resume observer to watch for future dynamic DOM additions
            startObserver();
        }
    }

    function syncDropdowns(lang) {
        document.querySelectorAll(".global-lang-select, #chatbot-lang-select, #health-lang-select").forEach(select => {
            if (select.value !== lang) {
                select.value = lang;
            }
        });
    }

    function startObserver() {
        if (typeof MutationObserver === "undefined" || !document.body) return;
        if (!observer) {
            observer = new MutationObserver((mutations) => {
                if (isTranslating) return;
                let shouldTranslate = false;
                for (let i = 0; i < mutations.length; i++) {
                    const added = mutations[i].addedNodes;
                    for (let j = 0; j < added.length; j++) {
                        const node = added[j];
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            if (node.hasAttribute?.('data-i18n') || node.querySelector?.('[data-i18n], [data-i18n-placeholder], [data-i18n-title], [data-i18n-value]')) {
                                shouldTranslate = true;
                                break;
                            }
                        }
                    }
                    if (shouldTranslate) break;
                }
                if (shouldTranslate) {
                    applyTranslations(getStoredLanguage());
                }
            });
        }
        observer.observe(document.body, { childList: true, subtree: true });
    }

    window.getI18nText = function (key, defaultText) {
        const lang = getStoredLanguage();
        if (window.TRANSLATIONS && window.TRANSLATIONS[lang] && window.TRANSLATIONS[lang][key]) {
            return window.TRANSLATIONS[lang][key];
        }
        return defaultText || key;
    };

    window.LanguageManager = {
        getLanguage: getStoredLanguage,
        setLanguage: setLanguage,
        applyTranslations: function () {
            applyTranslations(getStoredLanguage());
        },
        getText: window.getI18nText
    };

    // Set document lang attribute immediately
    const currentLang = getStoredLanguage();
    document.documentElement.setAttribute("lang", currentLang);

    // Initial translation run
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            setLanguage(currentLang);
        });
    } else {
        setLanguage(currentLang);
    }

    window.addEventListener("load", () => {
        applyTranslations(getStoredLanguage());
    });

    // Event listener for language select dropdowns
    document.addEventListener("change", (e) => {
        if (e.target.matches(".global-lang-select, #chatbot-lang-select, #health-lang-select")) {
            const newLang = e.target.value;
            setLanguage(newLang);
        }
    });
})();
