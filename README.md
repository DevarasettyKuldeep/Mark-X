# Mark-X

Mark-X is a Python desktop AI assistant for Windows. It combines a Tkinter interface, voice input, neural text-to-speech, LLM-based task planning, multi-turn session memory, system controls, and extensible action modules for desktop automation.

## Features

- **Cyber-HUD Desktop UI**: Animated glowing HUD avatar with real-time status badges (`ONLINE | IDLE`, `LISTENING`, `THINKING`, `SPEAKING`).
- **Interactive Hotkeys**:
  - `Esc`: Instantly interrupt and stop assistant speech.
  - `Ctrl+L`: Clear conversation log.
  - `Ctrl+M`: Quick toggle between Voice mode and Text mode.
- **Dual Text & Voice Input**: Real-time microphone capture with voice activity detection (faster-whisper) and direct text input.
- **Neural Text-to-Speech**: High-fidelity Microsoft Edge Neural TTS with automatic offline `pyttsx3` subprocess fallback.
- **Conversational Session Memory**: Multi-turn context awareness enabling pronouns and natural follow-up queries.
- **Desktop System Controls**: Native Windows volume adjustment, timestamped screenshot capture, battery status queries, and screen locking.
- **Media Playback**: Play songs and videos directly on YouTube and control media playback (play/pause, next track, stop).
- **Wikipedia Knowledge Lookup**: Rapid, concise encyclopedic summaries without browser clutter.
- **Web & Nearby Search**: SerpAPI integration with graceful Google Search and Google Maps browser fallback.
- **App Launcher**: Instant opening of Windows desktop applications.
- **Pre-flight Diagnostics**: Built-in environment and hardware readiness tool (`check_system.py`).
- **Automated Test Suite**: Unit tests covering parsing, memory managers, and action dispatchers.

## Tech Stack

- Python 3.10+
- Tkinter & Pillow (UI and HUD animations)
- OpenRouter API (LLM task planning)
- Microsoft Edge TTS (`edge-tts`) & `pyttsx3` (TTS engines)
- faster-whisper & sounddevice (Speech recognition & audio I/O)
- PyAutoGUI & Windows Kernel32 / User32 (Desktop automation & system control)
- Wikipedia & pywhatkit (Knowledge retrieval & YouTube media)
- python-dotenv

## Project Structure

```text
Mark-X/
  MarkX/
    actions/
      media_player.py     YouTube playback and media keys
      open_app.py         Windows application launcher
      send_message.py     WhatsApp message link generator
      system_control.py   Volume, screenshot, battery & lock
      weather_report.py   Weather forecast queries
      web_search.py       Web search and Google Maps
      wiki_lookup.py      Wikipedia summary retrieval
    core/
      prompt.txt          Assistant routing rules and intent schemas
    memory/
      memory_manager.py   Long-term persistent user memory
      temporary_memory.py Multi-turn session context and history
    main.py               App entry point and execution engine
    llm.py                LLM request handling and JSON task parsing
    speech_to_text.py     Voice activity detection and Whisper transcription
    tts.py                Neural Edge-TTS with pyttsx3 fallback
    ui.py                 Tkinter desktop interface and HUD
    face.png              Mark-X visual identity asset
  core/
    prompt.txt            Root prompt configuration
  tests/
    test_actions.py       Action handler unit tests
    test_llm_parser.py    JSON extractor and parser tests
    test_memory.py        Session and long-term memory tests
  check_system.py         System diagnostic verification tool
  .env.example            Environment configuration template
  requirements.txt        Python dependencies
```

## Setup

Clone the repository:

```bash
git clone https://github.com/DevarasettyKuldeep/Mark-X.git
cd Mark-X
```

Create and activate a virtual environment:

```bash
python -m venv env
env\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
copy .env.example .env
```

Configure your API key in `.env`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

*(Optional) Configure TTS voice and SerpAPI in `.env`:*

```env
TTS_ENGINE=edge
TTS_VOICE=en-US-ChristopherNeural
SERPAPI_API_KEY=your_serpapi_key_here
```

## Diagnostics

Verify system readiness, dependencies, audio hardware, and configuration:

```bash
python check_system.py
```

## Running Mark-X

```bash
python MarkX\main.py
```

## Running Tests

Execute the automated test suite:

```bash
python -m unittest discover -s tests -v
```

## Safety

Mark-X can open applications, take screenshots, adjust volume, and navigate browser links. Review any custom actions before enabling them in your environment.
