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

            // Localize dynamic user display name in greeting
            document.querySelectorAll("[data-user-name]").forEach(el => {
                const origName = el.getAttribute("data-user-name");
                if (origName) {
                    const localized = localizeUserName(origName, targetLang);
                    if (el.textContent !== localized) {
                        el.textContent = localized;
                    }
                }
            });
        } finally {
            isTranslating = false;
            // Resume observer to watch for future dynamic DOM additions
            startObserver();
        }
    }

    /**
     * Generic Dynamic Indic Name Transliteration Engine
     * Converts ANY arbitrary dynamic user name in Latin script into Hindi, Kannada, Tamil, or Telugu scripts
     * purely algorithmically. Zero hardcoded person name dictionaries.
     */
    function transliterateGenericWord(word, lang) {
        if (!word || lang === "en") return word;
        const cleanWord = word.trim();
        if (!/^[a-zA-Z]+$/.test(cleanWord)) {
            return cleanWord;
        }

        const lower = cleanWord.toLowerCase();
        const tables = {
            hi: {
                ind_vowels: { "aa": "आ", "ai": "ऐ", "au": "औ", "ee": "ई", "oo": "ऊ", "a": "अ", "i": "इ", "u": "उ", "e": "ए", "o": "ओ" },
                dep_vowels: { "aa": "ा", "ai": "ै", "au": "ौ", "ee": "ी", "oo": "ू", "a": "", "i": "ि", "u": "ु", "e": "े", "o": "ो" },
                consonants: {
                    "ksh": "क्ष", "gya": "ज्ञ", "tr": "त्र", "shr": "श्र",
                    "ny": "न्य", "vy": "व्य", "dy": "द्य", "ty": "त्य", "ry": "र्य", "sy": "स्य", "my": "म्य", "ly": "ल्या",
                    "sh": "श", "ch": "च", "th": "थ", "ph": "फ", "bh": "भ", "dh": "ध", "gh": "घ", "kh": "ख", "zh": "झ",
                    "b": "ब", "c": "क", "d": "द", "f": "फ", "g": "ग", "h": "ह", "j": "ज", "k": "क",
                    "l": "ल", "m": "म", "n": "न", "p": "प", "q": "क", "r": "र", "s": "स", "t": "त",
                    "v": "व", "w": "व", "x": "क्स", "y": "य", "z": "ज़"
                },
                virama: "्",
                anusvara: "ं"
            },
            kn: {
                ind_vowels: { "aa": "ಆ", "ai": "ಐ", "au": "ಔ", "ee": "ಈ", "oo": "ಊ", "a": "ಅ", "i": "ಇ", "u": "ಉ", "e": "ಎ", "o": "ಒ" },
                dep_vowels: { "aa": "ಾ", "ai": "ೈ", "au": "ೌ", "ee": "ೀ", "oo": "ೂ", "a": "", "i": "ಿ", "u": "ು", "e": "ೆ", "o": "ೊ" },
                consonants: {
                    "ksh": "ಕ್ಷ", "tr": "ತ್ರ",
                    "ny": "ನ್ಯ", "vy": "ವ್ಯ", "dy": "ದ್ಯ", "ty": "ತ್ಯ", "ry": "ರ್ಯ", "sy": "ಸ್ಯ", "my": "ಮ್ಯ",
                    "sh": "ಶ", "ch": "ಚ", "th": "ಥ", "ph": "ಫ", "bh": "ಭ", "dh": "ಧ", "gh": "ಘ", "kh": "ಖ",
                    "b": "ಬ", "c": "ಕ", "d": "ದ", "f": "ಫ", "g": "ಗ", "h": "ಹ", "j": "ಜ", "k": "ಕ",
                    "l": "ಲ", "m": "ಮ", "n": "ನ", "p": "ಪ", "q": "ಕ", "r": "ರ", "s": "ಸ", "t": "ತ",
                    "v": "ವ", "w": "ವ", "y": "ಯ", "z": "ಜ"
                },
                virama: "್",
                anusvara: "ಂ"
            },
            ta: {
                ind_vowels: { "aa": "ஆ", "ai": "ஐ", "au": "ஔ", "ee": "ஈ", "oo": "ஊ", "a": "அ", "i": "இ", "u": "உ", "e": "எ", "o": "ஒ" },
                dep_vowels: { "aa": "ா", "ai": "ை", "au": "ௌ", "ee": "ீ", "oo": "ூ", "a": "", "i": "ி", "u": "ு", "e": "ெ", "o": "ொ" },
                consonants: {
                    "ny": "ன்ய", "vy": "வ்ய", "dy": "த்ய", "ty": "த்ய",
                    "sh": "ஷ்", "ch": "ச", "th": "த", "ph": "ப", "bh": "ப", "dh": "த", "gh": "க", "kh": "க",
                    "b": "ப", "c": "க", "d": "ட", "f": "ஃப", "g": "க", "h": "ஹ", "j": "ஜ", "k": "க",
                    "l": "ல", "m": "ம", "n": "ன", "p": "ப", "q": "க", "r": "ர", "s": "ஸ", "t": "த",
                    "v": "வ", "w": "வ", "y": "ய", "z": "ஸ"
                },
                virama: "்",
                anusvara: "ம்"
            },
            te: {
                ind_vowels: { "aa": "ఆ", "ai": "ఐ", "au": "ఔ", "ee": "ఈ", "oo": "ఊ", "a": "అ", "i": "ఇ", "u": "ఉ", "e": "ఎ", "o": "ఒ" },
                dep_vowels: { "aa": "ా", "ai": "ై", "au": "ౌ", "ee": "ీ", "oo": "ూ", "a": "", "i": "ి", "u": "ు", "e": "ె", "o": "ొ" },
                consonants: {
                    "ksh": "క్ష", "tr": "త్ర",
                    "ny": "న్య", "vy": "వ్య", "dy": "ద్య", "ty": "త్య", "ry": "ర్య", "sy": "స్య", "my": "మ్య",
                    "sh": "ష", "ch": "చ", "th": "త", "ph": "ఫ", "bh": "భ", "dh": "ధ", "gh": "ఘ", "kh": "ఖ",
                    "b": "బ", "c": "క", "d": "ద", "f": "ఫ", "g": "గ", "h": "హ", "j": "జ", "k": "క",
                    "l": "ల", "m": "మ", "n": "న", "p": "ప", "q": "క", "r": "ర", "s": "స", "t": "త",
                    "v": "వ", "w": "వ", "y": "య", "z": "జ"
                },
                virama: "్",
                anusvara: "ం"
            }
        };

        const script = tables[lang];
        if (!script) return word;

        let i = 0;
        const n = lower.length;
        const result = [];
        let lastWasConsonant = false;
        let isFirstSyllable = true;

        while (i < n) {
            // Anusvara check for 'an' / 'am'
            if ((lower.substring(i, i + 2) === "an" || lower.substring(i, i + 2) === "am") && i + 2 < n && !"aeiouy".includes(lower[i + 2])) {
                if (lastWasConsonant && script.anusvara) {
                    result.push(script.anusvara);
                    i += 2;
                    lastWasConsonant = false;
                    continue;
                }
            }

            // Try consonants (ordered longest match first)
            const consKeys = ["ksh", "gya", "shr", "tr", "ny", "vy", "dy", "ty", "ry", "sy", "my", "ly",
                              "sh", "ch", "th", "ph", "bh", "dh", "gh", "kh", "zh",
                              "b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "q", "r", "s", "t", "v", "w", "x", "y", "z"];
            let cMatch = null;
            for (const ck of consKeys) {
                if (lower.startsWith(ck, i) && script.consonants[ck]) {
                    cMatch = ck;
                    break;
                }
            }

            if (cMatch) {
                if (lastWasConsonant && script.virama && lang !== "ta") {
                    result.push(script.virama);
                }
                result.push(script.consonants[cMatch]);
                i += cMatch.length;
                lastWasConsonant = true;
                continue;
            }

            // Try vowels (ordered longest match first)
            const vKeys = ["aa", "ai", "au", "ee", "oo", "a", "i", "u", "e", "o"];
            let vMatch = null;
            for (const vk of vKeys) {
                if (lower.startsWith(vk, i)) {
                    vMatch = vk;
                    break;
                }
            }

            if (vMatch) {
                if (lastWasConsonant) {
                    let matra = script.dep_vowels[vMatch] !== undefined ? script.dep_vowels[vMatch] : "";
                    if (vMatch === "a" && isFirstSyllable && i + 1 < n && !"aeiou".includes(lower[i + 1])) {
                        matra = script.dep_vowels["aa"];
                    } else if (vMatch === "a" && i + 1 === n && n > 3) {
                        matra = script.dep_vowels["aa"];
                    } else if (vMatch === "u" && i + 1 === n && lang === "hi") {
                        matra = script.dep_vowels["oo"];
                    }
                    result.push(matra);
                } else {
                    const indVowel = script.ind_vowels[vMatch] || "";
                    result.push(indVowel);
                }
                i += vMatch.length;
                lastWasConsonant = false;
                isFirstSyllable = false;
                continue;
            }

            result.push(lower[i]);
            i++;
            lastWasConsonant = false;
        }

        if (lastWasConsonant && script.virama && (lang === "kn" || lang === "ta" || lang === "te")) {
            result.push(script.virama);
        }

        return result.join("") || word;
    }

    function localizeUserName(fullName, lang) {
        if (!fullName || !lang || lang === "en") return fullName;
        const parts = fullName.trim().split(/\s+/);
        const localizedParts = parts.map(p => transliterateGenericWord(p, lang));
        return localizedParts.join(" ");
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
