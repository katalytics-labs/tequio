import unittest
from normalizer import normalize_label

class Labels(unittest.TestCase):
    def test_whitespace(self):
        self.assertEqual(normalize_label('  north\t wall\n'), 'north wall')
    def test_unicode(self):
        self.assertEqual(normalize_label('  muro   norte — 東京  '), 'muro norte — 東京')
    def test_empty(self):
        for value in ['', ' \t\n']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_label(value)
    def test_non_text(self):
        for value in [None, 42, True, b'label']:
            with self.subTest(value=value), self.assertRaises(TypeError):
                normalize_label(value)
