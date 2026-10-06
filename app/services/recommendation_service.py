import json
import logging
import math
import re
import urllib.parse
from typing import Dict, Any, List, Optional
from flask import current_app
from app.services.maps_service import geocode_address, search_nearby_hospitals
from app.services.hospital_service import get_doctors_by_hospital_id, save_or_get_hospitals_batch, get_hospitals_from_db_near
from app.database.connection import get_db

logger = logging.getLogger(__name__)

# Medical Specialty Mappings for Diseases and Health Conditions
DISEASE_SPECIALTY_MAP = {
    'diabetes': ['General Physician', 'Genomic Medicine & Physician'],
    'diabetic': ['General Physician', 'Genomic Medicine & Physician'],
    'blood sugar': ['General Physician'],
    'cancer': ['Oncologist', 'Dermatologist & Oncologist'],
    'tumor': ['Oncologist'],
    'chemotherapy': ['Oncologist'],
    'leukemia': ['Oncologist'],
    'lymphoma': ['Oncologist'],
    'heart': ['Cardiologist'],
    'cardiac': ['Cardiologist'],
    'chest pain': ['Cardiologist'],
    'cardiovascular': ['Cardiologist'],
    'heart attack': ['Cardiologist'],
    'hypertension': ['Cardiologist', 'General Physician'],
    'blood pressure': ['General Physician', 'Cardiologist'],
    'skin': ['Dermatologist', 'Dermatologist & Oncologist'],
    'rash': ['Dermatologist'],
    'eczema': ['Dermatologist'],
    'psoriasis': ['Dermatologist'],
    'acne': ['Dermatologist'],
    'brain': ['Neurologist'],
    'neuro': ['Neurologist'],
    'neurological': ['Neurologist'],
    'stroke': ['Neurologist'],
    'seizure': ['Neurologist'],
    'parkinson': ['Neurologist'],
    'alzheimer': ['Neurologist'],
    'headache': ['Neurologist', 'General Physician'],
    'child': ['Pediatrician'],
    'children': ['Pediatrician'],
    'baby': ['Pediatrician'],
    'infant': ['Pediatrician'],
    'pediatric': ['Pediatrician'],
    'women': ['Gynecologist'],
    'pregnancy': ['Gynecologist'],
    'gynec': ['Gynecologist'],
    'gynaec': ['Gynecologist'],
    'maternity': ['Gynecologist'],
    'ovarian': ['Gynecologist'],
    'cervical': ['Gynecologist', 'Oncologist'],
    'bone': ['Orthopedic Doctor'],
    'joint': ['Orthopedic Doctor'],
    'fracture': ['Orthopedic Doctor'],
    'arthritis': ['Orthopedic Doctor'],
    'dna': ['Genomic Medicine & Physician', 'General Physician'],
    'genetic': ['Genomic Medicine & Physician', 'General Physician'],
    'genomic': ['Genomic Medicine & Physician', 'General Physician'],
    'mutation': ['Genomic Medicine & Physician', 'General Physician'],
    'cystic fibrosis': ['Genomic Medicine & Physician', 'General Physician'],
    'huntington': ['Genomic Medicine & Physician', 'Neurologist'],
    'sickle cell': ['Genomic Medicine & Physician', 'General Physician'],
}

KNOWN_SPECIALTIES = {
    'cardiologist': 'Cardiologist',
    'cardiology': 'Cardiologist',
    'oncologist': 'Oncologist',
    'oncology': 'Oncologist',
    'neurologist': 'Neurologist',
    'neurology': 'Neurologist',
    'dermatologist': 'Dermatologist',
    'dermatology': 'Dermatologist',
    'general physician': 'General Physician',
    'physician': 'General Physician',
    'pediatrician': 'Pediatrician',
    'pediatrics': 'Pediatrician',
    'gynecologist': 'Gynecologist',
    'gynaecologist': 'Gynecologist',
    'gynecology': 'Gynecologist',
    'orthopedic': 'Orthopedic Doctor',
    'orthopedist': 'Orthopedic Doctor',
    'orthopedics': 'Orthopedic Doctor',
    'genomic': 'Genomic Medicine & Physician',
    'dentist': 'Dentist',
    'dentistry': 'Dentist',
    'nephrologist': 'Nephrologist',
    'nephrology': 'Nephrologist',
    'hepatologist': 'Hepatologist',
    'pulmonologist': 'Pulmonologist',
    'ophthalmologist': 'Ophthalmologist',
    'psychiatrist': 'Psychiatrist',
    'psychologist': 'Psychiatrist',
}

KNOWN_CITIES = [
    'bengaluru', 'bangalore', 'mangalore', 'mangaluru',
    'karwar', 'ankola', 'mysore', 'mysuru', 'hubli', 'hubballi',
    'dharwad', 'belgaum', 'belagavi', 'udupi', 'shimoga', 'shivamogga',
    'delhi', 'mumbai', 'chennai', 'hyderabad', 'pune', 'kolkata', 'manipal'
]

