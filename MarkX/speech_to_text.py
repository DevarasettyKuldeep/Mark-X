# speech_to_text.py
#
# Improvements over the original:
#  - Voice Activity Detection (VAD): recording stops automatically after
#    silence, so you don't have to wait for a fixed 5-second window.
#  - Configurable silence threshold and max recording time.
#  - Cancellable via a threading.Event so the voice loop can stop it cleanly.
#  - Device index loaded from .env (AUDIO_INPUT_DEVICE) so you don't have to
#    hard-code it.

import os
import threading
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
SAMPLE_RATE       = 16_000
MODEL_SIZE        = os.getenv("WHISPER_MODEL", "small")
LANGUAGE          = os.getenv("WHISPER_LANG", "en")
MAX_SECONDS       = int(os.getenv("MAX_RECORD_SECONDS", "10"))
SILENCE_THRESHOLD = float(os.getenv("SILENCE_THRESHOLD", "0.01"))  # RMS
SILENCE_DURATION  = float(os.getenv("SILENCE_DURATION", "1.2"))    # seconds

_device_env = os.getenv("AUDIO_INPUT_DEVICE")
INPUT_DEVICE = int(_device_env) if _device_env is not None else None  # None = system default

# ── Load model once ───────────────────────────────────────────────────────────
print(f"Loading Whisper model ({MODEL_SIZE})...")
_model = WhisperModel(MODEL_SIZE, compute_type="int8")
print("Whisper model ready.")

# Global cancel flag — set this from outside to abort a recording
cancel_flag = threading.Event()


def record_voice(prompt: str = "Listening, sir...") -> str:
    """
    Record from the microphone until silence is detected or MAX_SECONDS is
    reached, then transcribe with Whisper.

    Returns the transcribed string (empty string if nothing was heard or
    the recording was cancelled).
    """
    print(prompt)
    cancel_flag.clear()

    chunk_size = int(SAMPLE_RATE * 0.1)   # 100 ms chunks
    silence_chunks_needed = int(SILENCE_DURATION / 0.1)

    frames: list[np.ndarray] = []
    silent_chunks = 0
    max_chunks = int(MAX_SECONDS / 0.1)

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=INPUT_DEVICE,
            blocksize=chunk_size,
        ) as stream:
            for _ in range(max_chunks):
                if cancel_flag.is_set():
                    print("Recording cancelled.")
                    return ""

                chunk, _ = stream.read(chunk_size)
                frames.append(chunk.copy())

                rms = float(np.sqrt(np.mean(chunk ** 2)))
                if rms < SILENCE_THRESHOLD:
                    silent_chunks += 1
                    if silent_chunks >= silence_chunks_needed and len(frames) > silence_chunks_needed:
                        break  # natural end of speech
                else:
                    silent_chunks = 0

    except Exception as e:
        print(f"Microphone error: {e}")
        return ""

    if not frames:
        return ""

    audio = np.concatenate(frames, axis=0).squeeze()

    # Skip transcription if the entire recording is silence
    if float(np.sqrt(np.mean(audio ** 2))) < SILENCE_THRESHOLD:
        print("No speech detected (silence only).")
        return ""

    try:
        segments, _ = _model.transcribe(
            audio,
            language=LANGUAGE,
            beam_size=5,
            vad_filter=True,         # built-in VAD pass
        )
        text = " ".join(seg.text for seg in segments).strip()
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""

    if text:
        print(f"You: {text}")
    else:
        print("No speech detected.")

    return text
