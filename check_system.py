#!/usr/bin/env python3
# check_system.py
#
# Mark-X Pre-flight System Diagnostic Tool
# Verifies environment, dependencies, audio hardware, assets, and API configuration.

import os
import sys

def print_status(component: str, ok: bool, details: str = ""):
    symbol = "+" if ok else "x"
    status_str = "OK  " if ok else "FAIL"
    print(f"[{symbol}] {component:<26} : {status_str} {details}")


def check_python_version() -> bool:
    v = sys.version_info
    ver_str = f"{v.major}.{v.minor}.{v.micro}"
    is_ok = v.major == 3 and v.minor >= 10
    print_status("Python Version", is_ok, f"({ver_str})")
    return is_ok


def check_dependencies() -> bool:
    modules = [
        ("requests", "HTTP API client"),
        ("dotenv", "Environment variable loader"),
        ("sounddevice", "Audio recording and playback"),
        ("soundfile", "WAV/Audio buffer processor"),
        ("pyautogui", "Desktop UI automation"),
        ("PIL", "Pillow image processing"),
        ("edge_tts", "Neural text-to-speech"),
        ("wikipedia", "Wikipedia encyclopedia lookup"),
        ("pyttsx3", "Offline fallback speech engine"),
    ]

    all_ok = True
    print("\n--- Dependencies ---")
    for mod_name, desc in modules:
        try:
            __import__(mod_name)
            print_status(mod_name, True, f"({desc})")
        except ImportError:
            print_status(mod_name, False, f"MISSING ({desc})")
            all_ok = False
    return all_ok


def check_audio_devices() -> bool:
    print("\n--- Audio Hardware ---")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_count = sum(1 for d in devices if d.get("max_input_channels", 0) > 0)
        output_count = sum(1 for d in devices if d.get("max_output_channels", 0) > 0)

        print_status("Microphone Inputs", input_count > 0, f"({input_count} detected)")
        print_status("Audio Outputs", output_count > 0, f"({output_count} detected)")
        return input_count > 0 and output_count > 0
    except Exception as e:
        print_status("Audio Query", False, f"({e})")
        return False


def check_configuration_and_assets() -> bool:
    print("\n--- Configuration & Assets ---")
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Check .env
    env_path = os.path.join(base_dir, ".env")
    env_exists = os.path.exists(env_path)
    print_status(".env File", env_exists, f"({'Found' if env_exists else 'Create via: copy .env.example .env'})")

    api_key_set = False
    if env_exists:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
        api_key_set = bool(key and key != "your_openrouter_api_key_here")
        print_status("OpenRouter API Key", api_key_set, f"({'Configured' if api_key_set else 'Not configured or placeholder'})")

    # Check assets
    face_path = os.path.join(base_dir, "MarkX", "face.png")
    face_exists = os.path.exists(face_path)
    print_status("Mark-X Avatar Asset", face_exists, f"({'Found' if face_exists else 'Missing MarkX/face.png'})")

    prompt_path = os.path.join(base_dir, "core", "prompt.txt")
    prompt_exists = os.path.exists(prompt_path)
    print_status("System Prompt Rules", prompt_exists, f"({'Found' if prompt_exists else 'Missing core/prompt.txt'})")

    minimal_ui_path = os.path.join(base_dir, "MarkX", "minimal_ui.py")
    minimal_ui_exists = os.path.exists(minimal_ui_path)
    print_status("Minimal Workspace UI", minimal_ui_exists, f"({'Found' if minimal_ui_exists else 'Missing MarkX/minimal_ui.py'})")

    return env_exists and face_exists and prompt_exists and minimal_ui_exists


def main():
    print("=" * 60)
    print("      M A R K - X  Pre-flight System Diagnostics")
    print("=" * 60)

    py_ok = check_python_version()
    deps_ok = check_dependencies()
    audio_ok = check_audio_devices()
    cfg_ok = check_configuration_and_assets()

    print("\n" + "=" * 60)
    if py_ok and deps_ok and audio_ok and cfg_ok:
        print("[+] System status: READY. Launch with: python MarkX/main.py")
        print("=" * 60)
        sys.exit(0)
    else:
        print("[!] System status: WARNING or INCOMPLETE configuration.")
        print("    Review any items marked [x] above.")
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()
