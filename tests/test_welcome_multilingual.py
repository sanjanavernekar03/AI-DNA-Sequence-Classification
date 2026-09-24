import unittest
import json
import os
from app import create_app

class TestWelcomeMultilingual(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        trans_file_path = os.path.join(os.path.dirname(__file__), '../app/static/js/translations.js')
        with open(trans_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        json_str = content[content.find('{'):content.rfind('}')+1]
        self.translations = json.loads(json_str)
        self.welcome_keys = [
            'welcome_page_title',
            'gen_genovaix_6a2b',
            'app_title_dnaura',
            'auto_2ee346',
            'gen_ai_powered_genetic_a_c9d4',
            'gen_explore_dna_sequence_18ee',
            'welcome_open_dashboard',
            'welcome_sign_in',
            'nav_login',
            'nav_register',
            'auto_f83d80',
            'auto_473955',
            'auto_7fa27a',
            'auto_f759fe',
            'auto_9a6893',
            'auto_a7d7b5',
            'auto_55c29e',
            'auto_8729c9'
        ]
        self.supported_langs = ['en', 'kn', 'hi', 'te', 'ta']

    def test_welcome_keys_exist_in_all_5_languages(self):
        """Test that all Welcome Page keys exist across all 5 languages."""
        for lang in self.supported_langs:
            for key in self.welcome_keys:
                self.assertIn(key, self.translations[lang], f"Key '{key}' missing for language '{lang}'")
                val = self.translations[lang][key]
                self.assertIsNotNone(val)
                self.assertNotEqual(val, "")

    def test_welcome_translations_are_native_script(self):
        """Test that non-English languages contain native script translations (no untranslated English text)."""
        english_only_keys = ['welcome_page_title', 'auto_2ee346', 'gen_ai_powered_genetic_a_c9d4', 'gen_explore_dna_sequence_18ee', 'auto_f83d80', 'auto_473955', 'auto_7fa27a']
        for lang in ['kn', 'hi', 'te', 'ta']:
            for key in english_only_keys:
                en_val = self.translations['en'][key]
                lang_val = self.translations[lang][key]
                self.assertNotEqual(en_val, lang_val, f"Key '{key}' in language '{lang}' is untranslated English! Value: {lang_val}")

    def test_welcome_page_route_renders_correctly(self):
        """Test that GET / renders welcome.html template cleanly with data-i18n tags."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Verify essential data-i18n attributes exist in HTML
        self.assertIn('data-i18n="welcome_page_title"', html)
        self.assertIn('data-i18n="gen_genovaix_6a2b"', html)
        self.assertIn('data-i18n="auto_2ee346"', html)
        self.assertIn('data-i18n="gen_ai_powered_genetic_a_c9d4"', html)
        self.assertIn('data-i18n="gen_explore_dna_sequence_18ee"', html)
        self.assertIn('data-i18n="auto_f83d80"', html)
        self.assertIn('data-i18n="auto_473955"', html)
        self.assertIn('data-i18n="auto_7fa27a"', html)

if __name__ == '__main__':
    unittest.main()
