# tests/test_ui.py

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "MarkX"))

from minimal_ui import MinimalUI
from ui import JarvisUI


class TestUIInterfaces(unittest.TestCase):
    def setUp(self):
        self.face_path = os.path.join(BASE_DIR, "MarkX", "face.png")

    def test_minimal_ui_creation_and_methods(self):
        ui = MinimalUI(self.face_path)
        ui.root.withdraw()  # keep hidden during test

        # Check default state
        self.assertEqual(ui.get_mode(), "text")
        self.assertIn("Ask Mark-X anything", ui.input_box.get())

        # Test toast logging without chat clutter
        ui.write_log("You: Hello Mark-X")
        self.assertEqual(ui.toast_var.get(), "You: Hello Mark-X")

        ui.write_log("Mark-X: Good day, sir.")
        self.assertEqual(ui.toast_var.get(), "Mark-X: Good day, sir.")

        # Test mode toggle
        ui._toggle_mode()
        self.assertEqual(ui.get_mode(), "voice")
        ui._toggle_mode()
        self.assertEqual(ui.get_mode(), "text")

        # Test switch callback
        switched = []
        ui.set_switch_ui_callback(lambda: switched.append(True))
        ui._on_switch_to_full()
        self.assertTrue(switched[0])

        ui.root.destroy()

    def test_jarvis_ui_creation_and_callbacks(self):
        ui = JarvisUI(self.face_path)
        ui.root.withdraw()

        # Check default state
        self.assertEqual(ui.get_mode(), "text")

        # Test switch callback
        switched = []
        ui.set_switch_ui_callback(lambda: switched.append(True))
        ui._on_switch_to_minimal()
        self.assertTrue(switched[0])

        # Test clear log
        ui.write_log("Test message")
        ui.clear_log()
        self.assertEqual(len(ui.typing_queue), 0)

        ui.root.destroy()


if __name__ == "__main__":
    unittest.main()