CITY_ALIASES = {
    'bangalore': ['bangalore', 'bengaluru'],
    'bengaluru': ['bangalore', 'bengaluru'],
    'mysore': ['mysore', 'mysuru'],
    'mysuru': ['mysore', 'mysuru'],
    'mangalore': ['mangalore', 'mangaluru'],
    'mangaluru': ['mangalore', 'mangaluru'],
    'hubli': ['hubli', 'hubballi'],
    'hubballi': ['hubli', 'hubballi'],
    'belgaum': ['belgaum', 'belagavi'],
    'belagavi': ['belgaum', 'belagavi'],
    'shimoga': ['shimoga', 'shivamogga'],
    'shivamogga': ['shimoga', 'shivamogga'],
}

MULTILINGUAL_DISEASE_MAP = {
    # Hindi
    'मधुमेह': 'diabetes', 'शुगर': 'diabetes', 'कैंसर': 'cancer', 'हृदय': 'heart',
    'हार्ट': 'heart', 'त्वचा': 'skin', 'दिमाग': 'brain', 'बच्चे': 'child', 'महिला': 'women',
    # Kannada
    'ಮಧುಮೇಹ': 'diabetes', 'ಕ್ಯಾನ್ಸರ್': 'cancer', 'ಹೃದಯ': 'heart', 'ಚರ್ಮ': 'skin',
    'ಮೆದುಳು': 'brain', 'ಮಕ್ಕಳು': 'child',
    # Tamil
    'நீரிழிவு': 'diabetes', 'புற்றுநோய்': 'cancer', 'இதயம்': 'heart', 'தோல்': 'skin',
    'மூளை': 'brain', 'குழந்தை': 'child',
    # Telugu
    'మధుమేహం': 'diabetes', 'క్యాన్సర్': 'cancer', 'గుండె': 'heart', 'చర్మం': 'skin',
    'మెదడు': 'brain', 'పిల్లలు': 'child',
}

