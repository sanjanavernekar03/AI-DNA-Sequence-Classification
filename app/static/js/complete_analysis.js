/**
 * DNAura — Complete DNA Analysis Interactive Orchestration Runner
 */

document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('btn-run-complete-analysis');
    const form = document.getElementById('complete-analysis-form');
    const progressModalElem = document.getElementById('completeAnalysisProgressModal');

    if (!runBtn || !form) return;

    let progressModal = null;
    if (progressModalElem) {
        progressModal = new bootstrap.Modal(progressModalElem, { backdrop: 'static', keyboard: false });
    }

    form.addEventListener('submit', async (e) => {
        // Intercept standard submission for live animated step-by-step progress
        e.preventDefault();

        function getI18nText(key, defaultText) {
            const lang = (window.LanguageManager && window.LanguageManager.getLanguage) ? window.LanguageManager.getLanguage() : 'en';
            if (window.TRANSLATIONS && window.TRANSLATIONS[lang] && window.TRANSLATIONS[lang][key]) {
                return window.TRANSLATIONS[lang][key];
            }
            return defaultText;
        }

        const seqInput = document.getElementById('sequence_input');
        if (!seqInput || !seqInput.value.trim()) {
            showToast(getI18nText('js_val_err', 'Validation Error'), getI18nText('js_input_seq', 'Please input or select a target DNA sequence.'), 'danger');
            return;
        }

        if (progressModal) {
            progressModal.show();
        }

        // Step animation helper
        const setStepActive = (stepId) => {
            const el = document.getElementById(stepId);
            if (el) {
                el.className = 'progress-step-item step-active';
                const statusIcon = el.querySelector('.step-icon');
                if (statusIcon) statusIcon.innerHTML = '<span class="spinner-border spinner-border-sm text-info" role="status"></span>';
            }
        };

        const setStepDone = (stepId) => {
            const el = document.getElementById(stepId);
            if (el) {
                el.className = 'progress-step-item step-done';
                const statusIcon = el.querySelector('.step-icon');
                if (statusIcon) statusIcon.innerHTML = '<i class="bi bi-check-circle-fill text-emerald"></i>';
            }
        };

        try {
            // Animate initial steps
            setStepActive('step-seq');
            await new Promise(r => setTimeout(r, 400));
            setStepDone('step-seq');

            setStepActive('step-sim');
            await new Promise(r => setTimeout(r, 450));
            setStepDone('step-sim');

            setStepActive('step-mut');
            await new Promise(r => setTimeout(r, 400));
            setStepDone('step-mut');

            setStepActive('step-clf');

            // Send actual async request
            const payload = {
                sequence: seqInput.value,
                sequence_name: document.getElementById('sequence_name_input')?.value || 'Target Sample Sequence',
                reference_sequence: document.getElementById('reference_sequence_input')?.value || '',
                reference_name: document.getElementById('reference_name_input')?.value || 'Wildtype Reference'
            };

            const response = await fetch('/analysis/complete/api/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            // Check if response is JSON or if it was redirected to login
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                // If it returned HTML (e.g. login page), redirect them to login
                window.location.href = '/auth/login';
                return;
            }

            const data = await response.json();

            setStepDone('step-clf');
            setStepActive('step-dis');
            await new Promise(r => setTimeout(r, 450));
            setStepDone('step-dis');

            setStepActive('step-vis');
            await new Promise(r => setTimeout(r, 400));
            setStepDone('step-vis');

            if (data.success && data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                if (progressModal) {
                    setTimeout(() => progressModal.hide(), 500); // delay to prevent transition conflicts
                }
                showToast(getI18nText('js_exec_err', 'Execution Error'), data.error || getI18nText('js_fail_pipeline', 'Failed to complete DNA analysis pipeline.'), 'danger');
            }
        } catch (err) {
            if (progressModal) progressModal.hide();
            showToast(getI18nText('js_exec_err', 'Execution Error'), err.message || getI18nText('js_fail_pipeline', 'Could not complete analysis.'), 'danger');
        }
    });
});
