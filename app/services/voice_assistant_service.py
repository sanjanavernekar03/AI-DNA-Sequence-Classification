import json
import logging
import re
from typing import Dict, Any, Optional

from app.services.chatbot_service import get_chatbot_response, ChatbotServiceError, _call_ollama
from app.services.recommendation_service import get_ai_recommendation, extract_intent_and_entities

logger = logging.getLogger(__name__)

# Controlled Action Whitelist
ALLOWED_INTENTS = {
    'OPEN_DASHBOARD',
    'OPEN_COMPLETE_ANALYSIS',
    'OPEN_SIMILARITY',
    'OPEN_MUTATION',
    'OPEN_CLASSIFICATION',
    'OPEN_DISEASE_PREDICTION',
    'OPEN_VISUALIZATION',
    'OPEN_HEALTH_GUIDANCE',
    'OPEN_DIET_PLANNER',
    'OPEN_HOSPITALS',
    'OPEN_APPOINTMENTS',
    'OPEN_REPORTS',
    'OPEN_PROFILE',
    'OPEN_SETTINGS',
    'RUN_COMPLETE_ANALYSIS',
    'RUN_SEQUENCE_ANALYSIS',
    'RUN_SIMILARITY_ANALYSIS',
    'RUN_MUTATION_ANALYSIS',
    'RUN_CLASSIFICATION',
    'RUN_DISEASE_PREDICTION',
    'RUN_VISUALIZATION',
    'CREATE_DIET_PLAN',
    'GENERATE_REPORT',
    'FIND_HOSPITAL',
    'FIND_DOCTOR',
    'BOOK_APPOINTMENT',
    'CANCEL_APPOINTMENT',
    'LOGOUT',
    'CHANGE_THEME',
    'CHANGE_LANGUAGE',
    'CONFIRM_YES',
    'CONFIRM_NO',
    'CHATBOT_QUERY'
}

