import os
import json
import logging
import urllib.request
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

HEALTH_DISCLAIMER = "This information is provided for general educational and wellness purposes only and is not a medical diagnosis, prescription, or substitute for professional medical advice. If you describe an urgent situation, please seek immediate help from local emergency services or a qualified healthcare professional."

def generate_health_guidance(problem: str, language: str = 'en') -> Dict[str, Any]:
    """
    Generates structured wellness guidance in English, Hindi, Kannada, Telugu, or Tamil.
    Uses local Ollama AI by default, falling back to structured domain engine.
    """
    problem_clean = problem.strip()
    if not problem_clean:
        return _get_default_guidance(language)

    try:
        guidance = _call_ollama_health_guidance(problem_clean, language)
        if guidance:
            return guidance
    except Exception as e:
        logger.error(f"Local Ollama Health Guidance error: {e}")

    # Domain Knowledge Health Engine Fallback
    return _generate_structured_domain_guidance(problem_clean, language)


def _call_ollama_health_guidance(problem: str, language: str) -> Optional[Dict[str, Any]]:
    system_prompt = f"""
    You are an expert AI Wellness Advisor. Provide GENERAL WELLNESS GUIDANCE for the reported problem in {language}.
    You MUST output valid JSON matching this exact structure:
    {{
      "title": "Wellness Guidance Summary",
      "general_wellness": "General wellness explanation",
      "healthy_foods": ["Food 1", "Food 2", "Food 3"],
      "diet_considerations": ["Diet tip 1", "Diet tip 2"],
      "exercise_suggestions": ["Exercise 1", "Exercise 2"],
      "lifestyle_recommendations": ["Lifestyle tip 1", "Lifestyle tip 2"],
      "medical_disclaimer": "{HEALTH_DISCLAIMER}"
    }}
    Do NOT diagnose, prescribe, or claim medical conditions. Respond strictly in {language}.
    """
    
    url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": "llama3.2",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Health Problem: {problem}"}
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        text = res_data.get("message", {}).get("content", "")
        return json.loads(text)


