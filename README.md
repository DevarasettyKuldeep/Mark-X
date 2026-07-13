# Mark-X

Mark-X is a Python desktop AI assistant for Windows. It combines a Tkinter interface, voice input, text-to-speech, LLM-based task planning, local memory, and action modules for common desktop tasks.

## Features

- Desktop assistant UI with animated visual identity
- Text and voice command input
- Text-to-speech responses
- LLM-powered intent and task planning
- Open Windows applications
- Web search with browser fallback
- Nearby-place searches through Google Maps
- Weather lookup through browser search
- WhatsApp message link generation
- Local memory management

## Tech Stack

- Python
- Tkinter
- OpenRouter API
- faster-whisper
- sounddevice
- pyttsx3
- SerpAPI, optional
- python-dotenv

## Project Structure

```text
Mark-X/
  MarkX/
    actions/          Command action modules
    core/             Assistant prompt rules
    memory/           Memory helpers
    main.py           App entry point and command engine
    llm.py            LLM request and JSON task parsing
    ui.py             Tkinter desktop interface
    speech_to_text.py Voice transcription
    tts.py            Text-to-speech
    face.png          Mark-X visual asset
  core/
    prompt.txt        Root prompt copy
  .env.example        Example environment variables
  requirements.txt    Python dependencies
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

Then edit `.env` and add your API key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

Optional, for summarized web results:

```env
SERPAPI_API_KEY=your_serpapi_api_key_here
```

## Run

```bash
python MarkX\main.py
```

## Notes

- `.env`, `env/`, `memory/`, and Python cache files are intentionally ignored.
- If `SERPAPI_API_KEY` is not configured, web search opens browser results instead of failing.
- For nearby searches, Mark-X opens Google Maps results.
- This project is intended for personal learning and local desktop automation.

## Safety

Mark-X can open applications and browser links on your computer. Review any new action module before enabling it, and do not add untrusted code to the assistant.
