from flask import Blueprint, render_template, session, jsonify, current_app, request
from app.routes.auth import login_required
from app.services.dna_service import SAMPLE_SEQUENCES
from app.services.chatbot_service import _call_ollama
from datetime import datetime
import random
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

DNA_FACTS_BY_LANG = {
    "en": [
        "Human DNA is about 99.9% identical from person to person.",
        "If uncoiled, the DNA in all your cells would stretch to Pluto and back.",
        "About 8% of human DNA is made of ancient viral fragments.",
        "We share about 60% of our DNA with bananas and fruit flies.",
        "DNA has a half-life of 521 years and degrades over time.",
        "A single gram of DNA can store roughly 215 petabytes of data.",
        "Identical twins have the exact same DNA code.",
        "There are over 3 billion base pairs in the human genome.",
        "Genes make up only about 1% to 2% of human DNA.",
        "The DNA double helix was discovered by Watson, Crick, and Franklin in 1953."
    ],
    "hi": [
        "मानव डीएनए एक व्यक्ति से दूसरे व्यक्ति में लगभग 99.9% समान होता है।",
        "यदि आपकी सभी कोशिकाओं के डीएनए को खोला जाए, तो वह प्लूटो तक जाकर वापस आ सकता है।",
        "मानव डीएनए का लगभग 8% हिस्सा प्राचीन वायरल टुकड़ों से बना है।",
        "हम केला और फल मक्खियों के साथ अपने डीएनए का लगभग 60% साझा करते हैं।",
        "डीएनए का आधा जीवन 521 वर्ष का होता है और यह समय के साथ क्षय होता है।",
        "एक ग्राम डीएनए लगभग 215 पेटाबाइट डेटा स्टोर कर सकता है।",
        "समरूप जुड़वां बच्चों का डीएनए कोड बिल्कुल एक जैसा होता है।",
        "मानव जीनोम में 3 अरब से अधिक बेस पेयर होते हैं।",
        "जीन मानव डीएनए का केवल लगभग 1% से 2% हिस्सा बनाते हैं।",
        "डीएनए डबल हेलिक्स की खोज 1953 में वाटसन, क्रिक और फ्रैंकलिन ने की थी।"
    ],
    "kn": [
        "ಮಾನವನ ಡಿಎನ್‌ಎ ವ್ಯಕ್ತಿಯಿಂದ ವ್ಯಕ್ತಿಗೆ ಸುಮಾರು 99.9% ಒಂದೇ ರೀತಿಯದ್ದಾಗಿದೆ.",
        "ನಿಮ್ಮ ಎಲ್ಲಾ ಕೋಶಗಳಲ್ಲಿನ ಡಿಎನ್‌ಎಯನ್ನು ಬಿಚ್ಚಿದರೆ, ಅದು ಪ್ಲುಟೊವರೆಗೆ ಹೋಗಿ ಹಿಂತಿರುಗಬಹುದು.",
        "ಮಾನವ ಡಿಎನ್‌ಎಯ ಸುಮಾರು 8% ಪ್ರಾಚೀನ ವೈರಲ್ ತುಣುಕುಗಳಿಂದ ಮಾಡಲ್ಪಟ್ಟಿದೆ.",
        "ನಾವು ಬಾಳೆಹಣ್ಣುಗಳು ಮತ್ತು ಹಣ್ಣಿನ ನೊಣಗಳೊಂದಿಗೆ ನಮ್ಮ ಡಿಎನ್‌ಎಯ ಸುಮಾರು 60% ಅನ್ನು ಹಂಚಿಕೊಳ್ಳುತ್ತೇವೆ.",
        "ಡಿಎನ್‌ಎ 521 ವರ್ಷಗಳ ಅರ್ಧ-ಆಯುಷ್ಯವನ್ನು ಹೊಂದಿದೆ ಮತ್ತು ಕಾಲಕ್ರಮೇಣ ಕ್ಷೀಣಿಸುತ್ತದೆ.",
        "ಒಂದು ಗ್ರಾಂ ಡಿಎನ್‌ಎ ಸುಮಾರು 215 ಪೆಟಾಬೈಟ್ ಡೇಟಾವನ್ನು ಸಂಗ್ರಹಿಸಬಹುದು.",
        "ಏಕರೂಪದ ಅವಳಿಗಳು ನಿಖರವಾಗಿ ಒಂದೇ ರೀತಿಯ ಡಿಎನ್‌ಎ ಕೋಡ್ ಅನ್ನು ಹೊಂದಿರುತ್ತಾರೆ.",
        "ಮಾನವ ಜೀನೋಮ್‌ನಲ್ಲಿ 3 ಶತಕೋಟಿಗೂ ಹೆಚ್ಚು ಬೇಸ್ ಜೋಡಿಗಳಿವೆ.",
        "ಜೀನ್‌ಗಳು ಮಾನವ ಡಿಎನ್‌ಎಯ ಸುಮಾರು 1% ರಿಂದ 2% ರಷ್ಟು ಮಾತ್ರ ಹೊಂದಿರುತ್ತವೆ.",
        "ಡಿಎನ್‌ಎ ಡಬಲ್ ಹೆಲಿಕ್ಸ್ ಅನ್ನು 1953 ರಲ್ಲಿ ವಾಟ್ಸನ್, ಕ್ರಿಕ್ ಮತ್ತು ಫ್ರಾಂಕ್ಲಿನ್ ಕಂಡುಹಿಡಿದರು."
    ],
    "ta": [
        "மனித டிஎன்ஏ நபருக்கு நபர் சுமார் 99.9% ஒரே மாதிரியாக இருக்கும்.",
        "சுருக்கப்படாமல் விரித்தால், உங்கள் எல்லா செல்களிலும் உள்ள டிஎன்ஏ பிளൂട്ടோ வரை சென்று திரும்பும்.",
        "மனித டிஎன்ஏவில் சுமார் 8% பழங்கால வைரஸ் துண்டுகளால் ஆனது.",
        "வாழைப்பழங்கள் மற்றும் பழ ஈக்களுடன் நாம் சுமார் 60% டிஎன்ஏவைப் பகிர்ந்து கொள்கிறோம்.",
        "டிஎன்ஏவின் அரை ஆயுள் 521 ஆண்டுகள் மற்றும் காலப்போக்கில் சிதைகிறது.",
        "ஒரு கிராம் டிஎன்ஏ சுமார் 215 பெட்டாபைட் டேட்டாவை சேமிக்க முடியும்.",
        "ஒரே மாதிரியான இரட்டையர்கள் ஒரே மாதிரியான டிஎன்ஏ குறியீட்டைக் கொண்டுள்ளனர்.",
        "மனித மரபணுவில் 3 பில்லியனுக்கும் அதிகமான கார இணைகள் உள்ளன.",
        "மரபணுக்கள் மனித டிஎன்ஏவில் சுமார் 1% முதல் 2% மட்டுமே உள்ளன.",
        "டிஎன்ஏ இரட்டை ஹெலிக்ஸ் 1953 இல் வாட்சன், கிரிக் மற்றும் ஃபிராங்க்ளின் ஆகியோரால் கண்டுபிடிக்கப்பட்டது."
    ],
    "te": [
        "మానవ డీఎన్ఏ ఒక వ్యక్తి నుండి మరొక వ్యక్తికి దాదాపు 99.9% ఒకేలా ఉంటుంది.",
        "మీ అన్ని కణాలలోని డీఎన్ఏను విప్పితే, అది ప్లూటో వరకు వెళ్లి తిరిగి రాగలదు.",
        "మానవ డీఎన్ఏలో దాదాపు 8% పురాతన వైరల్ విభాగాలు ఉంటాయి.",
        "మనం అరటిపండ్లు మరియు పండ్ల ఈగలతో దాదాపు 60% డీఎన్ఏను పంచుకుంటాము.",
        "డీఎన్ఏ అర్ధ జీవిత కాలం 521 సంవత్సరాలు మరియు కాలక్రమేణా క్షీణిస్తుంది.",
        "ఒక గ్రాము డీఎన్ఏ దాదాపు 215 పెటాబైట్ల డేటాను నిల్వ చేయగలదు.",
        "సమరూప కవలలు ఖచ్చితంగా ఒకే డీఎన్ఏ కోడ్‌ను కలిగి ఉంటారు.",
        "మానవ జీనోమ్‌లో 3 బిలియన్లకు పైగా బేస్ జత ఉన్నాయి.",
        "జీన్లు మానవ డీఎన్ఏలో దాదాపు 1% నుండి 2% మాత్రమే ఉంటాయి.",
        "డీఎన్ఏ డబుల్ హెలిక్స్ 1953 లో వాట్సన్, క్రిక్ మరియు ఫ్రాంక్లిన్ కనుగొన్నారు."
    ]
}

DNA_FACTS = DNA_FACTS_BY_LANG["en"]

def get_time_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 22:
        return "Evening"
    else:
        return "Night"

@dashboard_bp.route('/')
@login_required
def index():
    greeting_time = get_time_greeting()
    # Provide a random fallback fact initially so the UI doesn't look empty
    random_fact = random.choice(DNA_FACTS_BY_LANG["en"])
    return render_template('dashboard/index.html', samples=SAMPLE_SEQUENCES, greeting_time=greeting_time, dna_fact=random_fact)

@dashboard_bp.route('/api/dna-fact')
@login_required
def get_dna_fact():
    lang = request.args.get('lang', 'en')
    facts_list = DNA_FACTS_BY_LANG.get(lang, DNA_FACTS_BY_LANG['en'])
    fact = random.choice(facts_list)
    return jsonify({"fact": fact, "source": "multilingual_system"})
