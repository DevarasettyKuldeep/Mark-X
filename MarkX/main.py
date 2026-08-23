# main.py

import os
import sys
import time
import threading
import queue
from llm import get_llm_output
from tts import speak, stop_speaking
from ui import JarvisUI
from minimal_ui import MinimalUI

from actions.open_app import open_app
from actions.web_search import web_search
from actions.weather_report import weather_action
from actions.send_message import send_message
from actions.system_control import system_control_action
from actions.media_player import media_action
from actions.wiki_lookup import wiki_action

from memory.memory_manager import load_memory, update_memory
from memory.temporary_memory import TemporaryMemory

# ── Global task queue ─────────────────────────────────────────────────────────
task_queue = queue.Queue()


class CommandEngine:
    def __init__(self, ui):
        self.ui = ui
        self.running = True
        self.session_memory = TemporaryMemory()

        # Start the background task worker
        threading.Thread(target=self._task_worker, daemon=True).start()

    def set_ui(self, ui):
        """Update active UI target when switching interface modes."""
        self.ui = ui

    # ── Input handler ─────────────────────────────────────────────────────────
    def handle_input(self, text: str):
        text = text.strip()
        if not text:
            return

        self.session_memory.set_last_user_text(text)
        self.ui.write_log(f"You: {text}")
        self.ui.set_thinking(True)

        # Run LLM call in background so the UI stays responsive
        threading.Thread(
            target=self._process_input, args=(text,), daemon=True
        ).start()

    def _process_input(self, text: str):
        try:
            memory = load_memory()
            result = get_llm_output(
                text,
                memory_block=memory,
                conversation_history=self.session_memory.get_history_for_prompt()
            )
        except Exception as e:
            self.ui.set_thinking(False)
            self.ui.write_log(f"[Error] LLM call failed: {e}")
            return

        self.ui.set_thinking(False)

        # Persist any memory updates returned by the LLM
        memory_update = result.get("memory_update")
        if memory_update and isinstance(memory_update, dict):
            try:
                update_memory(memory_update)
            except Exception as e:
                print(f"Memory update failed: {e}")

        tasks = result.get("tasks", [])
        if not tasks:
            self.ui.write_log("[Mark-X] No tasks generated.")
            return

        for task in tasks:
            task_queue.put(task)

    # ── Task worker ───────────────────────────────────────────────────────────
    def _task_worker(self):
        while self.running:
            try:
                task = task_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self._execute_task(task)
            except Exception as e:
                self.ui.write_log(f"[Error] Task execution failed: {e}")
                print(f"Task error: {e}")
            finally:
                task_queue.task_done()

    def _execute_task(self, task: dict):
        intent = task.get("intent", "chat")
        parameters = task.get("parameters", {})
        response_text = task.get("text", "")

        intent_aliases = {
            "weather": "weather_report",
            "search_web": "search",
            "open_application": "open_app",
            "play_music": "play_media",
            "media": "play_media",
            "media_control": "play_media",
            "wiki": "wiki_lookup",
            "wikipedia": "wiki_lookup",
        }
        intent = intent_aliases.get(intent, intent)

        if intent == "send_message":
            parameters = dict(parameters)
            if "contact" not in parameters and "receiver" in parameters:
                parameters["contact"] = parameters["receiver"]
            if "message" not in parameters and "message_text" in parameters:
                parameters["message"] = parameters["message_text"]

        if intent == "open_app":
            open_app(
                parameters=parameters,
                response=response_text,
                player=self.ui,
                session_memory=self.session_memory,
            )

        elif intent == "search":
            web_search(
                parameters=parameters,
                player=self.ui,
                session_memory=self.session_memory,
            )

        elif intent == "system_control":
            system_control_action(
                parameters=parameters,
                player=self.ui,
                session_memory=self.session_memory,
            )

        elif intent == "play_media":
            media_action(
                parameters=parameters,
                player=self.ui,
                session_memory=self.session_memory,
            )

        elif intent == "wiki_lookup":
            wiki_action(
                parameters=parameters,
                player=self.ui,
                session_memory=self.session_memory,
            )

        elif intent == "weather_report":
            weather_action(
                parameters=parameters,
                player=self.ui,
                session_memory=self.session_memory,
            )

        elif intent == "send_message":
            send_message(
                parameters=parameters,
                player=self.ui,
                session_memory=self.session_memory,
            )

        else:  # "chat" or anything unrecognised
            if response_text:
                self.session_memory.set_last_ai_response(response_text)
                self.ui.write_log(f"Mark-X: {response_text}")
                self.ui.start_speaking()
                speak(response_text)
                self.ui.stop_speaking()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_faces = [
        os.path.join(base_dir, "face.png"),
        os.path.join(base_dir, "MarkX", "face.png"),
        r"MarkX\face.png",
    ]
    face_path = next((p for p in candidate_faces if os.path.exists(p)), r"MarkX\face.png")

    # CLI flag detection: --minimal / -m or --hud / --full
    default_env_ui = os.getenv("DEFAULT_UI", "full").lower().strip()
    start_minimal = (
        "--minimal" in sys.argv
        or "-m" in sys.argv
        or (default_env_ui in ("minimal", "workspace") and "--full" not in sys.argv and "--hud" not in sys.argv)
    )

    app_state = {
        "active_ui": None,
        "engine": None,
        "voice_thread_started": False,
        "mode": "minimal" if start_minimal else "full",
    }

    def launch_ui(target_mode: str):
        old_ui = app_state["active_ui"]
        if old_ui and hasattr(old_ui, "root"):
            try:
                old_ui.root.destroy()
            except Exception:
                pass

        app_state["mode"] = target_mode
        if target_mode == "minimal":
            ui = MinimalUI(face_path)
            ui.set_switch_ui_callback(lambda: launch_ui("full"))
        else:
            ui = JarvisUI(face_path)
            ui.set_switch_ui_callback(lambda: launch_ui("minimal"))

        app_state["active_ui"] = ui

        if app_state["engine"] is None:
            app_state["engine"] = CommandEngine(ui)
        else:
            app_state["engine"].set_ui(ui)

        engine = app_state["engine"]
        ui.set_user_input_callback(lambda text: engine.handle_input(text))

        # Start persistent voice listening worker
        if not app_state["voice_thread_started"]:
            app_state["voice_thread_started"] = True

            def voice_loop():
                from speech_to_text import record_voice
                while True:
                    curr_ui = app_state.get("active_ui")
                    if curr_ui and hasattr(curr_ui, "get_mode") and curr_ui.get_mode() == "voice":
                        curr_ui.write_log("🎙 Listening...")
                        text = record_voice()
                        if text and text.strip():
                            engine.handle_input(text)
                    else:
                        time.sleep(0.3)

            threading.Thread(target=voice_loop, daemon=True).start()

        ui.root.mainloop()

    launch_ui("minimal" if start_minimal else "full")


if __name__ == "__main__":
    main()
