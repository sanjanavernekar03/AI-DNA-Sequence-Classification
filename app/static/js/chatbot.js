/**
 * Global AI Chatbot & Voice Assistant Frontend Controller
 */

document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("chatbot-toggle-btn");
    const panel = document.getElementById("chatbot-panel");
    const closeBtn = document.getElementById("chatbot-close-btn");
    const conversation = document.getElementById("chatbot-conversation");
    const form = document.getElementById("chatbot-form");
    const input = document.getElementById("chatbot-input");
    const langSelect = document.getElementById("chatbot-lang-select");
    const voiceInputBtn = document.getElementById("btn-voice-input");
    const voiceOutputBtn = document.getElementById("btn-voice-output-toggle");
    const voiceStatus = document.getElementById("voice-status-text");
    const suggestions = document.querySelectorAll("[data-chat-prompt]");

    let isAudioOutputEnabled = true;
    const conversationHistory = [];
    let userCoords = null;

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (pos) {
                userCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
            },
            function () {},
            { timeout: 5000 }
        );
    }

    if (!toggleBtn || !panel) return;

    suggestions.forEach(function (suggestion) {
        suggestion.addEventListener("click", function () {
            const prompt = suggestion.dataset.chatPrompt;
            if (prompt) sendMessage(prompt);
        });
    });

    // Toggle Chatbot Panel
    toggleBtn.addEventListener("click", function () {
        panel.classList.toggle("d-none");
        if (!panel.classList.contains("d-none")) {
            input.focus();
            if (navigator.geolocation && !userCoords) {
                navigator.geolocation.getCurrentPosition(
                    function (pos) {
                        userCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                    },
                    function () {},
                    { timeout: 3000 }
                );
            }
        }
    });

    closeBtn.addEventListener("click", function () {
        panel.classList.add("d-none");
        if (window.VoiceAssistant) window.VoiceAssistant.stopSpeaking();
    });

    // Voice Output Toggle
    if (voiceOutputBtn) {
        voiceOutputBtn.addEventListener("click", function () {
            isAudioOutputEnabled = !isAudioOutputEnabled;
            if (isAudioOutputEnabled) {
                voiceOutputBtn.classList.add("active");
                voiceOutputBtn.classList.replace("btn-outline-secondary", "btn-outline-cyan");
            } else {
                voiceOutputBtn.classList.remove("active");
                voiceOutputBtn.classList.replace("btn-outline-cyan", "btn-outline-secondary");
                if (window.VoiceAssistant) window.VoiceAssistant.stopSpeaking();
            }
        });
    }

    function getI18nText(key, defaultText) {
        const lang = (window.LanguageManager && window.LanguageManager.getLanguage) ? window.LanguageManager.getLanguage() : 'en';
        if (window.TRANSLATIONS && window.TRANSLATIONS[lang] && window.TRANSLATIONS[lang][key]) {
            return window.TRANSLATIONS[lang][key];
        }
        return defaultText;
    }

    // Voice Input Speech Recognition
    if (voiceInputBtn) {
        voiceInputBtn.addEventListener("click", function () {
            const lang = langSelect ? langSelect.value : ((window.LanguageManager && window.LanguageManager.getLanguage) ? window.LanguageManager.getLanguage() : 'en');
            if (window.VoiceAssistant && window.VoiceAssistant.isListening) {
                window.VoiceAssistant.stopListening();
                voiceInputBtn.classList.remove("btn-danger");
                voiceInputBtn.classList.add("btn-outline-emerald");
                voiceStatus.textContent = "";
                return;
            }

            voiceInputBtn.classList.remove("btn-outline-emerald");
            voiceInputBtn.classList.add("btn-danger");
            voiceStatus.textContent = getI18nText('js_listening', 'Listening...');

            window.VoiceAssistant.startListening(
                lang,
                function (transcript) {
                    input.value = transcript;
                    voiceStatus.textContent = getI18nText('js_processing', 'Processing speech...');
                    sendMessage(transcript);
                },
                function (err) {
                    voiceStatus.textContent = getI18nText('js_mic_error', 'Mic error:') + " " + err;
                    voiceInputBtn.classList.remove("btn-danger");
                    voiceInputBtn.classList.add("btn-outline-emerald");
                },
                function () {
                    voiceInputBtn.classList.remove("btn-danger");
                    voiceInputBtn.classList.add("btn-outline-emerald");
                    voiceStatus.textContent = "";
                }
            );
        });
    }

    // Send Form Submission
    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            const text = input.value.strip ? input.value.strip() : input.value.trim();
            if (text) {
                sendMessage(text);
            }
        });
    }

    function sendMessage(text) {
        appendMessage("user", text);
        input.value = "";

        const currentLang = (window.LanguageManager && window.LanguageManager.getLanguage) ? window.LanguageManager.getLanguage() : (langSelect ? langSelect.value : 'en');
        const currentPath = window.location.pathname;

        // Show typing indicator
        const typingId = appendTypingIndicator();

        fetch("/api/chatbot/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message: text,
                current_page: currentPath,
                language: currentLang,
                conversation: conversationHistory.slice(-10),
                user_location: userCoords
            })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator(typingId);
            if (data.error) {
                appendMessage("assistant", "Error: " + data.error);
            } else {
                appendMessage("assistant", data.response);
                conversationHistory.push({ role: "user", content: text });
                conversationHistory.push({ role: "assistant", content: data.response });
                if (isAudioOutputEnabled && window.VoiceAssistant) {
                    window.VoiceAssistant.speak(data.response, currentLang);
                }

                // Execute controlled action if returned (e.g. Navigation or Confirmation)
                if (data.action && data.action !== 'CHATBOT' && data.action !== 'SHOW_RECOMMENDATION' && window.VoiceAssistant) {
                    window.VoiceAssistant.handleControlledAction(data, text, function() {});
                }
            }
        })
        .catch(err => {
            removeTypingIndicator(typingId);
            appendMessage("assistant", getI18nText('js_cannot_connect', 'Unable to connect to assistant backend.'));
        });
    }

    function appendMessage(sender, text, disclaimer) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `chat-message ${sender}-msg mb-3`;

        let html = "";
        if (sender === "user") {
            html = `
                <div class="msg-bubble user-bubble shadow-sm">
                    <div>${escapeHtml(text)}</div>
                </div>
            `;
        } else {
            let formattedText = escapeHtml(text);
            formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
            formattedText = formattedText.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function(match, label, url) {
                if (url.includes('/appointments/book')) {
                    return `<a href="${url}" class="btn btn-sm btn-primary me-1 my-1 text-white text-decoration-none d-inline-flex align-items-center" style="font-size: 0.8rem; padding: 4px 10px; border-radius: 6px;"><i class="bi bi-calendar-plus me-1"></i>${label}</a>`;
                }
                if (url.includes('/hospitals/')) {
                    return `<a href="${url}" class="btn btn-sm btn-outline-primary me-1 my-1 text-decoration-none d-inline-flex align-items-center" style="font-size: 0.8rem; padding: 4px 10px; border-radius: 6px;"><i class="bi bi-hospital me-1"></i>${label}</a>`;
                }
                if (url.includes('google.com/maps') || url.includes('maps.google')) {
                    return `<a href="${url}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-danger me-1 my-1 text-decoration-none d-inline-flex align-items-center" style="font-size: 0.8rem; padding: 4px 10px; border-radius: 6px;"><i class="bi bi-geo-alt-fill me-1"></i>${label}</a>`;
                }
                return `<a href="${url}" class="text-primary text-decoration-underline" target="_blank">${label}</a>`;
            });
            formattedText = formattedText.replace(/\n/g, "<br>");

            html = `
                <div class="msg-bubble assistant-bubble shadow-sm">
                    <div class="fw-semibold text-emerald mb-1 small"><i class="bi bi-robot me-1"></i>DNAura Assistant</div>
                    <div>${formattedText}</div>
                    ${disclaimer ? `
                    <div class="disclaimer-chip mt-2">
                        <i class="bi bi-shield-exclamation me-1 text-warning"></i>
                        <span>${escapeHtml(disclaimer)}</span>
                    </div>` : ""}
                </div>
            `;
        }

        msgDiv.innerHTML = html;
        conversation.appendChild(msgDiv);
        conversation.scrollTop = conversation.scrollHeight;
    }

    // Expose ChatbotUI globally for Voice Assistant integration
    window.ChatbotUI = {
        appendMessage: appendMessage,
        sendMessage: sendMessage
    };

    // Voice Input Microphone Button Handler
    if (voiceInputBtn) {
        voiceInputBtn.addEventListener("click", function () {
            if (window.VoiceAssistant) {
                window.VoiceAssistant.triggerVoiceCommand(function(state, label) {
                    if (state === 'listening') {
                        voiceInputBtn.classList.remove("btn-outline-secondary", "btn-outline-emerald");
                        voiceInputBtn.classList.add("btn-danger");
                    } else if (state === 'idle' || state === 'success' || state === 'error') {
                        voiceInputBtn.classList.remove("btn-danger");
                        voiceInputBtn.classList.add("btn-outline-secondary");
                    }
                });
            }
        });
    }

    function appendTypingIndicator() {
        const id = "typing-" + Date.now();
        const msgDiv = document.createElement("div");
        msgDiv.id = id;
        msgDiv.className = "chat-message assistant-msg mb-3";
        msgDiv.innerHTML = `
            <div class="msg-bubble assistant-bubble shadow-sm py-2">
                <span class="spinner-grow spinner-grow-sm text-emerald" role="status"></span>
                <span class="small text-muted ms-2">${getI18nText('js_assistant_thinking', 'Assistant thinking...')}</span>
            </div>
        `;
        conversation.appendChild(msgDiv);
        conversation.scrollTop = conversation.scrollHeight;
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});