MULTILINGUAL_CITY_MAP = {
    'बैंगलोर': 'Bangalore', 'बेंगलोर': 'Bangalore', 'बेंगलुरु': 'Bangalore',
    'ಬೆಂಗಳೂರು': 'Bangalore', 'ಬೆಂಗಳೂರಿನಲ್ಲಿ': 'Bangalore',
    'பெங்களூர்': 'Bangalore', 'பெங்களூரில்': 'Bangalore',
    'బెంగళూరు': 'Bangalore', 'బెంగళూరులో': 'Bangalore',
    'मैसूर': 'Mysore', 'मैसूरु': 'Mysore', 'ಮೈಸೂರು': 'Mysore', 'மைசூர்': 'Mysore', 'మైసూర్': 'Mysore',
    'मुंबई': 'Mumbai', 'ಮುಂಬೈ': 'Mumbai', 'மும்பை': 'Mumbai', 'ముంబై': 'Mumbai',
    'दिल्ली': 'Delhi', 'ದೆಹಲಿ': 'Delhi', 'டெல்லி': 'Delhi', 'ఢిల్లీ': 'Delhi',
}
I18N_LABELS = {
    'en': {
        'header': "🏥 **Recommended Hospitals & Doctors**",
        'location': "Location",
        'dept': "Specialty / Department",
        'dist': "Distance",
        'doctors': "👨‍⚕️ **Recommended Doctors:**",
        'exp': "yrs exp",
        'book_btn': "Book Appointment",
        'view_hosp': "View Hospital Specialists",
        'view_map': "View on Map",
        'disclaimer': "Based on verified hospital and doctor location data.",
        'no_hospitals': "No matching hospitals found in {city}.",
        'no_hospitals_gen': "No matching hospitals or doctors were found for your request.",
        'prompt_location': "I need your location to find nearby hospitals. Please allow location access in your browser or specify a city.",
        'no_hospital_found': "I couldn't find that hospital in the available hospital data.",
        'no_doctor_found': "I couldn't find a matching doctor in the available data.",
        'no_condition_hosp': "I couldn't find a hospital matching this condition in the available data."
    },
    'hi': {
        'header': "🏥 **अनुशंसित अस्पताल और डॉक्टर**",
        'location': "स्थान",
        'dept': "विशेषज्ञता / विभाग",
        'dist': "दूरी",
        'doctors': "👨‍⚕️ **अनुशंसित डॉक्टर:**",
        'exp': "वर्ष का अनुभव",
        'book_btn': "अपॉइंटमेंट बुक करें",
        'view_hosp': "अस्पताल के डॉक्टर देखें",
        'view_map': "मानचित्र पर देखें",
        'disclaimer': "सत्यापित अस्पताल और डॉक्टर डेटा के आधार पर।",
        'no_hospitals': "{city} में कोई मेल खाता अस्पताल नहीं मिला।",
        'no_hospitals_gen': "आपकी आवश्यकता के लिए कोई अस्पताल या डॉक्टर नहीं मिला।",
        'prompt_location': "निकटतम अस्पताल खोजने के लिए मुझे आपके स्थान की आवश्यकता है। कृपया अपने ब्राउज़र में स्थान पहुँच की अनुमति दें या शहर बताएं।",
        'no_hospital_found': "उपलब्ध अस्पताल डेटा में वह अस्पताल नहीं मिला।",
        'no_doctor_found': "उपलब्ध डेटा में कोई मेल खाता डॉक्टर नहीं मिला।",
        'no_condition_hosp': "उपलब्ध डेटा में इस स्थिति से मेल खाता कोई अस्पताल नहीं मिला।"
    },
    'kn': {
        'header': "🏥 **ಶಿಫಾರಸು ಮಾಡಲಾದ ಆಸ್ಪತ್ರೆಗಳು ಮತ್ತು ವೈದ್ಯರು**",
        'location': "ಸ್ಥಳ",
        'dept': "ವಿಭಾಗ / ಪರಿಣತಿ",
        'dist': "ದೂರ",
        'doctors': "👨‍⚕️ **ಶಿಫಾರಸು ಮಾಡಲಾದ ವೈದ್ಯರು:**",
        'exp': "ವರ್ಷಗಳ ಅನುಭವ",
        'book_btn': "ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಬುಕ್ ಮಾಡಿ",
        'view_hosp': "ಆಸ್ಪತ್ರೆಯ ವೈದ್ಯರನ್ನು ವೀಕ್ಷಿಸಿ",
        'view_map': "ನಕ್ಷೆಯಲ್ಲಿ ವೀಕ್ಷಿಸಿ",
        'disclaimer': "ದೃಢೀಕರಿಸಿದ ಆಸ್ಪತ್ರೆ ಮತ್ತು ವೈದ್ಯರ ಡೇಟಾವನ್ನು ಆಧರಿಸಿದೆ.",
        'no_hospitals': "{city} ಯಲ್ಲಿ ಯಾವುದೇ ಆಸ್ಪತ್ರೆ ಕಂಡುಬಂದಿಲ್ಲ.",
        'no_hospitals_gen': "ನಿಮ್ಮ ವಿನಂತಿಗೆ ಯಾವುದೇ ಆಸ್ಪತ್ರೆ ಅಥವಾ ವೈದ್ಯರು ಕಂಡುಬಂದಿಲ್ಲ.",
        'prompt_location': "ಸಮೀಪದ ಆಸ್ಪತ್ರೆಗಳನ್ನು ಹುಡುಕಲು ನಿಮ್ಮ ಸ್ಥಳದ ವಿವರಗಳು ಬೇಕು. ದಯವಿಟ್ಟು ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಸ್ಥಳಾವಕಾಶ ನೀಡಲು ಅನುಮತಿಸಿ ಅಥವಾ ನಗರವನ್ನು ತಿಳಿಸಿ.",
        'no_hospital_found': "ಲಭ್ಯವಿರುವ ಆಸ್ಪತ್ರೆಯ ಡೇಟಾದಲ್ಲಿ ಆ ಆಸ್ಪತ್ರೆ ಕಂಡುಬಂದಿಲ್ಲ.",
        'no_doctor_found': "ಲಭ್ಯವಿರುವ ಡೇಟಾದಲ್ಲಿ ಯಾವುದೇ ವೈದ್ಯರು ಕಂಡುಬಂದಿಲ್ಲ.",
        'no_condition_hosp': "ಲಭ್ಯವಿರುವ ಡೇಟಾದಲ್ಲಿ ಈ ಸ್ಥಿತಿಗೆ ಹೊಂದುವ ಆಸ್ಪತ್ರೆ ಕಂಡುಬಂದಿಲ್ಲ."
    },
    'ta': {
        'header': "🏥 **பரிந்துரைக்கப்பட்ட மருத்துவமனைகள் மற்றும் மருத்துவர்கள்**",
        'location': "இடம்",
        'dept': "சிறப்பு / துறை",
        'dist': "தூரம்",
        'doctors': "👨‍⚕️ **பரிந்துரைக்கப்பட்ட மருத்துவர்கள்:**",
        'exp': "ஆண்டுகள் அனுபவம்",
        'book_btn': "முன்பதிவு செய்ய",
        'view_hosp': "மருத்துவர்களை பார்க்க",
        'view_map': "வரைபடத்தில் காண்க",
        'disclaimer': "சரிபார்க்கப்பட்ட மருத்துவமனை தரவுகளின் அடிப்படையில்.",
        'no_hospitals': "{city} இல் எந்த மருத்துவமனையும் கிடைக்கவில்லை.",
        'no_hospitals_gen': "உங்கள் கோரிக்கைக்கு ஏற்ற மருத்துவமனை கிடைக்கவில்லை.",
        'prompt_location': "அருகிலுள்ள மருத்துவமனைகளைக் கண்டறிய உங்கள் இருப்பிடம் தேவை. தயவுசெய்து இருப்பிட அனுமதியை வழங்கவும் அல்லது ஒரு நகரத்தைக் குறிப்பிடவும்.",
        'no_hospital_found': "கிடைக்கக்கூடிய மருத்துவமனை தரவில் அந்த மருத்துவமனை கிடைக்கவில்லை.",
        'no_doctor_found': "கிடைக்கக்கூடிய தரவில் பொருந்தக்கூடிய மருத்துவர் கிடைக்கவில்லை.",
        'no_condition_hosp': "கிடைக்கக்கூடிய தரவில் இந்த சிகிச்சைக்கு ஏற்ற மருத்துவமனை கிடைக்கவில்லை."
    },
    'te': {
        'header': "🏥 **సిఫార్సు చేసిన ఆసుపత్రులు మరియు వైద్యులు**",
        'location': "ప్రాంతం",
        'dept': "విభాగం / స్పెషాలిటీ",
        'dist': "దూరం",
        'doctors': "👨‍⚕️ **సిఫార్సు చేసిన వైద్యులు:**",
        'exp': "సంవత్సరాల అనుభవం",
        'book_btn': "అపాయింట్‌మెంట్ బుక్ చేయండి",
        'view_hosp': "వైద్యుల వివరాలు చూడండి",
        'view_map': "మ్యాప్‌లో చూడండి",
        'disclaimer': "ధృవీకరించబడిన ఆసుపత్రి మరియు వైద్యుల సమాచారం ఆధారంగా.",
        'no_hospitals': "{city} లో ఏ ఆసుపత్రి దొరకలేదు.",
        'no_hospitals_gen': "మీ కోరికకు తగిన ఆసుపత్రి లేదా వైద్యులు దొరకలేదు.",
        'prompt_location': "దగ్గరి ఆసుపత్రులను కనుగొనడానికి మీ లొకేషన్ అవసరం. దయచేసి బ్రౌజర్‌లో లొకేషన్ పర్మిషన్ ఇవ్వండి లేదా నగరాన్ని పేర్కొనండి.",
        'no_hospital_found': "అందుబాటులో ఉన్న ఆసుపత్రి డేటాలో ఆ ఆసుపత్రి దొరకలేదు.",
        'no_doctor_found': "అందుబాటులో ఉన్న డేటాలో సరిపోయే వైద్యులు దొరకలేదు.",
        'no_condition_hosp': "అందుబాటులో ఉన్న డేటాలో ఈ పరిస్థితికి సరిపోయే ఆసుపత్రి దొరకలేదు."
    }
}


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    v = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(v), math.sqrt(1 - v))


