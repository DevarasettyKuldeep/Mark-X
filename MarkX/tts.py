# tts.py
#
# pyttsx3's runAndWait() starts an internal event loop that CANNOT be restarted
# in the same process once it ends → "RuntimeError: run loop already started".
# The bulletproof fix: run every TTS call in its own SUBPROCESS.
# Each subprocess is a fresh Python process with no shared engine state.

import subprocess
import sys
import threading

_lock = threading.Lock()          # one utterance at a time
_stop_event = threading.Event()
_current_proc: subprocess.Popen | None = None

# Tiny worker script executed inside the child process
_WORKER = """
import sys, pyttsx3
text = sys.stdin.read()
try:
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.setProperty("volume", 1.0)
    voices = engine.getProperty("voices")
    if voices:
        engine.setProperty("voice", voices[0].id)
    engine.say(text)
    engine.runAndWait()
except Exception as e:
    print(f"TTS error: {e}", file=sys.stderr)
"""


def speak(text: str, block: bool = True) -> None:
    """Speak *text*. block=True waits until done; block=False is fire-and-forget."""
    global _current_proc
    if not text or not text.strip():
        return
    _stop_event.clear()

    def _run():
        global _current_proc
        with _lock:
            if _stop_event.is_set():
                return
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-c", _WORKER],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                _current_proc = proc
                proc.stdin.write(text.encode("utf-8"))
                proc.stdin.close()
                proc.wait()
                _current_proc = None
            except Exception as e:
                print(f"TTS subprocess error: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    if block:
        t.join()


def stop_speaking() -> None:
    """Kill the running TTS subprocess immediately."""
    global _current_proc
    _stop_event.set()
    proc = _current_proc
    if proc and proc.poll() is None:
        proc.kill()


# Legacy alias so old callers using edge_speak() still work
def edge_speak(text: str, ui=None) -> None:
    speak(text, block=False)