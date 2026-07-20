# tts.py
#
# Unified Text-to-Speech Engine for Mark-X:
# - Primary: Microsoft Edge Neural TTS (high-fidelity natural voices)
# - Fallback: pyttsx3 in dedicated subprocess (zero-latency offline support)
# - Synchronized UI speaking state and interruptible playback

import io
import os
import sys
import asyncio
import threading
import subprocess
from dotenv import load_dotenv

load_dotenv()

TTS_ENGINE = os.getenv("TTS_ENGINE", "edge").lower().strip()
TTS_VOICE  = os.getenv("TTS_VOICE", "en-US-ChristopherNeural").strip()
TTS_RATE   = os.getenv("TTS_RATE", "+0%").strip()
TTS_VOLUME = os.getenv("TTS_VOLUME", "+0%").strip()
TTS_PITCH  = os.getenv("TTS_PITCH", "+0Hz").strip()

_lock = threading.Lock()
_stop_event = threading.Event()
_current_proc: subprocess.Popen | None = None

_PYTTSX3_WORKER = """
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


def _pyttsx3_speak_internal(text: str, ui=None):
    """Fallback offline TTS using pyttsx3 in an isolated child process."""
    global _current_proc
    if _stop_event.is_set():
        return

    if ui:
        try:
            ui.start_speaking()
        except Exception:
            pass

    try:
        proc = subprocess.Popen(
            [sys.executable, "-c", _PYTTSX3_WORKER],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        _current_proc = proc
        proc.stdin.write(text.encode("utf-8"))
        proc.stdin.close()
        proc.wait()
    except Exception as e:
        print(f"pyttsx3 error: {e}")
    finally:
        _current_proc = None
        if ui:
            try:
                ui.stop_speaking()
            except Exception:
                pass


async def _stream_edge_tts(text: str):
    """Fetch audio stream from edge-tts and stream to sounddevice output."""
    import edge_tts
    import sounddevice as sd
    import soundfile as sf

    communicate = edge_tts.Communicate(
        text=text.strip(),
        voice=TTS_VOICE,
        rate=TTS_RATE,
        volume=TTS_VOLUME,
        pitch=TTS_PITCH,
    )

    audio_bytes = io.BytesIO()
    async for chunk in communicate.stream():
        if _stop_event.is_set():
            return
        if chunk.get("type") == "audio":
            audio_bytes.write(chunk["data"])

    if _stop_event.is_set():
        return

    audio_bytes.seek(0)
    data, samplerate = sf.read(audio_bytes, dtype="float32")
    channels = data.shape[1] if len(data.shape) > 1 else 1

    with sd.OutputStream(samplerate=samplerate, channels=channels, dtype="float32") as stream:
        block_size = 1024
        for start in range(0, len(data), block_size):
            if _stop_event.is_set():
                break
            stream.write(data[start:start + block_size])


def _edge_speak_internal(text: str, ui=None):
    """Execute Edge TTS audio playback, with automatic fallback to pyttsx3."""
    if _stop_event.is_set():
        return

    if ui:
        try:
            ui.start_speaking()
        except Exception:
            pass

    try:
        asyncio.run(_stream_edge_tts(text))
    except Exception as e:
        print(f"Edge TTS failed ({e}), falling back to pyttsx3 offline voice...")
        _pyttsx3_speak_internal(text, ui=ui)
    finally:
        if ui:
            try:
                ui.stop_speaking()
            except Exception:
                pass


def speak(text: str, block: bool = True, ui=None) -> None:
    """
    Speak text using configured TTS engine.
    block=True waits until finished; block=False runs in a background thread.
    """
    if not text or not text.strip():
        return

    _stop_event.clear()

    def _worker():
        with _lock:
            if _stop_event.is_set():
                return
            if TTS_ENGINE == "edge":
                _edge_speak_internal(text, ui=ui)
            else:
                _pyttsx3_speak_internal(text, ui=ui)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    if block:
        t.join()


def stop_speaking() -> None:
    """Immediately stop audio playback and terminate any running TTS process."""
    global _current_proc
    _stop_event.set()
    proc = _current_proc
    if proc and proc.poll() is None:
        try:
            proc.kill()
        except Exception:
            pass


def edge_speak(text: str, ui=None, block: bool = False) -> None:
    """Backward-compatible caller interface."""
    speak(text, block=block, ui=ui)