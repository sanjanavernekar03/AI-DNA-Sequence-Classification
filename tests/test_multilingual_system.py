import unittest
import json
import os

class TestMultilingualSystem(unittest.TestCase):
    def setUp(self):
        trans_file_path = os.path.join(os.path.dirname(__file__), '../app/static/js/translations.js')
        with open(trans_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse JSON from window.TRANSLATIONS = { ... };
        json_str = content[content.find('{'):content.rfind('}')+1]
        self.translations = json.loads(json_str)
        self.supported_langs = ['en', 'kn', 'hi', 'te', 'ta']

    def test_all_five_languages_exist(self):
        """Test that all 5 required languages (en, kn, hi, te, ta) exist in TRANSLATIONS."""
        for lang in self.supported_langs:
            self.assertIn(lang, self.translations, f"Language '{lang}' missing from TRANSLATIONS")
            self.assertGreater(len(self.translations[lang]), 500, f"Language '{lang}' has insufficient keys")

    def test_key_parity_across_languages(self):
        """Test that every language dictionary has identical key counts and no missing or empty translations."""
        en_keys = set(self.translations['en'].keys())
        for lang in self.supported_langs:
            if lang == 'en':
                continue
            lang_keys = set(self.translations[lang].keys())
            missing_keys = en_keys - lang_keys
            self.assertEqual(len(missing_keys), 0, f"Language '{lang}' is missing keys: {missing_keys}")
            
            # Ensure no keys have empty or null values
            empty_vals = [k for k, v in self.translations[lang].items() if v is None or v == ""]
            self.assertEqual(len(empty_vals), 0, f"Language '{lang}' has empty translation values: {empty_vals}")

    def test_utf8_encoding_and_no_mangled_characters(self):
        """Test that no garbled CP1252 or corrupted characters exist in any language dictionary."""
        mangled_patterns = ['â€”', 'Ã—', 'Ã ', 'â€', 'Ã©']
        for lang in self.supported_langs:
            dict_str = json.dumps(self.translations[lang], ensure_ascii=False)
            for pattern in mangled_patterns:
                self.assertNotIn(pattern, dict_str, f"Found mangled character pattern '{pattern}' in language '{lang}'")

if __name__ == '__main__':
    unittest.main()
