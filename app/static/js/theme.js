/**
 * DNAura — Global Theme Manager (Light / Dark Mode)
 */
(function () {
    const THEME_STORAGE_KEY = 'dnaura_theme_preference';

    // 1. Immediate Anti-Flash Theme Initializer
    function applyEarlyTheme() {
        var savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
        if (savedTheme === 'dark') {
            document.documentElement.classList.add('dark-theme');
            if (document.body) document.body.classList.add('dark-theme');
        } else {
            document.documentElement.classList.remove('dark-theme');
            if (document.body) document.body.classList.remove('dark-theme');
        }
    }
    applyEarlyTheme();

    // 2. Global Theme Manager
    window.ThemeManager = {
        getTheme: function () {
            return localStorage.getItem(THEME_STORAGE_KEY) || 'light';
        },
        setTheme: function (theme) {
            const newTheme = theme === 'dark' ? 'dark' : 'light';
            localStorage.setItem(THEME_STORAGE_KEY, newTheme);
            document.documentElement.setAttribute('data-theme', newTheme);
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            if (document.body) {
                document.body.setAttribute('data-theme', newTheme);
                document.body.setAttribute('data-bs-theme', newTheme);
            }

            if (newTheme === 'dark') {
                document.documentElement.classList.add('dark-theme');
                if (document.body) document.body.classList.add('dark-theme');
            } else {
                document.documentElement.classList.remove('dark-theme');
                if (document.body) document.body.classList.remove('dark-theme');
            }

            this.updateToggleUI(newTheme);
        },
        toggleTheme: function () {
            const current = this.getTheme();
            const next = current === 'dark' ? 'light' : 'dark';
            this.setTheme(next);
        },
        updateToggleUI: function (theme) {
            const buttons = document.querySelectorAll('.theme-toggle-btn');
            const currentTheme = theme || this.getTheme();

            buttons.forEach(function (btn) {
                const darkIcon = btn.querySelector('.theme-icon-dark');
                const lightIcon = btn.querySelector('.theme-icon-light');
                const label = btn.querySelector('.theme-label');

                if (currentTheme === 'dark') {
                    if (darkIcon) darkIcon.style.display = 'inline-block';
                    if (lightIcon) lightIcon.style.display = 'none';
                    if (label) {
                        label.setAttribute('data-i18n', 'theme_dark');
                        if (window.getI18nText) {
                            label.textContent = window.getI18nText('theme_dark', 'Dark');
                        } else {
                            label.textContent = 'Dark';
                        }
                    }
                } else {
                    if (darkIcon) darkIcon.style.display = 'none';
                    if (lightIcon) lightIcon.style.display = 'inline-block';
                    if (label) {
                        label.setAttribute('data-i18n', 'theme_light');
                        if (window.getI18nText) {
                            label.textContent = window.getI18nText('theme_light', 'Light');
                        } else {
                            label.textContent = 'Light';
                        }
                    }
                }
            });
        }
    };

    // 3. Attach Event Listeners on DOMContentLoaded & window load
    function initThemeEvents() {
        const theme = window.ThemeManager.getTheme();
        window.ThemeManager.setTheme(theme);

        document.querySelectorAll('.theme-toggle-btn').forEach(function (btn) {
            btn.removeEventListener('click', handleToggleClick);
            btn.addEventListener('click', handleToggleClick);
        });
    }

    function handleToggleClick(e) {
        e.preventDefault();
        window.ThemeManager.toggleTheme();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initThemeEvents);
    } else {
        initThemeEvents();
    }
})();
