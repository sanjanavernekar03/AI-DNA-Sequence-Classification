import pytest
import json
import re
from app import create_app

def get_translations():
    with open("app/static/js/translations.js", "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'window\.TRANSLATIONS\s*=\s*(\{[\s\S]*\});', content)
    assert match, "Could not parse window.TRANSLATIONS from translations.js"
    return json.loads(match.group(1))

LANGUAGES = ["en", "hi", "kn", "ta", "te"]
DYNAMIC_TEST_USERS = [
    {"user_id": 1, "username": "raju", "full_name": "Raju", "email": "raju@example.com"},
    {"user_id": 2, "username": "sanjana", "full_name": "Sanjana", "email": "sanjana@example.com"},
    {"user_id": 3, "username": "rahul", "full_name": "Rahul", "email": "rahul@example.com"},
    {"user_id": 4, "username": "ananya", "full_name": "Ananya", "email": "ananya@example.com"},
    {"user_id": 5, "username": "priya", "full_name": "Priya", "email": "priya@example.com"},
    {"user_id": 6, "username": "arun", "full_name": "Arun", "email": "arun@example.com"}
]

def test_greeting_multilingual_and_dynamic_users():
    translations = get_translations()
    app = create_app()

    for user in DYNAMIC_TEST_USERS:
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = user['user_id']
                sess['username'] = user['username']
                sess['full_name'] = user['full_name']
                sess['email'] = user['email']

            res = client.get('/dashboard/')
            assert res.status_code == 200
            html = res.get_data(as_text=True)

            # 1. Verify user's name is dynamically rendered in HTML with data-user-name attribute matching the current logged-in user
            assert f'data-user-name="{user["full_name"]}"' in html, f"User full name attribute data-user-name=\"{user['full_name']}\" missing in rendered HTML"

            # 2. Verify data-i18n attribute for time-based greeting is present
            match = re.search(r'<span\s+data-i18n="(gen_greeting_\w+)">([^<]+)</span>', html)
            assert match, "Greeting span with data-i18n not found in HTML"

            greeting_key = match.group(1)
            assert greeting_key in ["gen_greeting_morning", "gen_greeting_afternoon", "gen_greeting_evening", "gen_greeting_night"]

            # 3. Verify that all 5 languages have valid translated strings for the greeting prefix
            for lang in LANGUAGES:
                assert lang in translations, f"Language {lang} missing in translations"
                assert greeting_key in translations[lang], f"Key {greeting_key} missing in {lang}"
                translated_prefix = translations[lang][greeting_key]
                assert translated_prefix, f"Empty translation for {greeting_key} in {lang}"

def test_no_hardcoded_name_dictionaries_in_javascript():
    with open("app/static/js/language.js", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify no NAME_TRANSLITERATIONS dictionary exists
    assert "NAME_TRANSLITERATIONS" not in content, "Found hardcoded NAME_TRANSLITERATIONS dictionary in language.js"
    assert "if (name == \"Raju\")" not in content, "Found special-case hardcoded check for Raju"
    assert "if (username == \"Raju\")" not in content, "Found special-case hardcoded check for Raju"

def test_no_hardcoded_names_in_translation_dictionaries():
    translations = get_translations()
    for lang in LANGUAGES:
        for key, val in translations[lang].items():
            if key.startswith("gen_greeting_"):
                assert "Raju" not in val, f"User name hardcoded into translation key '{key}' for '{lang}'"
