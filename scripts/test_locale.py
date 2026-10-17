#!/usr/bin/env python3
import unittest
from check_locale import normalize

class LocaleTests(unittest.TestCase):
    def test_simplified_characters(self):
        self.assertEqual(normalize('\u4f01\u4e1a\u6301\u7eed\u66f4\u65b0\u65b0\u95fb'), '企業持續更新新聞')
    def test_taiwan_terms(self):
        self.assertEqual(normalize('\u751f\u547d\u5468\u671f\u548c\u6578\u64da\u5eab'), '生命週期和資料庫')
    def test_keep_shared_words(self):
        text = '演算法、資產配置、物理質量、干擾、台灣、NVIDIA、vLLM、42B、15%'
        self.assertEqual(normalize(text), text)
        self.assertEqual(normalize(normalize(text)), text)
    def test_keep_urls_and_identifiers(self):
        text = 'https://example.com/\u65b0\u95fb?mode=dark model_id=Qwen3 api/v1'
        self.assertEqual(normalize(text), text)
    def test_idempotence(self):
        text = '\u8abf\u7528\u7b97\u6cd5\u548c\u914d\u7f6e\u6587\u4ef6'
        once = normalize(text)
        self.assertEqual(normalize(once), once)

if __name__ == '__main__':
    unittest.main()
