# tests/test_actions.py

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "MarkX"))

from actions.wiki_lookup import clean_wiki_text
from actions.system_control import system_control_action
from actions.media_player import media_action


class TestActions(unittest.TestCase):
    def test_clean_wiki_text(self):
        dirty = "Albert Einstein [1] was a theoretical physicist [citation needed] born in Germany."
        cleaned = clean_wiki_text(dirty)
        self.assertNotIn("[1]", cleaned)
        self.assertNotIn("[citation needed]", cleaned)
        self.assertIn("Albert Einstein", cleaned)
        self.assertIn("theoretical physicist", cleaned)

    def test_system_control_invalid_command_graceful(self):
        # Should not crash on invalid/unknown command
        res = system_control_action({"command": "nonexistent_subsystem_action"})
        self.assertIn("Sir, I recognized system control command", res)

    def test_media_action_empty_params_graceful(self):
        # Should not crash on empty parameters
        res = media_action({})
        self.assertIn("Sir, what would you like me to play or control?", res)


if __name__ == "__main__":
    unittest.main()
