# main.py

import threading
import queue
from llm import get_llm_output
from tts import speak, stop_speaking
from ui import JarvisUI

from actions.open_app import open_app
from actions.web_search import web_search
from actions.weather_report import weather_action
from actions.send_message import send_message
from actions.system_control import system_control_action

from memory.memory_manager import load_memory, update_memory
from memory.temporary_memory import TemporaryMemory

# ── Global task queue ─────────────────────────────────────────────────────────
task_queue = queue.Queue()


class CommandEngine:
    def __init__(self, ui: JarvisUI):
        self.ui = ui
        self.running = True
        self.session_memory = TemporaryMemory()

        # Start the background task worker
        threading.Thread(target=self._task_worker, daemon=True).start()

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
    ui = JarvisUI(r"MarkX\face.png", size=(900, 900))
    engine = CommandEngine(ui)

    # Text input callback
    ui.set_user_input_callback(lambda text: engine.handle_input(text))

    # Voice input thread — only active when mode == "voice"
    def voice_loop():
        from speech_to_text import record_voice
        while True:
            if ui.get_mode() == "voice":
                ui.write_log("🎙  Listening...")
                text = record_voice()
                if text and text.strip():
                    engine.handle_input(text)
            else:
                # Sleep briefly so we're not hammering the CPU while in text mode
                import time
                time.sleep(0.3)

    threading.Thread(target=voice_loop, daemon=True).start()

    ui.root.mainloop()


if __name__ == "__main__":
    main()
