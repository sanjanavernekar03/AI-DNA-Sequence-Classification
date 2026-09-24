/**
 * Multilingual Voice Assistant Service (Browser Native Web Speech API)
 * Supports English (en-US), Hindi (hi-IN), Kannada (kn-IN)
 */

window.VoiceAssistant = {
    speechRecognition: null,
    speechSynth: window.speechSynthesis,
    isListening: false,
    autoSpeakEnabled: true,
    
    // Language BC47 Codes Mapping
    langCodes: {
        'en': 'en-US',
        'hi': 'hi-IN',
        'kn': 'kn-IN',
        'te': 'te-IN',
        'ta': 'ta-IN'
    },

    init: function() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.speechRecognition = new SpeechRecognition();
            this.speechRecognition.continuous = false;
            this.speechRecognition.interimResults = false;
        } else {
            console.warn("Web Speech Recognition API is not supported in this browser.");
        }
    },

    startListening: function(lang, onResultCallback, onErrorCallback, onEndCallback) {
        if (!this.speechRecognition) {
            if (onErrorCallback) onErrorCallback("Speech recognition is not supported in your browser.");
            return;
        }

        const bcp47 = this.langCodes[lang] || 'en-US';
        this.speechRecognition.lang = bcp47;

        this.speechRecognition.onstart = () => {
            this.isListening = true;
        };

        this.speechRecognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (onResultCallback) onResultCallback(transcript);
        };

        this.speechRecognition.onerror = (event) => {
            this.isListening = false;
            if (onErrorCallback) onErrorCallback(event.error);
        };

        this.speechRecognition.onend = () => {
            this.isListening = false;
            if (onEndCallback) onEndCallback();
        };

        try {
            this.speechRecognition.start();
        } catch (e) {
            console.error("Error starting speech recognition:", e);
        }
    },

    stopListening: function() {
        if (this.speechRecognition && this.isListening) {
            this.speechRecognition.stop();
            this.isListening = false;
        }
    },

    speak: function(text, lang) {
        if (!this.speechSynth) return;
        this.speechSynth.cancel(); // Stop any ongoing speech

        const cleanText = text.replace(/[\*\_#`]/g, ''); // Strip markdown
        const utterance = new SpeechSynthesisUtterance(cleanText);
        const bcp47 = this.langCodes[lang] || 'en-US';
        utterance.lang = bcp47;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        // Try to match voice for language
        const voices = this.speechSynth.getVoices();
        const matchedVoice = voices.find(v => v.lang.startsWith(lang) || v.lang === bcp47);
        if (matchedVoice) {
            utterance.voice = matchedVoice;
        }

        this.speechSynth.speak(utterance);
    },

    stopSpeaking: function() {
        if (this.speechSynth) {
            this.speechSynth.cancel();
        }
    }
};

// Auto-initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    window.VoiceAssistant.init();
});