def _generate_structured_domain_guidance(problem: str, lang: str) -> Dict[str, Any]:
    p = problem.lower()

    if lang == 'hi':
        return {
            "title": f"'{problem}' के लिए स्वास्थ्य एवं पोषण मार्गदर्शन",
            "general_wellness": "पर्याप्त पोषण, नियमित शारीरिक गतिविधि और तनाव प्रबंधन समग्र ऊर्जा को बनाए रखने के लिए आवश्यक हैं।",
            "healthy_foods": [
                "हरी पत्तेदार सब्जियां (पालक, मेथी)",
                "ताजे मौसमी फल (सेब, केला, अनार)",
                "अंकुरित अनाज और दालें",
                "सूखे मेवे (बादाम, अखरोट)"
            ],
            "diet_considerations": [
                "प्रतिदिन 8-10 गिलास पानी पीकर हाइड्रेटेड रहें",
                "अधिक चीनी और प्रसंस्कृत खाद्य पदार्थों से बचें",
                "संतुलित आहार में प्रोटीन और फाइबर शामिल करें"
            ],
            "exercise_suggestions": [
                "रोजाना 30 मिनट तेज चाल (Walking)",
                "हल्का योगाभ्यास और प्राणायाम",
                "स्ट्रेचिंग और कार्डियो एक्सरसाइज"
            ],
            "lifestyle_recommendations": [
                "प्रतिदिन 7-8 घंटे की गुणवत्तापूर्ण नींद लें",
                "नियमित समय पर भोजन करें",
                "स्क्रीन टाइम घटाएं और तनाव मुक्त रहें"
            ],
            "medical_disclaimer": HEALTH_DISCLAIMER
        }
    elif lang == 'kn':
        return {
            "title": f"'{problem}' ಗಾಗಿ ಆರೋಗ್ಯ ಮತ್ತು ಜೀವನಶೈಲಿ ಮಾರ್ಗದರ್ಶನ",
            "general_wellness": "ಉತ್ತಮ ಪೋಷಕಾಂಶಯುಕ್ತ ಆಹಾರ, ನಿಯಮಿತ ವ್ಯಾಯಾಮ ಮತ್ತು ಸರಿಯಾದ ವಿಶ್ರಾಂತಿ ನಿಮ್ಮ ಶಕ್ತಿಯನ್ನು ಹೆಚ್ಚಿಸಲು ಸಹಕಾರಿ.",
            "healthy_foods": [
                "ಹಸಿರು ಸೊಪ್ಪು ತರಕಾರಿಗಳು",
                "ತಾಜಾ ಹಣ್ಣುಗಳು (ಸೇಬು, ಬಾಳೆಹಣ್ಣು)",
                "ಕಾಳುಗಳು ಮತ್ತು ಧಾನ್ಯಗಳು",
                "ಬಾದಾಮಿ ಮತ್ತು ಒಣ ಹಣ್ಣುಗಳು"
            ],
            "diet_considerations": [
                "ದಿನಕ್ಕೆ ಕನಿಷ್ಠ 2.5 ರಿಂದ 3 ಲೀಟರ್ ನೀರು ಕುಡಿಯಿರಿ",
                "ಸಂಸ್ಕರಿಸಿದ ಆಹಾರ ಮತ್ತು ಸಕ್ಕರೆಯನ್ನು ಕಡಿಮೆ ಮಾಡಿ",
                "ಪ್ರೋಟೀನ್ ಭರಿತ ಆಹಾರವನ್ನು ಸೇವಿಸಿ"
            ],
            "exercise_suggestions": [
                "ದಿನವೂ 30 ನಿಮಿಷಗಳ ಕಾಲ ನಡಿಗೆ",
                "ಯೋಗ ಮತ್ತು ಪ್ರಾಣಾಯಾಮ",
                "ಸರಳ ದೇಹದಂಡನೆ ವ್ಯಾಯಾಮಗಳು"
            ],
            "lifestyle_recommendations": [
                "ದಿನಕ್ಕೆ 7-8 ಗಂಟೆಗಳ ಕಾಲ ನಿದ್ರೆ ಮಾಡಿ",
                "ಸಮಯಕ್ಕೆ ಸರಿಯಾಗಿ ಆಹಾರ ಸೇವಿಸಿ",
                "ಮಾನಸಿಕ ಒತ್ತಡವನ್ನು ಕಡಿಮೆ ಮಾಡಿಕೊಳ್ಳಿ"
            ],
            "medical_disclaimer": HEALTH_DISCLAIMER
        }
    elif lang == 'te':
        return {
            "title": f"'{problem}' కోసం ఆరోగ్యం మరియు జీవనశైలి మార్గదర్శకత్వం",
            "general_wellness": "మంచి పోషకాహారం, క్రమబద్ధమైన వ్యాయామం మరియు సరైన విశ్రాంతి మీ శక్తిని పెంచడానికి సహాయపడతాయి.",
            "healthy_foods": [
                "ఆకుకూరలు మరియు తాజా కూరగాయలు",
                "తాజా పండ్లు (యాపిల్స్, అరటిపండ్లు)",
                "పప్పు ధాన్యాలు మరియు మొలకలు",
                "బాదం మరియు డ్రై ఫ్రూట్స్"
            ],
            "diet_considerations": [
                "రోజుకు 2.5 నుండి 3 లీటర్ల నీరు త్రాగండి",
                "ప్రాసెస్ చేసిన ఆహారాలు మరియు చక్కెరను తగ్గించండి",
                "ప్రోటీన్ సమృద్ధిగా ఉన్న ఆహారాన్ని తీసుకోండి"
            ],
            "exercise_suggestions": [
                "రోజువారీ 30 నిమిషాల వేగవంతమైన నడక",
                "యోగా మరియు ప్రాణాయామం",
                "సాధారణ వ్యాయామాలు"
            ],
            "lifestyle_recommendations": [
                "రోజుకు 7-8 గంటల నాణ్యమైన నిద్ర పొందండి",
                "సమయానికి ఆహారం తీసుకోండి",
                "మానసిక ఒత్తిడిని తగ్గించుకోండి"
            ],
            "medical_disclaimer": HEALTH_DISCLAIMER
        }
    elif lang == 'ta':
        return {
            "title": f"'{problem}' க்கான சுகாதாரம் மற்றும் வாழ்க்கை முறை வழிகாட்டுதல்",
            "general_wellness": "நல்ல ஊட்டச்சத்து உணவு, வழக்கமான உடற்பயிற்சி மற்றும் சரியான ஓய்வு உங்கள் ஆற்றலை அதிகரிக்க உதவும்.",
            "healthy_foods": [
                "பச்சை காய்கறிகள் மற்றும் கீரைகள்",
                "புதிய பழங்கள் (ஆப்பிள், வாழைப்பழம்)",
                "பருப்பு வகைகள் மற்றும் தானியங்கள்",
                "பாதாம் மற்றும் உலர்ந்த பழங்கள்"
            ],
            "diet_considerations": [
                "நாளைக்கு 2.5 முதல் 3 லிட்டர் தண்ணீர் குடிக்கவும்",
                "பதப்படுத்தப்பட்ட உணவுகள் மற்றும் சர்க்கரையை குறைக்கவும்",
                "புரதம் நிறைந்த உணவை உட்கொள்ளுங்கள்"
            ],
            "exercise_suggestions": [
                "தினசரி 30 நிமிடங்கள் விறுவிறுப்பான நடைபயிற்சி",
                "யோகா மற்றும் பிராணாயாமம்",
                "எளிய உடற்பயிற்சிகள்"
            ],
            "lifestyle_recommendations": [
                "நாளைக்கு 7-8 மணிநேரம் தரமான தூக்கம் பெறவும்",
                "நேரத்திற்கு உணவு உண்ணுங்கள்",
                "மன அழுத்தத்தைக் குறைக்கவும்"
            ],
            "medical_disclaimer": HEALTH_DISCLAIMER
        }
    else: # English default
        return {
            "title": f"Wellness & Health Guidance for '{problem}'",
            "general_wellness": "Maintaining optimal wellness involves balanced nutrition, regular physical movement, hydration, and stress reduction strategies.",
            "healthy_foods": [
                "Fresh leafy greens & colorful vegetables",
                "Antioxidant-rich berries & citrus fruits",
                "Lean proteins (beans, lentils, poultry, tofu)",
                "Whole grains (oats, quinoa, brown rice)",
                "Healthy fats (almonds, walnuts, chia seeds)"
            ],
            "diet_considerations": [
                "Stay well-hydrated with 2.5 - 3 liters of water daily",
                "Limit refined sugars and processed fast foods",
                "Ensure balanced meals with complex carbohydrates & protein"
            ],
            "exercise_suggestions": [
                "30 minutes of brisk walking or moderate cardio daily",
                "Basic bodyweight strength exercises (squats, lunges, pushups)",
                "Stretching or yoga for flexibility and recovery"
            ],
            "lifestyle_recommendations": [
                "Maintain 7-8 hours of consistent nightly sleep",
                "Practice mindfulness or deep breathing for stress relief",
                "Take regular active breaks from sitting"
            ],
            "medical_disclaimer": HEALTH_DISCLAIMER
        }


def _get_default_guidance(lang: str) -> Dict[str, Any]:
    return _generate_structured_domain_guidance("General Wellness & Energy", lang)
