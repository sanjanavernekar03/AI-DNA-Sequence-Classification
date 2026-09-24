import unittest
import json
import os
from app import create_app

class TestAuthMultilingual(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        trans_file_path = os.path.join(os.path.dirname(__file__), '../app/static/js/translations.js')
        with open(trans_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        json_str = content[content.find('{'):content.rfind('}')+1]
        self.translations = json.loads(json_str)

        self.auth_keys = [
            'login_page_title',
            'reg_page_title',
            'auto_e812a2',
            'auto_3cb5af',
            'gen_DNAura_6a2b',
            'login_title',
            'gen_sign_in_to_continue_7cd3',
            'login_label_identifier',
            'login_ph_identifier',
            'reg_label_password',
            'login_ph_password',
            'reg_toggle_password',
            'login_remember_me',
            'nav_login',
            'login_no_account',
            'nav_register',
            'gen_create_your_DNAura_82d5',
            'gen_join_us_to_unlock_pe_c8b8',
            'reg_step_1',
            'reg_step_2',
            'gen_health_information_dad9',
            'prof_fullname',
            'reg_ph_full_name',
            'reg_label_username',
            'reg_ph_username',
            'gen_email_ce8a',
            'reg_ph_email',
            'reg_label_phone',
            'reg_ph_phone',
            'gen_address_dd7b',
            'reg_ph_address',
            'reg_label_city',
            'reg_ph_city',
            'reg_label_state',
            'reg_ph_state',
            'reg_label_country',
            'reg_ph_country',
            'reg_label_postal_code',
            'reg_ph_postal',
            'reg_ph_create_pass',
            'reg_label_confirm_password',
            'reg_btn_next',
            'auto_62e53e',
            'gen_blood_group_0bf1',
            'gen_select_blood_group_o_dbec',
            'gen_height_cm_20fb',
            'reg_ph_height',
            'gen_weight_kg_9172',
            'reg_ph_weight',
            'reg_label_dob',
            'reg_label_gender',
            'gen_select_optional_51a6',
            'reg_gender_male',
            'reg_gender_female',
            'reg_gender_other',
            'reg_btn_back',
            'gen_complete_registratio_e3e3',
            'reg_have_account',
            'welcome_sign_in'
        ]
        self.supported_langs = ['en', 'kn', 'hi', 'te', 'ta']

    def test_auth_keys_exist_in_all_5_languages(self):
        """Test that all Login and Register keys exist across all 5 languages."""
        for lang in self.supported_langs:
            for key in self.auth_keys:
                self.assertIn(key, self.translations[lang], f"Key '{key}' missing for language '{lang}'")
                val = self.translations[lang][key]
                self.assertIsNotNone(val)
                self.assertNotEqual(val, "")

    def test_login_route_renders_correctly(self):
        """Test GET /auth/login renders login.html template with data-i18n attributes."""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        self.assertIn('data-i18n="login_page_title"', html)
        self.assertIn('data-i18n="login_title"', html)
        self.assertIn('data-i18n="gen_sign_in_to_continue_7cd3"', html)
        self.assertIn('data-i18n="login_label_identifier"', html)
        self.assertIn('data-i18n-placeholder="login_ph_identifier"', html)
        self.assertIn('data-i18n-placeholder="login_ph_password"', html)
        self.assertIn('data-i18n="login_remember_me"', html)
        self.assertIn('data-i18n="nav_login"', html)
        self.assertIn('data-i18n="login_no_account"', html)

    def test_register_route_renders_correctly(self):
        """Test GET /auth/register renders register.html template with data-i18n attributes."""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        self.assertIn('data-i18n="reg_page_title"', html)
        self.assertIn('data-i18n="gen_create_your_DNAura_82d5"', html)
        self.assertIn('data-i18n="gen_join_us_to_unlock_pe_c8b8"', html)
        self.assertIn('data-i18n="reg_step_1"', html)
        self.assertIn('data-i18n="gen_health_information_dad9"', html)
        self.assertIn('data-i18n-placeholder="reg_ph_full_name"', html)
        self.assertIn('data-i18n-placeholder="reg_ph_username"', html)
        self.assertIn('data-i18n-placeholder="reg_ph_email"', html)
        self.assertIn('data-i18n-placeholder="reg_ph_phone"', html)
        self.assertIn('data-i18n-placeholder="reg_ph_address"', html)
        self.assertIn('data-i18n-placeholder="reg_ph_city"', html)
        self.assertIn('data-i18n-placeholder="reg_ph_state"', html)
        self.assertIn('data-i18n-placeholder="reg_ph_country"', html)
        self.assertIn('data-i18n-placeholder="reg_ph_postal"', html)

if __name__ == '__main__':
    unittest.main()
