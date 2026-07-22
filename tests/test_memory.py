# tests/test_memory.py

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "MarkX"))

from memory.temporary_memory import TemporaryMemory
from memory.memory_manager import _empty_memory, _recursive_update


class TestTemporaryMemory(unittest.TestCase):
    def setUp(self):
        self.mem = TemporaryMemory(max_history=3)

    def test_history_sliding_window(self):
        self.mem.set_last_user_text("Hello 1")
        self.mem.set_last_ai_response("Reply 1")
        self.mem.set_last_user_text("Hello 2")
        self.mem.set_last_ai_response("Reply 2")

        # History max is 3 items
        self.assertLessEqual(len(self.mem.conversation_history), 3)
        prompt_hist = self.mem.get_history_for_prompt()
        self.assertIn("Reply 2", prompt_hist)
        self.assertNotIn("Hello 1", prompt_hist)

    def test_parameter_storage(self):
        self.mem.update_parameters({"city": "London", "units": "metric"})
        self.assertEqual(self.mem.get_parameter("city"), "London")
        self.assertEqual(self.mem.get_parameter("units"), "metric")

    def test_action_memory(self):
        self.mem.set_open_app("notepad")
        self.assertEqual(self.mem.get_last_opened_app(), "notepad")

        self.mem.set_last_search("quantum computing", "A branch of physics...")
        last_s = self.mem.get_last_search()
        self.assertEqual(last_s["query"], "quantum computing")

    def test_reset(self):
        self.mem.set_open_app("calc")
        self.mem.update_parameters({"temp": "high"})
        self.mem.reset()
        self.assertIsNone(self.mem.get_last_opened_app())
        self.assertEqual(self.mem.get_parameters(), {})


class TestMemoryManager(unittest.TestCase):
    def test_empty_structure(self):
        empty = _empty_memory()
        self.assertIn("identity", empty)
        self.assertIn("preferences", empty)
        self.assertIn("relationships", empty)
        self.assertIn("emotional_state", empty)

    def test_recursive_update_new_field(self):
        base = {"preferences": {"theme": {"value": "dark"}}}
        update = {"preferences": {"volume": 80}}
        changed = _recursive_update(base, update)
        self.assertTrue(changed)
        self.assertIn("volume", base["preferences"])
        self.assertEqual(base["preferences"]["volume"]["value"], 80)
        # Verify original theme is preserved
        self.assertEqual(base["preferences"]["theme"]["value"], "dark")

    def test_recursive_update_empty_ignored(self):
        base = {"preferences": {"color": {"value": "blue"}}}
        update = {"preferences": {"color": ""}}
        changed = _recursive_update(base, update)
        self.assertFalse(changed)
        self.assertEqual(base["preferences"]["color"]["value"], "blue")


if __name__ == "__main__":
    unittest.main()