I18N_INTENT_RESPONSES = {
    'en': {
        'OPEN_DASHBOARD': "Opening Dashboard...",
        'OPEN_COMPLETE_ANALYSIS': "Opening Complete DNA Analysis module...",
        'OPEN_SIMILARITY': "Opening DNA Similarity Analysis module...",
        'OPEN_MUTATION': "Opening Mutation Analysis module...",
        'OPEN_CLASSIFICATION': "Opening DNA Classification module...",
        'OPEN_DISEASE_PREDICTION': "Opening Disease Prediction module...",
        'OPEN_VISUALIZATION': "Opening DNA Visualization...",
        'OPEN_HEALTH_GUIDANCE': "Opening Health Guide...",
        'OPEN_DIET_PLANNER': "Opening Diet Planner...",
        'OPEN_HOSPITALS': "Opening Hospital Recommendations...",
        'OPEN_APPOINTMENTS': "Opening My Appointments...",
        'OPEN_REPORTS': "Opening Analysis Reports...",
        'OPEN_PROFILE': "Opening your Profile...",
        'OPEN_SETTINGS': "Opening Account Settings...",
        'RUN_COMPLETE_ANALYSIS': "Starting complete DNA analysis on your sequence...",
        'RUN_COMPLETE_ANALYSIS_NEED_SEQ': "Opening Complete Analysis. Please provide your DNA sequence or upload a sequence file to analyze.",
        'RUN_SEQUENCE_ANALYSIS': "Starting sequence processing analysis...",
        'RUN_SIMILARITY_ANALYSIS': "Starting sequence similarity alignment...",
        'RUN_MUTATION_ANALYSIS': "Starting mutation detection analysis...",
        'RUN_CLASSIFICATION': "Starting DNA functional classification...",
        'RUN_DISEASE_PREDICTION': "Starting disease risk prediction...",
        'RUN_VISUALIZATION': "Generating DNA sequence visualization...",
        'CREATE_DIET_PLAN': "Opening Diet Planner in Health Guide...",
        'GENERATE_REPORT': "Opening Reports page to generate your DNA report...",
        'CHANGE_THEME_DARK': "Switching theme to Dark Mode...",
        'CHANGE_THEME_LIGHT': "Switching theme to Light Mode...",
        'CHANGE_LANGUAGE': "Switching website language to {lang_name}...",
        'BOOK_CONFIRM_PROMPT': "I found {doctor} at {hospital}. Would you like me to proceed with booking this appointment?",
        'BOOK_GENERAL_PROMPT': "Would you like me to open the doctor appointment booking page?",
        'CANCEL_CONFIRM_PROMPT': "Are you sure you want to cancel an appointment? I will open your appointments list.",
        'LOGOUT_CONFIRM_PROMPT': "Are you sure you want to log out of DNAura?",
        'CONFIRM_CANCELLED': "Action cancelled.",
        'CONFIRM_EXECUTE': "Proceeding as requested...",
        'UNKNOWN_COMMAND': "Sorry, I couldn't understand that command. Please try again."
    },
    'hi': {
        'OPEN_DASHBOARD': "डैशबोर्ड खोला जा रहा है...",
        'OPEN_COMPLETE_ANALYSIS': "कम्प्लीट डीएनए एनालिसिस खोला जा रहा है...",
        'OPEN_SIMILARITY': "डीएनए सिमिलरिटी एनालिसिस खोला जा रहा है...",
        'OPEN_MUTATION': "म्यूटेशन एनालिसिस पेज खोला जा रहा है...",
        'OPEN_CLASSIFICATION': "डीएनए क्लासिफिकेशन पेज खोला जा रहा है...",
        'OPEN_DISEASE_PREDICTION': "डिसीज प्रेडिक्शन पेज खोला जा रहा है...",
        'OPEN_VISUALIZATION': "डीएनए विज़ुअलाइज़ेशन खोला जा रहा है...",
        'OPEN_HEALTH_GUIDANCE': "स्वास्थ्य मार्गदर्शिका खोली जा रही है...",
        'OPEN_DIET_PLANNER': "डाइट प्लानर खोला जा रहा है...",
        'OPEN_HOSPITALS': "अस्पताल की सिफारिशें खोली जा रही हैं...",
        'OPEN_APPOINTMENTS': "माय अपॉइंटमेंट्स खोला जा रहा है...",
        'OPEN_REPORTS': "रिपोर्ट्स पेज खोला जा रहा है...",
        'OPEN_PROFILE': "आपका प्रोफाइल खोला जा रहा है...",
        'OPEN_SETTINGS': "खाता सेटिंग्स खोली जा रही हैं...",
        'RUN_COMPLETE_ANALYSIS': "आपकी सीक्वेंस पर कम्प्लीट डीएनए एनालिसिस शुरू किया जा रहा है...",
        'RUN_COMPLETE_ANALYSIS_NEED_SEQ': "कम्प्लीट एनालिसिस खोला जा रहा है। विश्लेषण के लिए कृपया अपनी डीएनए सीक्वेंस प्रदान करें।",
        'RUN_SEQUENCE_ANALYSIS': "सीक्वेंस प्रोसेसिंग शुरू की जा रही है...",
        'RUN_SIMILARITY_ANALYSIS': "सीक्वेंस सिमिलरिटी विश्लेषण शुरू किया जा रहा है...",
        'RUN_MUTATION_ANALYSIS': "म्यूटेशन विश्लेषण शुरू किया जा रहा है...",
        'RUN_CLASSIFICATION': "डीएनए क्लासिफिकेशन विश्लेषण शुरू किया जा रहा है...",
        'RUN_DISEASE_PREDICTION': "रोग जोखिम भविष्यवाणी शुरू की जा रही है...",
        'RUN_VISUALIZATION': "डीएनए विज़ुअलाइज़ेशन जनरेट किया जा रहा है...",
        'CREATE_DIET_PLAN': "डाइट प्लानर खोला जा रहा है...",
        'GENERATE_REPORT': "रिपोर्ट पेज खोला जा रहा है...",
        'CHANGE_THEME_DARK': "डार्क मोड चालू किया जा रहा है...",
        'CHANGE_THEME_LIGHT': "लाइट मोड चालू किया जा रहा है...",
        'CHANGE_LANGUAGE': "वेबसाइट की भाषा {lang_name} में बदली जा रही है...",
        'BOOK_CONFIRM_PROMPT': "मुझे {hospital} में {doctor} मिले। क्या आप अपॉइंटमेंट बुकिंग जारी रखना चाहते हैं?",
        'BOOK_GENERAL_PROMPT': "क्या आप अपॉइंटमेंट बुकिंग पेज खोलना चाहते हैं?",
        'CANCEL_CONFIRM_PROMPT': "क्या आप वाकई अपॉइंटमेंट रद्द करना चाहते हैं?",
        'LOGOUT_CONFIRM_PROMPT': "क्या आप वाकई DNAura से लॉग आउट करना चाहते हैं?",
        'CONFIRM_CANCELLED': "कार्रवाई रद्द कर दी गई।",
        'CONFIRM_EXECUTE': "अनुरोध के अनुसार आगे बढ़ रहे हैं...",
        'UNKNOWN_COMMAND': "क्षमा करें, मैं उस कमांड को समझ नहीं सका। कृपया पुनः प्रयास करें।"
    },
    'kn': {
        'OPEN_DASHBOARD': "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_COMPLETE_ANALYSIS': "ಸಂಪೂರ್ಣ ಡಿಎನ್‌ಎ ವಿಶ್ಲೇಷಣೆ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_SIMILARITY': "ಡಿಎನ್‌ಎ ಸಮಾನತೆ ವಿಶ್ಲೇಷಣೆ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_MUTATION': "ಮ್ಯುಟೇಷನ್ ವಿಶ್ಲೇಷಣೆ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_CLASSIFICATION': "ಡಿಎನ್‌ಎ ವರ್ಗೀಕರಣ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_DISEASE_PREDICTION': "ರೋಗ ಮುನ್ಸೂಚನೆ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_VISUALIZATION': "ಡಿಎನ್‌ಎ ವಿಶುವಲೈಸೇಶನ್ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_HEALTH_GUIDANCE': "ಆರೋಗ್ಯ ಮಾರ್ಗದರ್ಶಿ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_DIET_PLANNER': "ಡಯಟ್ ಪ್ಲಾನರ್ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_HOSPITALS': "ಆಸ್ಪತ್ರೆ ಶಿಫಾರಸುಗಳನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_APPOINTMENTS': "ನನ್ನ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್‌ಗಳನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_REPORTS': "ವರದಿಗಳ ಪುಟವನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_PROFILE': "ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'OPEN_SETTINGS': "ಖಾತೆ ಸಂಯೋಜನೆಗಳನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'RUN_COMPLETE_ANALYSIS': "ನಿಮ್ಮ ಡಿಎನ್‌ಎ ಸಂಪೂರ್ಣ ವಿಶ್ಲೇಷಣೆ ಪ್ರಾರಂಭಿಸಲಾಗುತ್ತಿದೆ...",
        'RUN_COMPLETE_ANALYSIS_NEED_SEQ': "ಸಂಪೂರ್ಣ ವಿಶ್ಲೇಷಣೆ ತೆರೆಯಲಾಗುತ್ತಿದೆ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಡಿಎನ್‌ಎ ಸೀಕ್ವೆನ್ಸ್ ಒದಗಿಸಿ.",
        'RUN_SEQUENCE_ANALYSIS': "ಸೀಕ್ವೆನ್ಸ್ ಪ್ರೊಸೆಸಿಂಗ್ ವಿಶ್ಲೇಷಣೆ ಪ್ರಾರಂಭಿಸಲಾಗುತ್ತಿದೆ...",
        'RUN_SIMILARITY_ANALYSIS': "ಸಮಾನತೆ ವಿಶ್ಲೇಷಣೆ ಪ್ರಾರಂಭಿಸಲಾಗುತ್ತಿದೆ...",
        'RUN_MUTATION_ANALYSIS': "ಮ್ಯುಟೇಷನ್ ವಿಶ್ಲೇಷಣೆ ಪ್ರಾರಂಭಿಸಲಾಗುತ್ತಿದೆ...",
        'RUN_CLASSIFICATION': "ಡಿಎನ್‌ಎ ವರ್ಗೀಕರಣ ವಿಶ್ಲೇಷಣೆ ಪ್ರಾರಂಭಿಸಲಾಗುತ್ತಿದೆ...",
        'RUN_DISEASE_PREDICTION': "ರೋಗ ಅಪಾಯದ ಮುನ್ಸೂಚನೆ ಪ್ರಾರಂಭಿಸಲಾಗುತ್ತಿದೆ...",
        'RUN_VISUALIZATION': "ಡಿಎನ್‌ಎ ವಿಶುವಲೈಸೇಶನ್ ಸೃಷ್ಟಿಸಲಾಗುತ್ತಿದೆ...",
        'CREATE_DIET_PLAN': "ಡಯಟ್ ಪ್ಲಾನರ್ ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'GENERATE_REPORT': "ವರದಿಗಳ ಪುಟವನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ...",
        'CHANGE_THEME_DARK': "ಡಾರ್ಕ್ ಮೋಡ್‌ಗೆ ಬದಲಾಯಿಸಲಾಗುತ್ತಿದೆ...",
        'CHANGE_THEME_LIGHT': "ಲೈಟ್ ಮೋಡ್‌ಗೆ ಬದಲಾಯಿಸಲಾಗುತ್ತಿದೆ...",
        'CHANGE_LANGUAGE': "ಭಾಷೆಯನ್ನು {lang_name} ಗೆ ಬದಲಾಯಿಸಲಾಗುತ್ತಿದೆ...",
        'BOOK_CONFIRM_PROMPT': "{hospital} ನಲ್ಲಿ {doctor} ಕಂಡುಬಂದಿದ್ದಾರೆ. ನೀವು ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಬುಕಿಂಗ್ ಮುಂದುವರಿಸಲು ಬಯಸುತ್ತೀರಾ?",
        'BOOK_GENERAL_PROMPT': "ನೀವು ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಬುಕಿಂಗ್ ಪುಟ ತೆರೆಯಲು ಬಯಸುತ್ತೀರಾ?",
        'CANCEL_CONFIRM_PROMPT': "ನೀವು ಖಚಿತವಾಗಿಯೂ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ರದ್ದುಗೊಳಿಸಲು ಬಯಸುತ್ತೀರಾ?",
        'LOGOUT_CONFIRM_PROMPT': "ನೀವು ಖಚಿತವಾಗಿಯೂ DNAura ದಿಂದ ಲಾಗ್‌ಔಟ್ ಮಾಡಲು ಬಯಸುತ್ತೀರಾ?",
        'CONFIRM_CANCELLED': "ಕ್ರಿಯೆಯನ್ನು ರದ್ದುಗೊಳಿಸಲಾಗಿದೆ.",
        'CONFIRM_EXECUTE': "ವಿನಂತಿಸಿದಂತೆ ಮುಂದುವರಿಯಲಾಗುತ್ತಿದೆ...",
        'UNKNOWN_COMMAND': "ಕ್ಷಮಿಸಿ, ಆಜ್ಞೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
    },
    'ta': {
        'OPEN_DASHBOARD': "டாஷ்போர்டு திறக்கப்படுகிறது...",
        'OPEN_COMPLETE_ANALYSIS': "முழுமையான டிஎன்ஏ பகுப்பாய்வு திறக்கப்படுகிறது...",
        'OPEN_SIMILARITY': "டிஎன்ஏ ஒப்பீட்டு பகுப்பாய்வு திறக்கப்படுகிறது...",
        'OPEN_MUTATION': "பிறழ்வு பகுப்பாய்வு திறக்கப்படுகிறது...",
        'OPEN_CLASSIFICATION': "டிஎன்ஏ வகைப்பாடு திறக்கப்படுகிறது...",
        'OPEN_DISEASE_PREDICTION': "நோய் கணிப்பு திறக்கப்படுகிறது...",
        'OPEN_VISUALIZATION': "டிஎன்ஏ காட்சிப்படுத்தல் திறக்கப்படுகிறது...",
        'OPEN_HEALTH_GUIDANCE': "சுகாதார வழிகாட்டி திறக்கப்படுகிறது...",
        'OPEN_DIET_PLANNER': "டயட் பிளானர் திறக்கப்படுகிறது...",
        'OPEN_HOSPITALS': "மருத்துவமனை பரிந்துரைகள் திறக்கப்படுகிறது...",
        'OPEN_APPOINTMENTS': "எனது முன்பதிவுகள் திறக்கப்படுகிறது...",
        'OPEN_REPORTS': "அறிக்கைகள் பக்கம் திறக்கப்படுகிறது...",
        'OPEN_PROFILE': "உங்கள் சுயவிவரம் திறக்கப்படுகிறது...",
        'OPEN_SETTINGS': "கணக்கு அமைப்புகள் திறக்கப்படுகிறது...",
        'RUN_COMPLETE_ANALYSIS': "முழுமையான டிஎன்ஏ பகுப்பாய்வு தொடங்குகிறது...",
        'RUN_COMPLETE_ANALYSIS_NEED_SEQ': "முழுமையான பகுப்பாய்வு திறக்கப்படுகிறது. உங்கள் டிஎன்ஏ வரிசையை வழங்கவும்.",
        'RUN_SEQUENCE_ANALYSIS': "வரிசை செயலாக்க பகுப்பாய்வு தொடங்குகிறது...",
        'RUN_SIMILARITY_ANALYSIS': "வரிசை ஒப்பீட்டு பகுப்பாய்வு தொடங்குகிறது...",
        'RUN_MUTATION_ANALYSIS': "பிறழ்வு பகுப்பாய்வு தொடங்குகிறது...",
        'RUN_CLASSIFICATION': "வகைப்பாட்டு பகுப்பாய்வு தொடங்குகிறது...",
        'RUN_DISEASE_PREDICTION': "நோய் அபாயக் கணிப்பு தொடங்குகிறது...",
        'RUN_VISUALIZATION': "டிஎன்ஏ காட்சிப்படுத்தல் உருவாக்கப்படுகிறது...",
        'CREATE_DIET_PLAN': "டயட் பிளானர் திறக்கப்படுகிறது...",
        'GENERATE_REPORT': "அறிக்கைகள் பக்கம் திறக்கப்படுகிறது...",
        'CHANGE_THEME_DARK': "டார்க் பயன்முறைக்கு மாறுகிறது...",
        'CHANGE_THEME_LIGHT': "லைட் பயன்முறைக்கு மாறுகிறது...",
        'CHANGE_LANGUAGE': "மொழி {lang_name}-க்கு மாற்றப்படுகிறது...",
        'BOOK_CONFIRM_PROMPT': "{hospital}-இல் {doctor} கண்டறியப்பட்டார். முன்பதிவை தொடர விரும்புகிறீர்களா?",
        'BOOK_GENERAL_PROMPT': "முன்பதிவு பக்கத்தைத் திறக்க விரும்புகிறீர்களா?",
        'CANCEL_CONFIRM_PROMPT': "முன்பதிவை நிச்சயமாக ரத்து செய்ய விரும்புகிறீர்களா?",
        'LOGOUT_CONFIRM_PROMPT': "நீங்கள் நிச்சயமாக DNAura-விலிருந்து வெளியேற விரும்புகிறீர்களா?",
        'CONFIRM_CANCELLED': "செயல்பாடு ரத்து செய்யப்பட்டது.",
        'CONFIRM_EXECUTE': "கோரியபடி தொடர்கிறது...",
        'UNKNOWN_COMMAND': "மன்னிக்கவும், அந்த கட்டளையைப் புரிந்து கொள்ள முடியவில்லை. மீண்டும் முயற்சிக்கவும்."
    },
    'te': {
        'OPEN_DASHBOARD': "డాష్‌బోర్డ్ తెరవబడుతోంది...",
        'OPEN_COMPLETE_ANALYSIS': "పూర్తి డీఎన్ఏ విశ్లేషణ తెరవబడుతోంది...",
        'OPEN_SIMILARITY': "డీఎన్ఏ పోలిక విశ్లేషణ తెరవబడుతోంది...",
        'OPEN_MUTATION': "మ్యుటేషన్ విశ్లేషణ తెరవబడుతోంది...",
        'OPEN_CLASSIFICATION': "డీఎన్ఏ వర్గీకరణ తెరవబడుతోంది...",
        'OPEN_DISEASE_PREDICTION': "వ్యాధి అంచనా తెరవబడుతోంది...",
        'OPEN_VISUALIZATION': "డీఎన్ఏ విజువలైజేషన్ తెరవబడుతోంది...",
        'OPEN_HEALTH_GUIDANCE': "ఆరోగ్య మార్గదర్శిని తెరవబడుతోంది...",
        'OPEN_DIET_PLANNER': "డైట్ ప్లానర్ తెరవబడుతోంది...",
        'OPEN_HOSPITALS': "ఆసుపత్రి సిఫార్సులు తెరవబడుతున్నాయి...",
        'OPEN_APPOINTMENTS': "నా అపాయింట్‌మెంట్‌లు తెరవబడుతున్నాయి...",
        'OPEN_REPORTS': "నివేదికల పేజీ తెరవబడుతోంది...",
        'OPEN_PROFILE': "మీ ప్రొఫైల్ తెరవబడుతోంది...",
        'OPEN_SETTINGS': "ఖాతా సెట్టింగ్‌లు తెరవబడుతున్నాయి...",
        'RUN_COMPLETE_ANALYSIS': "పూర్తి డీఎన్ఏ విశ్లేషణ ప్రారంభించబడుతోంది...",
        'RUN_COMPLETE_ANALYSIS_NEED_SEQ': "పూర్తి విశ్లేషణ తెరవబడుతోంది. దయచేసి మీ డీఎన్ఏ క్రమాన్ని అందించండి.",
        'RUN_SEQUENCE_ANALYSIS': "సీక్వెన్స్ ప్రాసెసింగ్ విశ్లేషణ ప్రారంభించబడుతోంది...",
        'RUN_SIMILARITY_ANALYSIS': "పోలిక విశ్లేషణ ప్రారంభించబడుతోంది...",
        'RUN_MUTATION_ANALYSIS': "మ్యుటేషన్ విశ్లేషణ ప్రారంభించబడుతోంది...",
        'RUN_CLASSIFICATION': "వర్గీకరణ విశ్లేషణ ప్రారంభించబడుతోంది...",
        'RUN_DISEASE_PREDICTION': "వ్యాధి ప్రమాద అంచనా ప్రారంభించబడుతోంది...",
        'RUN_VISUALIZATION': "డీఎన్ఏ విజువలైజేషన్ రూపొందించబడుతోంది...",
        'CREATE_DIET_PLAN': "డైట్ ప్లానర్ తెరవబడుతోంది...",
        'GENERATE_REPORT': "నివేదికల పేజీ తెరవబడుతోంది...",
        'CHANGE_THEME_DARK': "డార్క్ మోడ్‌కి మారుతోంది...",
        'CHANGE_THEME_LIGHT': "లైట్ మోడ్‌కి మారుతోంది...",
        'CHANGE_LANGUAGE': "భాషను {lang_name} కు మారుస్తోంది...",
        'BOOK_CONFIRM_PROMPT': "{hospital} లో {doctor} లభించారు. మీరు అపాయింట్‌మెంట్ బుకింగ్ కొనసాగించాలనుకుంటున్నారా?",
        'BOOK_GENERAL_PROMPT': "మీరు అపాయింట్‌మెంట్ బుకింగ్ పేజీని తెరవాలనుకుంటున్నారా?",
        'CANCEL_CONFIRM_PROMPT': "మీరు ఖచ్చితంగా అపాయింట్‌మెంట్‌ను రద్దు చేయాలనుకుంటున్నారా?",
        'LOGOUT_CONFIRM_PROMPT': "మీరు ఖచ్చితంగా DNAura నుండి లాగ్ అవుట్ అవ్వాలనుకుంటున్నారా?",
        'CONFIRM_CANCELLED': "చర్య రద్దు చేయబడింది.",
        'CONFIRM_EXECUTE': "అభ్యర్థించిన విధంగా ముందుకు సాగుతోంది...",
        'UNKNOWN_COMMAND': "క్షమించండి, ఆ ఆదేశాన్ని అర్థం చేసుకోలేకపోయాను. దయచేసి మళ్లీ ప్రయత్నించండి."
    }
}


