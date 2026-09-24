/**
 * DNAura — Global UI Utilities & Interactive Handlers
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize auto dismiss alerts
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 6000);
    });

    function getI18nText(key, defaultText) {
        if (typeof window.getI18nText === 'function') {
            const res = window.getI18nText(key);
            if (res && res !== key) return res;
        }
        const lang = (window.GenomixLanguage && window.GenomixLanguage.getLanguage) ? window.GenomixLanguage.getLanguage() : ((window.LanguageManager && window.LanguageManager.getLanguage) ? window.LanguageManager.getLanguage() : 'en');
        if (window.TRANSLATIONS && window.TRANSLATIONS[lang] && window.TRANSLATIONS[lang][key]) {
            return window.TRANSLATIONS[lang][key];
        }
        return defaultText;
    }

    // 2. Sample sequence loader handler
    const sampleButtons = document.querySelectorAll('[data-sample-key]');
    sampleButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetInputId = btn.getAttribute('data-target-input') || 'sequence_input';
            const nameInputId = btn.getAttribute('data-target-name') || 'sequence_name_input';
            const seqValue = btn.getAttribute('data-seq-val') || '';
            const seqName = btn.getAttribute('data-seq-name') || '';

            const inputElem = document.getElementById(targetInputId);
            if (inputElem) {
                inputElem.value = seqValue;
                inputElem.focus();
                // Trigger input event
                inputElem.dispatchEvent(new Event('input', { bubbles: true }));
            }

            const nameElem = document.getElementById(nameInputId);
            if (nameElem && seqName) {
                nameElem.value = seqName;
            }

            showToast(getI18nText('js_sample_loaded', 'Sample Loaded'), `Loaded '${seqName || "Sample sequence"}' into input area.`, 'info');
        });
    });

    // 3. Live sequence stats preview in input boxes
    const seqInputs = document.querySelectorAll('textarea[name="sequence"], textarea[name="reference_sequence"], textarea[name="sample_sequence"], textarea[name="query_sequence"]');
    seqInputs.forEach(input => {
        const counterId = input.getAttribute('data-counter-id');
        if (counterId) {
            const counterElem = document.getElementById(counterId);
            const updateStats = () => {
                const raw = input.value.replace(/\s+/g, '').toUpperCase();
                const len = raw.length;
                let gc = 0;
                if (len > 0) {
                    const g = (raw.match(/G/g) || []).length;
                    const c = (raw.match(/C/g) || []).length;
                    gc = Math.round(((g + c) / len) * 100);
                }
                if (counterElem) {
                    const lenLabel = (window.getI18nText) ? window.getI18nText('mod_seq_len', 'Length') : 'Length';
                    counterElem.innerHTML = `${lenLabel}: <strong>${len} bp</strong> | GC: <strong>${gc}%</strong>`;
                }
            };
            input.addEventListener('input', updateStats);
            updateStats();
        }
    });

    // 4. Copy to clipboard
    const copyButtons = document.querySelectorAll('[data-copy-target]');
    copyButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-copy-target');
            const targetElem = document.getElementById(targetId);
            if (targetElem) {
                const text = targetElem.innerText || targetElem.value;
                navigator.clipboard.writeText(text).then(() => {
                    showToast(getI18nText('js_copied', 'Copied'), getI18nText('js_seq_copied', 'Sequence content copied to clipboard.'), 'success');
                });
            }
        });
    });
});

// Lightweight Toast Notification
function showToast(title, message, type = 'info') {
    let container = document.getElementById('genomix-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'genomix-toast-container';
        container.style.position = 'fixed';
        container.style.bottom = '24px';
        container.style.right = '24px';
        container.style.zIndex = '9999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '8px';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const borderColors = {
        success: '#10B981',
        danger: '#EF4444',
        info: '#06B6D4',
        warning: '#F59E0B'
    };
    const borderColor = borderColors[type] || '#10B981';

    toast.className = 'card-glass';
    toast.style.padding = '12px 18px';
    toast.style.minWidth = '260px';
    toast.style.maxWidth = '360px';
    toast.style.borderLeft = `4px solid ${borderColor}`;
    toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
    toast.style.animation = 'fadeInUp 0.3s ease';

    toast.innerHTML = `
        <div style="font-weight:600; font-size:0.9rem; color:#F8FAFC;">${title}</div>
        <div style="font-size:0.82rem; color:#94A3B8; margin-top:2px;">${message}</div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