def _city_matches(requested_city: str, hospital_city: str, hospital_address: str = "") -> bool:
    if not requested_city:
        return True
    req_lower = requested_city.strip().lower()
    h_city_lower = (hospital_city or "").strip().lower()
    h_addr_lower = (hospital_address or "").strip().lower()

    aliases = CITY_ALIASES.get(req_lower, [req_lower])
    for alias in aliases:
        if alias in h_city_lower or alias in h_addr_lower:
            return True
    return False


def extract_intent_and_entities(message: str) -> Dict[str, Any]:
    """
    Parses user message to determine if it is a recommendation request
    and extracts disease/condition, specialty, location, target hospital, target doctor, and nearby flags.
    """
    msg_lower = message.strip().lower()

    hosp_keywords = [
        'hospital', 'hospitals', 'doctor', 'doctors', 'dr', 'dr.', 'physician', 'specialist',
        'cardiologist', 'cardiology', 'oncologist', 'oncology', 'neurologist', 'neurology',
        'dermatologist', 'dermatology', 'pediatrician', 'pediatrics', 'gynecologist', 'gynecology',
        'orthopedic', 'orthopedics', 'dentist', 'dentistry', 'nephrologist', 'nephrology',
        'pulmonologist', 'ophthalmologist', 'psychiatrist',
        'clinic', 'nursing home', 'medical center', 'treatment', 'consultant', 'dispensary',
        'अस्पताल', 'डॉक्टर', 'ಆಸ್ಪತ್ರೆ', 'ವೈದ್ಯರು', 'மருத்துவமனை', 'மருத்துவர்', 'ఆసుపత్రి', 'వైద్యుడు'
    ]

    action_keywords = [
        'suggest', 'recommend', 'find', 'need', 'want', 'looking for', 'search',
        'where to go', 'which hospital', 'which doctor', 'near me', 'nearby',
        'visit', 'book', 'consult', 'available in', 'closest',
        'सुझाव', 'चाहिए', 'पास', 'ಸಮೀಪ', 'ಅಗತ್ಯ', 'வேண்டும்', 'அருகில்', 'కావాలి', 'దగ్గర', 'ತಿಳಿಸಿ'
    ]

    has_hosp_kw = any(kw in msg_lower for kw in hosp_keywords)
    has_action_kw = any(kw in msg_lower for kw in action_keywords)

    is_pure_info_question = bool(re.search(r'^(what is|explain|what are the symptoms|how does|define)\b', msg_lower))

    is_recommendation = (has_hosp_kw or (has_action_kw and (any(d in msg_lower for d in DISEASE_SPECIALTY_MAP) or any(md in msg_lower for md in MULTILINGUAL_DISEASE_MAP)))) and not is_pure_info_question

    if not is_recommendation:
        return {'is_recommendation': False}

    # Extract Specialty
    extracted_specialty = None
    for kw, spec_name in KNOWN_SPECIALTIES.items():
        if kw in msg_lower:
            extracted_specialty = spec_name
            break

    # Extract Disease / Condition (English)
    extracted_disease = None
    for dis_key in DISEASE_SPECIALTY_MAP:
        if dis_key in msg_lower:
            extracted_disease = dis_key
            break

    # Extract Disease / Condition (Multilingual)
    if not extracted_disease:
        for m_key, m_val in MULTILINGUAL_DISEASE_MAP.items():
            if m_key in msg_lower:
                extracted_disease = m_val
                break

    # Extract Specific Doctor Query (e.g. "I want Dr. Alexander Wright" or "Find Dr. XYZ")
    doctor_name_query = None
    doc_m = re.search(r'\b(?:dr\.?|doctor)\s+([a-zA-Z\s]{2,30})\b', message, re.IGNORECASE)
    if doc_m:
        candidate_doc = doc_m.group(1).strip().title()
        cand_lower = candidate_doc.lower()
        stopwords_doc = {'appointment', 'recommendation', 'near me', 'nearby', 'in bangalore', 'specialist', 'physician', 'cardiologist', 'oncologist', 'neurologist', 'dermatologist', 'pediatrician', 'gynecologist', 'orthopedic', 'for diabetes', 'for cancer', 'for heart', 'who', 'which', 'and hospital', 'in', 'at'}
        if cand_lower not in stopwords_doc and not any(kw in cand_lower for kw in ['hospital', 'appointment', 'near', 'specialist']):
            doctor_name_query = candidate_doc

    # Extract Specific Hospital Name Query if user mentioned a hospital brand
    hospital_name_query = None
    known_hospital_chains = ['manipal', 'apollo', 'fortis', 'narayana', 'max', 'columbia asia', 'aster', 'kmc', 'sparsh', 'sakra', 'bgs', 'cloudnine']
    for chain in known_hospital_chains:
        if chain in msg_lower:
            hospital_name_query = chain.title()
            break

    if not hospital_name_query:
        h_m = re.search(r'\b([a-zA-Z0-9\s]{3,30})\s+hospital\b', message, re.IGNORECASE)
        if h_m:
            candidate_h = h_m.group(1).strip().title()
            cand_h_lower = candidate_h.lower()
            stopwords_h = {'a', 'the', 'good', 'nearby', 'any', 'which', 'cancer', 'diabetes', 'best', 'some', 'me a', 'my', 'find a', 'need a', 'suggest a', 'suggest me a', 'recommend a', 'recommend me a'}
            if cand_h_lower not in stopwords_h and not any(kw in cand_h_lower for kw in ['cancer', 'diabetes', 'heart', 'nearby', 'good', 'best', 'suggest', 'recommend', 'need', 'find']):
                hospital_name_query = candidate_h

    # Extract Location
    extracted_location = None

    # Priority 1: Match "in <City>", "at <City>", "near <City>" via regex
    m = re.search(r'\b(?:in|at|near)\s+([a-zA-Z0-9\s]{2,25})\b', message, re.IGNORECASE)
    if m:
        candidate = m.group(1).strip().title()
        cand_lower = candidate.lower()
        stopwords = {'me', 'my', 'here', 'hospital', 'hospitals', 'doctor', 'doctors', 'treatment', 'cancer', 'diabetes', 'the city', 'my area'}
        if cand_lower not in stopwords and not any(kw in cand_lower for kw in ['hospital', 'doctor']):
            extracted_location = candidate

    # Priority 2: Check KNOWN_CITIES if regex didn't find location
    if not extracted_location:
        for city in KNOWN_CITIES:
            if city in msg_lower:
                # If city matches hospital chain name (e.g. 'manipal') and 'in manipal' wasn't specified, skip treating as city
                if hospital_name_query and city.lower() == hospital_name_query.lower() and not re.search(r'\bin\s+manipal\b', msg_lower):
                    continue
                extracted_location = city.title()
                break

    # Priority 3: Multilingual city map
    if not extracted_location:
        for m_city, eng_city in MULTILINGUAL_CITY_MAP.items():
            if m_city in msg_lower:
                extracted_location = eng_city
                break

    # Extract Nearby Flag
    is_nearby = any(nb in msg_lower for nb in [
        'near me', 'nearby', 'closest', 'around me', 'near my location',
        'पास', 'ಸಮೀಪ', 'ಅருகில்', 'దగ్గర'
    ])

    return {
        'is_recommendation': True,
        'disease': extracted_disease,
        'specialty': extracted_specialty,
        'location': extracted_location,
        'is_nearby': is_nearby,
        'hospital_name_query': hospital_name_query,
        'doctor_name_query': doctor_name_query
    }