def get_i18n_msg(key: str, lang: str = 'en', **kwargs) -> str:
    lang_dict = I18N_INTENT_RESPONSES.get(lang, I18N_INTENT_RESPONSES['en'])
    msg_template = lang_dict.get(key, I18N_INTENT_RESPONSES['en'].get(key, 'Processing command...'))
    if kwargs:
        try:
            return msg_template.format(**kwargs)
        except Exception:
            return msg_template
    return msg_template


def _match_deterministic_rules(msg_lower: str) -> Optional[str]:
    """Pattern matching across English, Hindi, Kannada, Tamil, Telugu."""
    
    # 1. Confirmations (Using exact word boundaries for English and Indic keywords to prevent substring mismatches)
    has_english_yes = bool(re.search(r'\b(?:yes|confirm|proceed|sure|ok|okay)\b', msg_lower))
    has_indic_yes = bool(re.search(r'(?:\s|^)(?:हाँ|हां|हೌದು|ஆம்|அవును)(?:\s|$)', msg_lower))
    
    has_english_no = bool(re.search(r'\b(?:no|cancel|stop|abort)\b', msg_lower))
    has_indic_no = bool(re.search(r'(?:\s|^)(?:ना|नहीं|नहि|रद्द|ಬೇಡ|ರದ್ದು|இல்லை|ரத்து|వద్దు|రద్దు)(?:\s|$)', msg_lower))

    if (has_english_yes or has_indic_yes) and not (has_english_no or has_indic_no):
        return 'CONFIRM_YES'
    if has_english_no or has_indic_no:
        if not ('appointment' in msg_lower or 'अपॉइंटमेंट' in msg_lower or 'ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್' in msg_lower):
            return 'CONFIRM_NO'

    # 2. Sensitive Actions (Confirmation Required)
    if any(w in msg_lower for w in ['logout', 'log out', 'logoff', 'sign out', 'लॉग आउट', 'ಲಾಗ್‌ಔಟ್', 'வெளியேறு', 'లాగ్ అవుట్']):
        return 'LOGOUT'
    if any(w in msg_lower for w in ['cancel appointment', 'cancel my appointment', 'अपॉइंटमेंट रद्द', 'ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ರದ್ದು']):
        return 'CANCEL_APPOINTMENT'
    if re.search(r'\b(?:book|schedule|make)\s+(?:an?\s+)?appointment\b', msg_lower) or 'बुकिंग' in msg_lower or 'ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಬುಕ್' in msg_lower:
        return 'BOOK_APPOINTMENT'

    # 3. Theme & Language Controls
    if any(w in msg_lower for w in ['dark mode', 'dark theme', 'enable dark', 'switch to dark', 'डार्क मोड', 'ಡಾರ್ಕ್ ಮೋಡ್', 'டார்க்', 'డార్క్']):
        return 'CHANGE_THEME'
    if any(w in msg_lower for w in ['light mode', 'light theme', 'enable light', 'switch to light', 'लाइट मोड', 'ಲೈಟ್ ಮೋಡ್', 'லைட்', 'లైట్']):
        return 'CHANGE_THEME'
    if any(w in msg_lower for w in ['change language', 'switch language', 'set language', 'भाषा बदलो', 'ಭಾಷೆ ಬದಲಾಯಿಸಿ', 'மொழியை மாற்று', 'భాష మార్చండి']):
        return 'CHANGE_LANGUAGE'
    if any(lang_kw in msg_lower for lang_kw in ['hindi', 'kannada', 'tamil', 'telugu', 'english', 'हिंदी', 'कन्नड़', 'तमिल', 'तेलगू', 'ಕನ್ನಡ', 'ಹಿಂದಿ', 'ತಮಿಳು', 'ತೆಲುಗು']):
        if 'language' in msg_lower or 'भाषा' in msg_lower or 'ಭಾಷೆ' in msg_lower or 'மொழி' in msg_lower or 'భాష' in msg_lower:
            return 'CHANGE_LANGUAGE'

    # 4. User Account & Settings
    if any(w in msg_lower for w in ['open profile', 'my profile', 'show profile', 'प्रोफाइल', 'ಪ್ರೊಫೈಲ್', 'சுயவிவரம்', 'ప్రొఫైల్']):
        return 'OPEN_PROFILE'
    if any(w in msg_lower for w in ['open settings', 'account settings', 'settings', 'सेटिंग्स', 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', 'அமைப்புகள்', 'సెట్టింగ్‌లు']):
        return 'OPEN_SETTINGS'

    # 5. Analysis Runner Actions
    if any(w in msg_lower for w in ['perform complete', 'run complete analysis', 'analyze my dna', 'start complete analysis', 'do complete analysis', 'कम्प्लीट एनालिसिस करो', 'डीएनए विश्लेषण करो', 'ನನ್ನ ಡಿಎನ್ಎ ವಿಶ್ಲೇಷಿಸಿ', 'டிஎன்ஏ பகுப்பாய்வு செய்', 'నా డీఎన్ఏ విశ్లేషించండి']):
        return 'RUN_COMPLETE_ANALYSIS'
    if any(w in msg_lower for w in ['run sequence analysis', 'analyze sequence', 'calculate gc content', 'सीक्वेंस एनालिसिस करो']):
        return 'RUN_SEQUENCE_ANALYSIS'
    if any(w in msg_lower for w in ['compare dna', 'run similarity analysis', 'compare these dna sequences', 'डीएनए तुलना करो']):
        return 'RUN_SIMILARITY_ANALYSIS'
    if any(w in msg_lower for w in ['check mutations', 'run mutation analysis', 'म्यूटेशन चेक करो']):
        return 'RUN_MUTATION_ANALYSIS'
    if any(w in msg_lower for w in ['classify dna', 'run classification', 'डीएनए क्लासिफाई करो']):
        return 'RUN_CLASSIFICATION'
    if any(w in msg_lower for w in ['check disease risk', 'predict disease risk', 'perform disease prediction']):
        return 'RUN_DISEASE_PREDICTION'
    if any(w in msg_lower for w in ['visualize dna', 'create dna visualization', 'generate visualization']):
        return 'RUN_VISUALIZATION'

    # 6. Additional Action Commands
    if any(w in msg_lower for w in ['create a diet plan', 'make a diet plan', 'make diet plan', 'i want a diet plan', 'डाइट प्लान बनाओ', 'ಡಯಟ್ ಪ್ಲಾನ್ ಮಾಡಿ']):
        return 'CREATE_DIET_PLAN'
    if any(w in msg_lower for w in ['generate my report', 'generate report', 'download report', 'रिपोर्ट बनाओ', 'ವರದಿ ತಯಾರಿಸಿ']):
        return 'GENERATE_REPORT'

    # 7. Navigation Commands
    if any(w in msg_lower for w in ['open dashboard', 'go to dashboard', 'show dashboard', 'डैशबोर्ड', 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', 'டாஷ்போர்ட்', 'డాష్‌బోర్డ్']):
        return 'OPEN_DASHBOARD'

    if any(kw in msg_lower for kw in ['complete analysis', 'complete dna analysis', 'कम्प्लीट एनालिसिस', 'कम्प्लीट', 'ಸಂಪೂರ್ಣ ವಿಶ್ಲೇಷಣೆ', 'ಕಂಪ್ಲೀಟ್', 'ಅನಾಲಿಸಿಸ್', 'முழுமையான பகுப்பாய்வு', 'కంప్లీట్ అనాలసిస్']):
        return 'OPEN_COMPLETE_ANALYSIS'

    if any(kw in msg_lower for kw in ['similarity', 'compare dna', 'sequence alignment', 'समानता', 'ಸಿಮಿಲರಿಟಿ', 'ஒப்பீட்டு', 'పోలిక']):
        return 'OPEN_SIMILARITY'

    if any(kw in msg_lower for kw in ['mutation', 'check mutations', 'म्यूटेशन', 'उत्परिवर्तन', 'ಮ್ಯುಟೇಷನ್', 'பிறழ்வு', 'మ్యుటేషన్']):
        return 'OPEN_MUTATION'

    if any(kw in msg_lower for kw in ['classification', 'classify dna', 'वर्गीकरण', 'ವರ್ಗೀಕರಣ', 'வகைப்பாடு', 'వర్గీకరణ']):
        return 'OPEN_CLASSIFICATION'

    if any(kw in msg_lower for kw in ['disease prediction', 'disease risk', 'रोग भविष्यवाणी', 'ರೋಗ ಮುನ್ಸೂಚನೆ', 'நோய் கணிப்பு', 'వ్యాధి అంచనా']):
        return 'OPEN_DISEASE_PREDICTION'

    if any(kw in msg_lower for kw in ['visualization', 'visualize dna', 'विज़ुअलाइज़ेशन', 'ವಿಶುವಲೈಸೇಶನ್', 'காட்சிப்படுத்தல்', 'విజువలైజేషన్']):
        return 'OPEN_VISUALIZATION'

    if any(kw in msg_lower for kw in ['diet planner', 'diet plan', 'डाइट प्लानर', 'ಆಹಾರ ಯೋಜನೆ']):
        return 'OPEN_DIET_PLANNER'

    if any(kw in msg_lower for kw in ['health guide', 'health guidance', 'स्वास्थ्य मार्गदर्शिका', 'ಆರೋಗ್ಯ ಮಾರ್ಗದರ್ಶಿ', 'சுகாதார வழிகாட்டி', 'ఆరోగ్య మార్గదర్శిని']):
        return 'OPEN_HEALTH_GUIDANCE'

    if any(kw in msg_lower for kw in ['my appointments', 'show appointments', 'check appointments', 'मेरे अपॉइंटमेंट', 'ನನ್ನ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್', 'எனது முன்பதிவுகள்', 'నా అపాయింట్‌మెంట్‌లు']):
        return 'OPEN_APPOINTMENTS'

    if any(kw in msg_lower for kw in ['reports', 'my reports', 'रिपोर्ट्स', 'ವರದಿಗಳು', 'அறிக்கைகள்', 'నివేదికలు']):
        return 'OPEN_REPORTS'

    # Check if recommendation query (Hospital / Doctor)
    rec_entities = extract_intent_and_entities(msg_lower)
    if rec_entities.get('is_recommendation'):
        if rec_entities.get('doctor_name_query') or rec_entities.get('specialty') or 'doctor' in msg_lower or 'डॉक्टर' in msg_lower or 'ವೈದ್ಯರು' in msg_lower:
            return 'FIND_DOCTOR'
        return 'FIND_HOSPITAL'

    if any(kw in msg_lower for kw in ['hospitals', 'hospital', 'अस्पताल', 'ಆಸ್ಪತ್ರೆ', 'மருத்துவமனை', 'ఆసుపత్రి']):
        return 'OPEN_HOSPITALS'

    return None


def process_voice_assistant_command(
    message: str,
    current_page: str = "",
    language: str = "en",
    user_location: Optional[Dict[str, float]] = None,
    user_info: Optional[Dict[str, Any]] = None,
    conversation: Optional[list] = None,
    pending_action: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main Voice Assistant Intent Controller.
    Parses intent, enforces security whitelist, returns structured action response.
    """
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()
    lang = language if language in I18N_INTENT_RESPONSES else 'en'

    # Check pending confirmation action if user said yes/no
    matched_intent = _match_deterministic_rules(msg_lower)

    if pending_action and matched_intent in ['CONFIRM_YES', 'CONFIRM_NO']:
        if matched_intent == 'CONFIRM_YES':
            exec_url = pending_action.get('navigate_url')
            action_type = pending_action.get('action', 'NAVIGATE')
            return {
                'response': get_i18n_msg('CONFIRM_EXECUTE', lang=lang),
                'intent': 'CONFIRM_YES',
                'action': action_type,
                'navigate_url': exec_url,
                'requires_confirmation': False,
                'language': lang
            }
        else:
            return {
                'response': get_i18n_msg('CONFIRM_CANCELLED', lang=lang),
                'intent': 'CONFIRM_NO',
                'action': 'NONE',
                'navigate_url': None,
                'requires_confirmation': False,
                'language': lang
            }

    # Fallback to LLM if rule matching was inconclusive and message looks like dynamic command
    if not matched_intent:
        try:
            matched_intent = _llm_intent_classifier(msg_clean, lang)
        except Exception:
            matched_intent = 'CHATBOT_QUERY'

    if matched_intent not in ALLOWED_INTENTS:
        matched_intent = 'CHATBOT_QUERY'

    # -------------------------------------------------------------
    # CONTROLLED INTENT EXECUTION SWITCH
    # -------------------------------------------------------------
    
    # THEME & LANGUAGE INTENTS
    if matched_intent == 'CHANGE_THEME':
        target_theme = 'dark' if any(w in msg_lower for w in ['dark', 'डार्क', 'ಡಾರ್ಕ್', 'டார்க்', 'డార్క్']) else 'light'
        msg_key = 'CHANGE_THEME_DARK' if target_theme == 'dark' else 'CHANGE_THEME_LIGHT'
        return {
            'response': get_i18n_msg(msg_key, lang=lang),
            'intent': matched_intent,
            'action': 'CHANGE_THEME',
            'theme': target_theme,
            'language': lang
        }

    elif matched_intent == 'CHANGE_LANGUAGE':
        target_lang = 'en'
        lang_names = {'en': 'English', 'hi': 'Hindi', 'kn': 'Kannada', 'ta': 'Tamil', 'te': 'Telugu'}
        if 'hi' in msg_lower or 'hindi' in msg_lower or 'हिंदी' in msg_lower or 'ಹಿಂದಿ' in msg_lower:
            target_lang = 'hi'
        elif 'kn' in msg_lower or 'kannada' in msg_lower or 'कन्नड़' in msg_lower or 'ಕನ್ನಡ' in msg_lower:
            target_lang = 'kn'
        elif 'ta' in msg_lower or 'tamil' in msg_lower or 'तमिल' in msg_lower or 'ತಮಿಳು' in msg_lower:
            target_lang = 'ta'
        elif 'te' in msg_lower or 'telugu' in msg_lower or 'तेलगू' in msg_lower or 'ತೆಲುಗು' in msg_lower:
            target_lang = 'te'
        
        return {
            'response': get_i18n_msg('CHANGE_LANGUAGE', lang=lang, lang_name=lang_names.get(target_lang, 'English')),
            'intent': matched_intent,
            'action': 'CHANGE_LANGUAGE',
            'target_language': target_lang,
            'language': target_lang
        }

    # ACCOUNT / PROFILE / SETTINGS INTENTS
    elif matched_intent in ['OPEN_PROFILE', 'OPEN_SETTINGS']:
        return {
            'response': get_i18n_msg('OPEN_PROFILE' if matched_intent == 'OPEN_PROFILE' else 'OPEN_SETTINGS', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/auth/profile',
            'language': lang
        }

    # NAVIGATION INTENTS
    elif matched_intent == 'OPEN_DASHBOARD':
        return {
            'response': get_i18n_msg('OPEN_DASHBOARD', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/dashboard/',
            'language': lang
        }

    elif matched_intent == 'OPEN_COMPLETE_ANALYSIS':
        return {
            'response': get_i18n_msg('OPEN_COMPLETE_ANALYSIS', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/analysis/complete/',
            'language': lang
        }

    elif matched_intent == 'OPEN_SIMILARITY':
        return {
            'response': get_i18n_msg('OPEN_SIMILARITY', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/analysis/similarity/',
            'language': lang
        }

    elif matched_intent == 'OPEN_MUTATION':
        return {
            'response': get_i18n_msg('OPEN_MUTATION', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/analysis/mutation/',
            'language': lang
        }

    elif matched_intent == 'OPEN_CLASSIFICATION':
        return {
            'response': get_i18n_msg('OPEN_CLASSIFICATION', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/analysis/sequence/',
            'language': lang
        }

    elif matched_intent == 'OPEN_DISEASE_PREDICTION':
        return {
            'response': get_i18n_msg('OPEN_DISEASE_PREDICTION', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/analysis/complete/',
            'language': lang
        }

    elif matched_intent == 'OPEN_VISUALIZATION':
        return {
            'response': get_i18n_msg('OPEN_VISUALIZATION', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/analysis/complete/',
            'language': lang
        }

    elif matched_intent == 'OPEN_HEALTH_GUIDANCE':
        return {
            'response': get_i18n_msg('OPEN_HEALTH_GUIDANCE', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/health-guidance/',
            'language': lang
        }

    elif matched_intent == 'OPEN_DIET_PLANNER':
        return {
            'response': get_i18n_msg('OPEN_DIET_PLANNER', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/health-guidance/',
            'language': lang
        }

    elif matched_intent == 'OPEN_HOSPITALS':
        return {
            'response': get_i18n_msg('OPEN_HOSPITALS', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/hospitals/',
            'language': lang
        }

    elif matched_intent == 'OPEN_APPOINTMENTS':
        return {
            'response': get_i18n_msg('OPEN_APPOINTMENTS', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/appointments/my-appointments',
            'language': lang
        }

    elif matched_intent == 'OPEN_REPORTS':
        return {
            'response': get_i18n_msg('OPEN_REPORTS', lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': '/reports/',
            'language': lang
        }

    # ACTION INTENTS
    elif matched_intent in ['RUN_COMPLETE_ANALYSIS', 'RUN_DISEASE_PREDICTION', 'RUN_VISUALIZATION']:
        if '/analysis/complete' in current_page:
            return {
                'response': get_i18n_msg('RUN_COMPLETE_ANALYSIS', lang=lang),
                'intent': matched_intent,
                'action': 'RUN_PAGE_ANALYSIS',
                'navigate_url': None,
                'language': lang
            }
        else:
            return {
                'response': get_i18n_msg('RUN_COMPLETE_ANALYSIS_NEED_SEQ', lang=lang),
                'intent': matched_intent,
                'action': 'NAVIGATE',
                'navigate_url': '/analysis/complete/',
                'language': lang
            }

    elif matched_intent in ['RUN_SEQUENCE_ANALYSIS', 'RUN_CLASSIFICATION']:
        if '/analysis/sequence' in current_page:
            return {
                'response': get_i18n_msg('RUN_SEQUENCE_ANALYSIS', lang=lang),
                'intent': matched_intent,
                'action': 'RUN_PAGE_ANALYSIS',
                'navigate_url': None,
                'language': lang
            }
        else:
            return {
                'response': get_i18n_msg('RUN_SEQUENCE_ANALYSIS', lang=lang),
                'intent': matched_intent,
                'action': 'NAVIGATE',
                'navigate_url': '/analysis/sequence/',
                'language': lang
            }

    elif matched_intent == 'RUN_SIMILARITY_ANALYSIS':
        if '/analysis/similarity' in current_page:
            return {
                'response': get_i18n_msg('RUN_SIMILARITY_ANALYSIS', lang=lang),
                'intent': matched_intent,
                'action': 'RUN_PAGE_ANALYSIS',
                'navigate_url': None,
                'language': lang
            }
        else:
            return {
                'response': get_i18n_msg('RUN_SIMILARITY_ANALYSIS', lang=lang),
                'intent': matched_intent,
                'action': 'NAVIGATE',
                'navigate_url': '/analysis/similarity/',
                'language': lang
            }

    elif matched_intent == 'RUN_MUTATION_ANALYSIS':
        if '/analysis/mutation' in current_page:
            return {
                'response': get_i18n_msg('RUN_MUTATION_ANALYSIS', lang=lang),
                'intent': matched_intent,
                'action': 'RUN_PAGE_ANALYSIS',
                'navigate_url': None,
                'language': lang
            }
        else:
            return {
                'response': get_i18n_msg('RUN_MUTATION_ANALYSIS', lang=lang),
                'intent': matched_intent,
                'action': 'NAVIGATE',
                'navigate_url': '/analysis/mutation/',
                'language': lang
            }

    elif matched_intent in ['CREATE_DIET_PLAN', 'GENERATE_REPORT']:
        target_url = '/health-guidance/' if matched_intent == 'CREATE_DIET_PLAN' else '/reports/'
        msg_key = 'CREATE_DIET_PLAN' if matched_intent == 'CREATE_DIET_PLAN' else 'GENERATE_REPORT'
        return {
            'response': get_i18n_msg(msg_key, lang=lang),
            'intent': matched_intent,
            'action': 'NAVIGATE',
            'navigate_url': target_url,
            'language': lang
        }

    # RECOMMENDATION INTENTS (HOSPITALS & DOCTORS)
    elif matched_intent in ['FIND_HOSPITAL', 'FIND_DOCTOR']:
        rec_res = get_ai_recommendation(
            message=msg_clean,
            language=lang,
            user_location=user_location,
            user_info=user_info
        )
        if rec_res:
            return {
                'response': rec_res['response'],
                'intent': matched_intent,
                'action': 'SHOW_RECOMMENDATION',
                'navigate_url': None,
                'language': lang
            }

    # CONFIRMATION SENSITIVE ACTIONS
    elif matched_intent == 'BOOK_APPOINTMENT':
        rec_ent = extract_intent_and_entities(msg_clean)
        doc_q = rec_ent.get('doctor_name_query')
        hosp_q = rec_ent.get('hospital_name_query')
        
        prompt_text = get_i18n_msg('BOOK_GENERAL_PROMPT', lang=lang)
        book_url = '/hospitals/'
        if doc_q or hosp_q:
            prompt_text = get_i18n_msg('BOOK_CONFIRM_PROMPT', lang=lang, doctor=doc_q or 'the specialist', hospital=hosp_q or 'the recommended hospital')
            book_url = '/hospitals/'

        return {
            'response': prompt_text,
            'intent': matched_intent,
            'action': 'ASK_CONFIRMATION',
            'pending_action': {
                'action': 'NAVIGATE',
                'navigate_url': book_url
            },
            'requires_confirmation': True,
            'language': lang
        }

    elif matched_intent == 'CANCEL_APPOINTMENT':
        return {
            'response': get_i18n_msg('CANCEL_CONFIRM_PROMPT', lang=lang),
            'intent': matched_intent,
            'action': 'ASK_CONFIRMATION',
            'pending_action': {
                'action': 'NAVIGATE',
                'navigate_url': '/appointments/my-appointments'
            },
            'requires_confirmation': True,
            'language': lang
        }

    elif matched_intent == 'LOGOUT':
        return {
            'response': get_i18n_msg('LOGOUT_CONFIRM_PROMPT', lang=lang),
            'intent': matched_intent,
            'action': 'ASK_CONFIRMATION',
            'pending_action': {
                'action': 'NAVIGATE',
                'navigate_url': '/auth/logout'
            },
            'requires_confirmation': True,
            'language': lang
        }

    # CHATBOT QUERY FALLBACK
    try:
        cb_res = get_chatbot_response(
            user_message=msg_clean,
            current_page=current_page,
            language=lang,
            conversation=conversation or []
        )
        return {
            'response': cb_res['response'],
            'intent': 'CHATBOT_QUERY',
            'action': 'CHATBOT',
            'navigate_url': None,
            'language': lang
        }
    except ChatbotServiceError as exc:
        return {
            'response': str(exc),
            'intent': 'CHATBOT_QUERY',
            'action': 'ERROR',
            'navigate_url': None,
            'language': lang
        }


def _llm_intent_classifier(message: str, language: str) -> str:
    """Uses local Ollama to classify user intent into whitelist if rules were ambiguous."""
    system_prompt = (
        "You are an intent classifier for DNAura Website Voice Assistant. "
        "Classify the user utterance into exactly ONE of these intents:\n"
        "OPEN_DASHBOARD, OPEN_COMPLETE_ANALYSIS, OPEN_SIMILARITY, OPEN_MUTATION, OPEN_CLASSIFICATION, "
        "OPEN_DISEASE_PREDICTION, OPEN_VISUALIZATION, OPEN_HEALTH_GUIDANCE, OPEN_DIET_PLANNER, "
        "OPEN_HOSPITALS, OPEN_APPOINTMENTS, OPEN_REPORTS, RUN_COMPLETE_ANALYSIS, CREATE_DIET_PLAN, "
        "GENERATE_REPORT, FIND_HOSPITAL, FIND_DOCTOR, BOOK_APPOINTMENT, CANCEL_APPOINTMENT, LOGOUT, CHATBOT_QUERY.\n"
        "Output ONLY the intent string without markdown, commentary or punctuation."
    )
    from flask import current_app
    model = current_app.config.get("OLLAMA_MODEL", "llama3.2")
    base_url = current_app.config.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    resp = _call_ollama(
        message=message,
        language=language,
        conversation=[],
        model=model,
        base_url=base_url
    )
    cleaned = resp.strip().upper().replace('"', '').replace("'", '')
    for intent in ALLOWED_INTENTS:
        if intent in cleaned:
            return intent
    return 'CHATBOT_QUERY'
