import pytest
from app import create_app
from app.services.voice_assistant_service import process_voice_assistant_command, _match_deterministic_rules

@pytest.fixture
def app_ctx():
    app = create_app()
    with app.app_context():
        yield app

def test_navigation_intents(app_ctx):
    assert _match_deterministic_rules("open dashboard") == 'OPEN_DASHBOARD'
    assert _match_deterministic_rules("open complete analysis") == 'OPEN_COMPLETE_ANALYSIS'
    assert _match_deterministic_rules("कम्प्लीट एनालिसिस खोलो") in ['OPEN_COMPLETE_ANALYSIS', 'RUN_COMPLETE_ANALYSIS']
    assert _match_deterministic_rules("ಕಂಪ್ಲೀಟ್ ಅನಾಲಿಸಿಸ್ ತೆರೆಯಿರಿ") in ['OPEN_COMPLETE_ANALYSIS', 'RUN_COMPLETE_ANALYSIS']
    assert _match_deterministic_rules("open similarity analysis") == 'OPEN_SIMILARITY'
    assert _match_deterministic_rules("open mutation analysis") == 'OPEN_MUTATION'
    assert _match_deterministic_rules("open disease prediction") == 'OPEN_DISEASE_PREDICTION'
    assert _match_deterministic_rules("open health guide") == 'OPEN_HEALTH_GUIDANCE'
    assert _match_deterministic_rules("open diet planner") in ['OPEN_DIET_PLANNER', 'CREATE_DIET_PLAN']
    assert _match_deterministic_rules("open hospitals") in ['OPEN_HOSPITALS', 'FIND_HOSPITAL']
    assert _match_deterministic_rules("open my appointments") == 'OPEN_APPOINTMENTS'
    assert _match_deterministic_rules("open reports") == 'OPEN_REPORTS'

def test_action_intents(app_ctx):
    res = process_voice_assistant_command("perform complete dna analysis", current_page="/dashboard/", language="en")
    assert res['intent'] == 'RUN_COMPLETE_ANALYSIS'
    assert res['action'] == 'NAVIGATE'
    assert res['navigate_url'] == '/analysis/complete/'

    res_on_page = process_voice_assistant_command("perform complete dna analysis", current_page="/analysis/complete/", language="en")
    assert res_on_page['intent'] == 'RUN_COMPLETE_ANALYSIS'
    assert res_on_page['action'] == 'RUN_PAGE_ANALYSIS'

def test_confirmation_sensitive_actions(app_ctx):
    res_book = process_voice_assistant_command("book an appointment with Dr. Alexander Wright at Manipal Hospital", language="en")
    assert res_book['intent'] == 'BOOK_APPOINTMENT'
    assert res_book['action'] == 'ASK_CONFIRMATION'
    assert res_book['requires_confirmation'] is True

    res_logout = process_voice_assistant_command("logout of my account", language="en")
    assert res_logout['intent'] == 'LOGOUT'
    assert res_logout['action'] == 'ASK_CONFIRMATION'
    assert res_logout['requires_confirmation'] is True

def test_theme_and_language_intents(app_ctx):
    res_theme = process_voice_assistant_command("switch to dark mode", language="en")
    assert res_theme['intent'] == 'CHANGE_THEME'
    assert res_theme['action'] == 'CHANGE_THEME'
    assert res_theme['theme'] == 'dark'

    res_lang = process_voice_assistant_command("change language to hindi", language="en")
    assert res_lang['intent'] == 'CHANGE_LANGUAGE'
    assert res_lang['action'] == 'CHANGE_LANGUAGE'
    assert res_lang['target_language'] == 'hi'

def test_settings_and_profile_intents(app_ctx):
    res_prof = process_voice_assistant_command("open my profile", language="en")
    assert res_prof['intent'] == 'OPEN_PROFILE'
    assert res_prof['action'] == 'NAVIGATE'
    assert res_prof['navigate_url'] == '/auth/profile'

def test_recommendation_intents(app_ctx):
    res_hosp = process_voice_assistant_command("find a hospital for diabetes in Bangalore", language="en")
    assert res_hosp['intent'] == 'FIND_HOSPITAL'
    assert res_hosp['action'] == 'SHOW_RECOMMENDATION'
    assert "Apollo Hospital" in res_hosp['response'] or "Manipal" in res_hosp['response'] or "Diabetes" in res_hosp['response'] or "Bangalore" in res_hosp['response']

def test_multilingual_commands(app_ctx):
    for lang in ['en', 'hi', 'kn', 'ta', 'te']:
        res = process_voice_assistant_command("open complete analysis", language=lang)
        assert res['intent'] == 'OPEN_COMPLETE_ANALYSIS'
        assert res['action'] == 'NAVIGATE'
        assert res['navigate_url'] == '/analysis/complete/'


