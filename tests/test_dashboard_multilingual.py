import json
import re
import pytest
from app import create_app

def parse_translations():
    with open("app/static/js/translations.js", "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'window\.TRANSLATIONS\s*=\s*(\{[\s\S]*\});', content)
    assert match, "Could not find window.TRANSLATIONS in translations.js"
    json_str = match.group(1)
    return json.loads(json_str)

DASHBOARD_KEYS = [
    "dash_page_title",
    "gen_greeting_morning",
    "gen_greeting_afternoon",
    "gen_greeting_evening",
    "gen_greeting_night",
    "gen_explore_your_dna_analys",
    "gen_dna_fact",
    "auto_316f1e",
    "gen_dna_analysis_tools",
    "gen_choose_an_analysis_to_ex",
    "auto_e4fd95",
    "auto_45c977",
    "gen_explore_action",
    "auto_5ff956",
    "auto_5586e9",
    "auto_e80432",
    "auto_eade18",
    "auto_c9f142",
    "auto_121047",
    "auto_578801",
    "auto_26c782",
    "auto_7883e2",
    "auto_683fc8",
    "gen_home_8cf0",
    "gen_genetic_analysis_ce47",
    "auto_90f8e4",
    "gen_hospitals_doctors_3561",
    "gen_diet_planner_fde2",
    "gen_doctor_appointment",
    "nav_appointments",
    "auto_c40eb6",
    "nav_settings",
    "nav_logout"
]

LANGUAGES = ["en", "kn", "hi", "te", "ta"]

def test_dashboard_keys_exist_in_all_languages():
    translations = parse_translations()
    for lang in LANGUAGES:
        assert lang in translations, f"Language {lang} missing in translations.js"
        for key in DASHBOARD_KEYS:
            assert key in translations[lang], f"Key '{key}' missing for language '{lang}'"
            val = translations[lang][key]
            assert val and isinstance(val, str), f"Empty or non-string value for '{key}' in '{lang}'"

def test_no_untranslated_english_in_dashboard_keys():
    translations = parse_translations()
    # Non-english languages must not match the exact English value for keys that should be translated
    for lang in ["kn", "hi", "te", "ta"]:
        for key in DASHBOARD_KEYS:
            en_val = translations["en"][key]
            lang_val = translations[lang][key]
            assert lang_val != en_val, f"Key '{key}' in language '{lang}' has untranslated English text: '{lang_val}'"

def test_dashboard_route_renders():
    app = create_app()
    with app.test_client() as client:
        # Route should either redirect to login or render OK
        response = client.get('/dashboard/')
        assert response.status_code in [200, 302]
