/**
 * DNAura — Authentication System Scripts (auth.js)
 * Handles Password Visibility, Two-Step Registration, and Client Validations.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Password Visibility Toggle
    const toggleBtns = document.querySelectorAll('.password-toggle-btn');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = btn.getAttribute('data-target-input');
            const input = document.getElementById(targetId);
            const icon = btn.querySelector('i');
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    if (icon) {
                        icon.classList.remove('bi-eye');
                        icon.classList.add('bi-eye-slash');
                    }
                } else {
                    input.type = 'password';
                    if (icon) {
                        icon.classList.remove('bi-eye-slash');
                        icon.classList.add('bi-eye');
                    }
                }
            }
        });
    });

    // 2. Two-Step Registration Logic
    const regForm = document.getElementById('multi-step-register-form');
    const step1Pane = document.getElementById('step-1-pane');
    const step2Pane = document.getElementById('step-2-pane');
    const btnNext = document.getElementById('btn-step1-next');
    const btnBack = document.getElementById('btn-step2-back');
    const node1 = document.getElementById('node-step-1');
    const node2 = document.getElementById('node-step-2');
    const divider = document.getElementById('step-divider');

    if (step1Pane && step2Pane && btnNext && btnBack) {
        // Step 1 -> Step 2
        btnNext.addEventListener('click', () => {
            if (validateStep1()) {
                step1Pane.classList.remove('active');
                step2Pane.classList.add('active');

                if (node1) {
                    node1.classList.remove('active');
                    node1.classList.add('completed');
                    const circle1 = node1.querySelector('.node-circle');
                    if (circle1) circle1.innerHTML = '<i class="bi bi-check-lg"></i>';
                }

                if (divider) divider.classList.add('active');
                if (node2) node2.classList.add('active');
            }
        });

        // Step 2 -> Step 1 (Back)
        btnBack.addEventListener('click', () => {
            step2Pane.classList.remove('active');
            step1Pane.classList.add('active');

            if (node1) {
                node1.classList.remove('completed');
                node1.classList.add('active');
                const circle1 = node1.querySelector('.node-circle');
                if (circle1) circle1.textContent = '1';
            }

            if (divider) divider.classList.remove('active');
            if (node2) node2.classList.remove('active');
        });

        // Form Submit Validation for Step 2
        if (regForm) {
            regForm.addEventListener('submit', (e) => {
                if (!validateStep2()) {
                    e.preventDefault();
                }
            });
        }
    }

    function validateStep1() {
        let isValid = true;
        const nameInput = document.getElementById('reg_fullname');
        if (nameInput) {
            const val = nameInput.value.trim();
            if (!val || val.length < 2) {
                setFieldError(nameInput, 'reg_fullname_err', 'reg_err_fullname', 'Please provide your full name.');
                isValid = false;
            } else {
                clearFieldError(nameInput, 'reg_fullname_err');
            }
        }
        return isValid;
    }

    function validateStep2() {
        let isValid = true;
        const emailInput = document.getElementById('reg_email');
        const userInput = document.getElementById('reg_username');
        const passInput = document.getElementById('reg_password');
        const confInput = document.getElementById('reg_confirm_password');

        if (emailInput) {
            const emailVal = emailInput.value.trim();
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailVal || !emailRegex.test(emailVal)) {
                setFieldError(emailInput, 'reg_email_err', 'reg_err_email', 'Please enter a valid email address.');
                isValid = false;
            } else {
                clearFieldError(emailInput, 'reg_email_err');
            }
        }

        if (userInput) {
            const userVal = userInput.value.trim();
            const userRegex = /^[a-zA-Z0-9_]{3,30}$/;
            if (!userVal || !userRegex.test(userVal)) {
                setFieldError(userInput, 'reg_username_err', 'reg_err_username', 'Username must be 3-30 characters (alphanumeric).');
                isValid = false;
            } else {
                clearFieldError(userInput, 'reg_username_err');
            }
        }

        if (passInput) {
            const passVal = passInput.value;
            if (!passVal || passVal.length < 8) {
                setFieldError(passInput, 'reg_password_err', 'reg_err_password', 'Password must be at least 8 characters.');
                isValid = false;
            } else {
                clearFieldError(passInput, 'reg_password_err');
            }
        }

        if (confInput && passInput) {
            const passVal = passInput.value;
            const confVal = confInput.value;
            if (confVal !== passVal) {
                setFieldError(confInput, 'reg_confirm_password_err', 'reg_err_confirm', 'Passwords do not match.');
                isValid = false;
            } else {
                clearFieldError(confInput, 'reg_confirm_password_err');
            }
        }

        return isValid;
    }

    function setFieldError(inputElem, errorElemId, key, defaultMsg) {
        inputElem.classList.add('is-invalid');
        inputElem.classList.remove('is-valid');
        const errElem = document.getElementById(errorElemId);
        if (errElem) {
            errElem.textContent = defaultMsg;
            errElem.classList.add('visible');
        }
    }

    function clearFieldError(inputElem, errorElemId) {
        inputElem.classList.remove('is-invalid');
        inputElem.classList.add('is-valid');
        const errElem = document.getElementById(errorElemId);
        if (errElem) {
            errElem.textContent = '';
            errElem.classList.remove('visible');
        }
    }
});