def _get_db_hospitals_by_city_or_coords(search_city: str, lat: Optional[float], lng: Optional[float], hosp_name_query: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        aliases = CITY_ALIASES.get(search_city.lower(), [search_city.lower()])
        where_clauses = []
        params = []

        for alias in aliases:
            where_clauses.append("city LIKE %s OR address LIKE %s")
            params.extend([f"%{alias}%", f"%{alias}%"])

        query = f"SELECT id as db_id, external_place_id, name, address, city, state, country, phone, opening_hours, latitude as lat, longitude as lng FROM hospitals WHERE ({' OR '.join(where_clauses)})"
        
        if hosp_name_query:
            query += " AND name LIKE %s"
            params.append(f"%{hosp_name_query}%")
        query += " LIMIT 20"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return rows


def _get_db_hospitals_by_name(hosp_name_query: str) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id as db_id, external_place_id, name, address, city, state, country, phone, opening_hours, latitude as lat, longitude as lng FROM hospitals WHERE name LIKE %s LIMIT 20"
        cursor.execute(query, (f"%{hosp_name_query}%",))
        rows = cursor.fetchall()
        cursor.close()
        return rows


def _get_doctor_by_name(doctor_name_query: str) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT d.*, h.id as hospital_id, h.name as hospital_name, h.address as hospital_address, 
                   h.city as hospital_city, h.latitude as lat, h.longitude as lng, h.external_place_id 
            FROM doctors d 
            JOIN hospitals h ON d.hospital_id = h.id 
            WHERE d.full_name LIKE %s 
            LIMIT 5
        """
        cursor.execute(query, (f"%{doctor_name_query}%",))
        rows = cursor.fetchall()
        cursor.close()
        return rows


def _merge_hospital_lists(list1: List[Dict[str, Any]], list2: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for item in list1 + list2:
        h_id = item.get('db_id') or item.get('id')
        name_key = (item.get('name', '').strip().lower(), round(float(item.get('lat') or 0), 3), round(float(item.get('lng') or 0), 3))
        if h_id and h_id in seen:
            continue
        if name_key in seen:
            continue
        if h_id:
            seen.add(h_id)
        seen.add(name_key)
        result.append(item)
    return result


def get_ai_recommendation(
    message: str,
    language: str = "en",
    user_location: Optional[Dict[str, float]] = None,
    user_info: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Core Recommendation Engine. Returns response dict if message is recommendation request, else None.
    Uses verified location sources only; never invents or hallucinates hospital details.
    """
    labels = I18N_LABELS.get(language, I18N_LABELS['en'])
    intent_data = extract_intent_and_entities(message)
    if not intent_data.get('is_recommendation'):
        return None

    disease = intent_data.get('disease')
    specialty = intent_data.get('specialty')
    location_str = intent_data.get('location')
    is_nearby = intent_data.get('is_nearby')
    hosp_name_query = intent_data.get('hospital_name_query')
    doctor_name_query = intent_data.get('doctor_name_query')

    # SPECIFIC DOCTOR SEARCH (Requirement 8)
    if doctor_name_query:
        matched_docs = _get_doctor_by_name(doctor_name_query)
        if not matched_docs:
            return {
                'response': labels['no_doctor_found'],
                'language': language
            }
        
        user_lat, user_lng = None, None
        if user_location and user_location.get('lat') is not None and user_location.get('lng') is not None:
            try:
                user_lat = float(user_location['lat'])
                user_lng = float(user_location['lng'])
            except (ValueError, TypeError):
                pass

        response_lines = [labels['header'], ""]
        for idx, doc in enumerate(matched_docs, 1):
            h_id = doc['hospital_id']
            h_name = doc['hospital_name']
            h_addr = doc['hospital_address']
            h_city = doc['hospital_city']
            h_loc = f"{h_addr}, {h_city}".strip(", ") if h_addr else h_city

            response_lines.append(f"**{idx}. {h_name}**")
            if h_loc:
                response_lines.append(f"• **{labels['location']}:** {h_loc}")

            h_lat = doc.get('lat')
            h_lng = doc.get('lng')
            if user_lat is not None and user_lng is not None and h_lat is not None and h_lng is not None:
                dist = round(_haversine_distance(user_lat, user_lng, float(h_lat), float(h_lng)), 1)
                response_lines.append(f"• **{labels['dist']}:** {dist} km")

            response_lines.append(f"• **{labels['dept']}:** {doc['specialty']}")

            ext_id = doc.get('external_place_id') or ''
            if ext_id.startswith('google_'):
                place_id = ext_id.replace('google_', '')
                map_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            elif h_lat is not None and h_lng is not None:
                map_url = f"https://www.google.com/maps/search/?api=1&query={h_lat},{h_lng}"
            else:
                map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(f'{h_name} {h_city}')}"

            response_lines.append(f"📍 [{labels['view_map']}]({map_url})")

            response_lines.append(f"\n{labels['doctors']}")
            response_lines.append(f"• **{doc['full_name']}** — {doc['specialty']} ({doc.get('experience_years', 5)} {labels['exp']})")
            response_lines.append(f"  [{labels['book_btn']}](/appointments/book?hospital_id={h_id}&doctor_id={doc['id']})")
            response_lines.append(f"👉 [{labels['view_hosp']}](/hospitals/{h_id}/doctors)\n")

        response_lines.append(f"_\nℹ️ {labels['disclaimer']}_")
        return {
            'response': "\n".join(response_lines),
            'language': language
        }

    target_specialties = []
    if specialty:
        target_specialties = [specialty]
    elif disease:
        target_specialties = DISEASE_SPECIALTY_MAP.get(disease.lower(), ['General Physician'])

    search_city = None
    user_lat = None
    user_lng = None
    hospitals_list = []

    # CASE 1: User explicitly requested a city/location (e.g. "Bangalore", "Delhi", "Mumbai")
    if location_str:
        search_city = location_str.title()
        coords = geocode_address(search_city)
        if coords:
            user_lat = coords['lat']
            user_lng = coords['lng']
            # Search existing verified hospitals in DB matching city or coordinates
            hospitals_list = _get_db_hospitals_by_city_or_coords(search_city, user_lat, user_lng, hosp_name_query)

        # If DB has no verified hospitals for search_city (or < 3), query Places/Maps API at city coords
        if (not hospitals_list or len(hospitals_list) < 3) and coords:
            try:
                places_hospitals = search_nearby_hospitals(coords['lat'], coords['lng'], radius_km=30.0)
                if places_hospitals:
                    for ph in places_hospitals:
                        if not ph.get('city'):
                            ph['city'] = search_city
                    places_hospitals = save_or_get_hospitals_batch(places_hospitals)
                    
                    filtered_places = []
                    for ph in places_hospitals:
                        d = _haversine_distance(user_lat, user_lng, float(ph['lat']), float(ph['lng']))
                        ph['distance_km'] = round(d, 1)
                        if d <= 40.0 or _city_matches(search_city, ph.get('city', ''), ph.get('address', '')):
                            filtered_places.append(ph)
                    
                    hospitals_list = _merge_hospital_lists(hospitals_list, filtered_places)
            except Exception as exc:
                logger.warning("Places API lookup failed for %s: %s", search_city, exc)

        # STRICT VERIFICATION: Filter so ONLY hospitals matching requested location are retained
        if hospitals_list:
            verified_city_hospitals = []
            for h in hospitals_list:
                h_city = h.get('city') or ''
                h_addr = h.get('address') or ''
                h_lat = float(h.get('lat') or 0)
                h_lng = float(h.get('lng') or 0)
                
                matches_city_text = _city_matches(search_city, h_city, h_addr)
                in_radius = (user_lat is not None and user_lng is not None and _haversine_distance(user_lat, user_lng, h_lat, h_lng) <= 40.0)
                
                if matches_city_text or in_radius:
                    verified_city_hospitals.append(h)
            
            hospitals_list = verified_city_hospitals

        # Filter by specific hospital name query if user asked for a specific brand (e.g. "Manipal")
        if hosp_name_query and hospitals_list:
            matched_name = [h for h in hospitals_list if hosp_name_query.lower() in h.get('name', '').lower()]
            if matched_name:
                hospitals_list = matched_name

        # If after searching DB and Places API no verified hospital matches requested city, state clear message (Requirement 5)
        if not hospitals_list:
            return {
                'response': labels['no_hospitals'].format(city=search_city),
                'language': language
            }

    # CASE 2: Nearby requested ("near me", "nearby")
    elif is_nearby:
        if user_location and user_location.get('lat') is not None and user_location.get('lng') is not None:
            try:
                user_lat = float(user_location['lat'])
                user_lng = float(user_location['lng'])
            except (ValueError, TypeError):
                user_lat, user_lng = None, None

        if user_lat is None or user_lng is None:
            # Browser location permission not available - prompt user (Requirement 6 & 14)
            return {
                'response': labels['prompt_location'],
                'language': language
            }

        # Search DB near exact user GPS coordinates
        hospitals_list = get_hospitals_from_db_near(user_lat, user_lng, radius_km=50.0)

        # If DB has fewer than 3 hospitals near user GPS coords, search Places/Maps API
        if not hospitals_list or len(hospitals_list) < 3:
            try:
                live_hospitals = search_nearby_hospitals(user_lat, user_lng, radius_km=50.0)
                if live_hospitals:
                    live_hospitals = save_or_get_hospitals_batch(live_hospitals)
                    hospitals_list = _merge_hospital_lists(hospitals_list, live_hospitals)
            except Exception as exc:
                logger.warning("Nearby search failed: %s", exc)

        if hosp_name_query and hospitals_list:
            matched_name = [h for h in hospitals_list if hosp_name_query.lower() in h.get('name', '').lower()]
            if matched_name:
                hospitals_list = matched_name

        if not hospitals_list:
            return {
                'response': labels['no_hospitals_gen'],
                'language': language
            }

    # CASE 3: Neither location nor nearby explicitly in prompt
    else:
        # Check user_location (device GPS) first
        if user_location and user_location.get('lat') is not None and user_location.get('lng') is not None:
            try:
                user_lat = float(user_location['lat'])
                user_lng = float(user_location['lng'])
                hospitals_list = get_hospitals_from_db_near(user_lat, user_lng, radius_km=50.0)
                if not hospitals_list or len(hospitals_list) < 3:
                    live_hospitals = search_nearby_hospitals(user_lat, user_lng, radius_km=50.0)
                    if live_hospitals:
                        live_hospitals = save_or_get_hospitals_batch(live_hospitals)
                        hospitals_list = _merge_hospital_lists(hospitals_list, live_hospitals)
            except (ValueError, TypeError):
                user_lat, user_lng = None, None

        # Check specific hospital name if requested without location (e.g. "I want Manipal Hospital")
        if hosp_name_query:
            db_matched_hosp = _get_db_hospitals_by_name(hosp_name_query)
            if db_matched_hosp:
                hospitals_list = db_matched_hosp
            elif not hospitals_list:
                return {
                    'response': labels['no_hospital_found'],
                    'language': language
                }

        # Check registered user profile location if hospitals_list is still empty
        if not hospitals_list:
            reg_city = (user_info.get('city') if user_info else '') or ''
            reg_lat = (user_info.get('latitude') if user_info else None)
            reg_lng = (user_info.get('longitude') if user_info else None)

            if reg_city:
                search_city = reg_city.title()
                coords = geocode_address(search_city)
                if coords:
                    user_lat = coords['lat']
                    user_lng = coords['lng']
                hospitals_list = _get_db_hospitals_by_city_or_coords(search_city, user_lat, user_lng, hosp_name_query)
            elif reg_lat and reg_lng:
                user_lat = float(reg_lat)
                user_lng = float(reg_lng)
                hospitals_list = get_hospitals_from_db_near(user_lat, user_lng, radius_km=50.0)

        # Filter by hosp_name_query if specified
        if hosp_name_query and hospitals_list:
            matched_name = [h for h in hospitals_list if hosp_name_query.lower() in h.get('name', '').lower()]
            if matched_name:
                hospitals_list = matched_name
            else:
                return {
                    'response': labels['no_hospital_found'],
                    'language': language
                }

        if not hospitals_list:
            return {
                'response': labels['prompt_location'],
                'language': language
            }

    # Calculate actual geographic distance for every hospital in results
    for hosp in hospitals_list:
        h_lat = hosp.get('lat') or hosp.get('latitude')
        h_lng = hosp.get('lng') or hosp.get('longitude')
        if user_lat is not None and user_lng is not None and h_lat is not None and h_lng is not None:
            hosp['distance_km'] = round(_haversine_distance(user_lat, user_lng, float(h_lat), float(h_lng)), 1)
        elif hosp.get('distance_km') is None:
            hosp['distance_km'] = None

    # Match Doctors & Rank Results
    matched_results = []
    for hosp in hospitals_list:
        h_id = hosp.get('db_id') or hosp.get('id')
        if not h_id:
            continue

        docs = get_doctors_by_hospital_id(h_id)

        matching_docs = []
        if target_specialties:
            for doc in docs:
                doc_spec = doc.get('specialty', '').lower()
                for t_spec in target_specialties:
                    ts_lower = t_spec.lower()
                    if (ts_lower in doc_spec or doc_spec in ts_lower or 
                        ('oncolog' in ts_lower and 'oncolog' in doc_spec) or
                        ('cardio' in ts_lower and 'cardio' in doc_spec) or
                        ('neuro' in ts_lower and 'neuro' in doc_spec) or
                        ('derma' in ts_lower and 'derma' in doc_spec) or
                        ('pediatr' in ts_lower and 'pediatr' in doc_spec) or
                        ('gynec' in ts_lower and 'gynec' in doc_spec) or
                        ('ortho' in ts_lower and 'ortho' in doc_spec) or
                        (('physician' in ts_lower or 'genomic' in ts_lower or 'diabet' in ts_lower) and ('physician' in doc_spec or 'genomic' in doc_spec))):
                        matching_docs.append(doc)
                        break

        # STRICT SPECIALTY FILTERING: If condition/specialty was requested, only keep matching doctors!
        if target_specialties:
            selected_docs = matching_docs
        else:
            selected_docs = docs

        # If condition/specialty was requested, only retain hospitals that have at least 1 matching doctor
        if target_specialties and not selected_docs:
            continue

        matched_results.append({
            'hospital': hosp,
            'doctors': selected_docs,
            'has_exact_match': len(matching_docs) > 0
        })

    if target_specialties and not matched_results:
        return {
            'response': labels['no_doctor_found'],
            'language': language
        }

    # Sort results: exact specialty matches first, then actual distance
    matched_results.sort(key=lambda x: (not x['has_exact_match'], x['hospital'].get('distance_km') if x['hospital'].get('distance_km') is not None else 999))

    # Format Chatbot Response Output
    response_lines = [labels['header'], ""]

    top_results = matched_results[:3]
    for idx, item in enumerate(top_results, 1):
        hosp = item['hospital']
        docs = item['doctors']
        h_id = hosp.get('db_id') or hosp.get('id')

        h_name = hosp.get('name', 'Hospital')
        h_addr = hosp.get('address', '')
        h_city = hosp.get('city') or search_city or ''
        h_loc = f"{h_addr}, {h_city}".strip(", ") if h_addr else h_city

        response_lines.append(f"**{idx}. {h_name}**")
        if h_loc:
            response_lines.append(f"• **{labels['location']}:** {h_loc}")

        if hosp.get('distance_km') is not None:
            response_lines.append(f"• **{labels['dist']}:** {hosp['distance_km']} km")

        if target_specialties:
            response_lines.append(f"• **{labels['dept']}:** {', '.join(target_specialties)}")

        # Verified Google Maps link (Requirement 10)
        ext_id = hosp.get('external_place_id') or ''
        h_lat = hosp.get('lat') or hosp.get('latitude')
        h_lng = hosp.get('lng') or hosp.get('longitude')
        
        if ext_id.startswith('google_'):
            place_id = ext_id.replace('google_', '')
            map_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        elif h_lat is not None and h_lng is not None:
            map_url = f"https://www.google.com/maps/search/?api=1&query={h_lat},{h_lng}"
        else:
            map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(f'{h_name} {h_city}')}"

        response_lines.append(f"📍 [{labels['view_map']}]({map_url})")

        if docs:
            response_lines.append(f"\n{labels['doctors']}")
            for doc in docs[:2]:
                doc_id = doc.get('id')
                doc_name = doc.get('full_name', 'Doctor')
                doc_spec = doc.get('specialty', 'Specialist')
                doc_exp = doc.get('experience_years', 5)
                response_lines.append(f"• **{doc_name}** — {doc_spec} ({doc_exp} {labels['exp']})")
                response_lines.append(f"  [{labels['book_btn']}](/appointments/book?hospital_id={h_id}&doctor_id={doc_id})")

        response_lines.append(f"👉 [{labels['view_hosp']}](/hospitals/{h_id}/doctors)\n")

    response_lines.append(f"_\nℹ️ {labels['disclaimer']}_")

    return {
        'response': "\n".join(response_lines),
        'language': language
    }
