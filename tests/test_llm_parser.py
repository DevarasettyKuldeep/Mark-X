# tests/test_llm_parser.py

import os
import sys
import unittest

# Ensure MarkX directory is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "MarkX"))

from llm import _extract_json, _error_response


class TestLLMParser(unittest.TestCase):
    def test_clean_json_extraction(self):
        raw = '{"tasks": [{"intent": "chat", "parameters": {}, "text": "Hello, sir."}], "memory_update": null}'
        data = _extract_json(raw)
        self.assertIsNotNone(data)
        self.assertEqual(data["tasks"][0]["intent"], "chat")
        self.assertEqual(data["tasks"][0]["text"], "Hello, sir.")

    def test_markdown_fence_extraction(self):
        raw = """```json
{
  "tasks": [
    {"intent": "system_control", "parameters": {"command": "volume_up"}, "text": "Increasing volume."}
  ],
  "memory_update": null
}
```"""
        data = _extract_json(raw)
        self.assertIsNotNone(data)
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["intent"], "system_control")
        self.assertEqual(data["tasks"][0]["parameters"]["command"], "volume_up")

    def test_extra_chatter_around_json(self):
        raw = """Sure, here is your plan:
{
  "tasks": [
    {"intent": "wiki_lookup", "parameters": {"query": "Nikola Tesla"}, "text": "Looking up Tesla."}
  ]
}
Hope this helps!"""
        data = _extract_json(raw)
        self.assertIsNotNone(data)
        self.assertEqual(data["tasks"][0]["intent"], "wiki_lookup")

    def test_malformed_json_fallback(self):
        raw = "This is just invalid text with no JSON object."
        data = _extract_json(raw)
        self.assertIsNone(data)

    def test_empty_string_extraction(self):
        self.assertIsNone(_extract_json(""))
        self.assertIsNone(_extract_json(None))

    def test_error_response_structure(self):
        err = _error_response("Test error")
        self.assertIn("tasks", err)
        self.assertEqual(err["tasks"][0]["intent"], "chat")
        self.assertEqual(err["tasks"][0]["text"], "Test error")
        self.assertIsNone(err["memory_update"])


if __name__ == "__main__":
    unittest.main()
