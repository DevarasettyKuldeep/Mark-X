# llm.py

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"

PROMPT_PATH = "core/prompt.txt"

# ── Fallback system prompt ────────────────────────────────────────────────────
DEFAULT_SYSTEM_PROMPT = """You are Mark-X, an advanced AI assistant.

You MUST respond ONLY with a valid JSON object — no prose, no markdown fences.

The JSON must have this exact structure:
{
  "tasks": [
    {
      "intent": "<intent>",
      "parameters": { ... },
      "text": "<what to say to the user>"
    }
  ],
  "memory_update": { "key": "value" }
}

Rules:
- "tasks" is always an array. Split compound requests into multiple task objects.
- "memory_update" is optional; include it only when the user shares personal info worth remembering (name, preferences, location, etc.).
- Supported intents: open_app | search | weather_report | send_message | chat
- For "open_app": parameters must include "app_name" (string).
- For "search": parameters must include "query" (string).
- For "weather_report": parameters must include "city" (string).
- For "send_message": parameters must include "contact" (string) and "message" (string).
- For "chat": parameters can be empty {}. "text" is the reply you speak aloud.
- Always keep "text" concise, natural, and first-person (you are Mark-X).

Example for "Open YouTube and search for lo-fi music":
{
  "tasks": [
    {"intent": "open_app", "parameters": {"app_name": "youtube"}, "text": "Opening YouTube, sir."},
    {"intent": "search", "parameters": {"query": "lo-fi music"}, "text": "Searching for lo-fi music."}
  ]
}
"""


def load_system_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return content
    except Exception as e:
        print(f"Could not load prompt.txt: {e}")
    return DEFAULT_SYSTEM_PROMPT


SYSTEM_PROMPT = load_system_prompt()


# ── JSON extraction ───────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict | None:
    """Robustly extract the first valid JSON object from a string."""
    if not text:
        return None

    text = text.strip()

    # Strip ```json ... ``` or ``` ... ``` fences
    for fence_start, fence_end in [("```json", "```"), ("```", "```")]:
        if fence_start in text:
            try:
                s = text.index(fence_start) + len(fence_start)
                e = text.index(fence_end, s)
                text = text[s:e].strip()
                break
            except ValueError:
                pass

    # Find outermost { }
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception as e:
        print(f"JSON parse error: {e}")
        print(f"   Raw content: {text[:300]}")
        return None


# ── Fallback response builder ─────────────────────────────────────────────────

def _error_response(message: str) -> dict:
    return {
        "tasks": [{"intent": "chat", "parameters": {}, "text": message}],
        "memory_update": None,
    }


# ── Main LLM call ─────────────────────────────────────────────────────────────

def get_llm_output(user_text: str, memory_block: dict = None) -> dict:
    """
    Returns:
        {
            "tasks": [ {"intent": str, "parameters": dict, "text": str}, ... ],
            "memory_update": dict | None
        }
    """
    if not user_text or not user_text.strip():
        return _error_response("Sir, I didn't catch that.")

    if not OPENROUTER_API_KEY:
        print("OPENROUTER_API_KEY not found!")
        return _error_response("Sir, the API key is missing.")

    # Build memory context
    memory_str = (
        "\n".join(f"  {k}: {v}" for k, v in memory_block.items())
        if memory_block else "  (none)"
    )

    user_prompt = (
        f'User message: "{user_text}"\n\n'
        f"Known user memory:\n{memory_str}"
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 600,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=30
        )

        if response.status_code != 200:
            print(f"API error {response.status_code}: {response.text[:200]}")
            return _error_response(f"Sir, there was an API error ({response.status_code}).")

        content = response.json()["choices"][0]["message"]["content"]
        parsed = _extract_json(content)

        if not parsed:
            # LLM returned plain text — wrap it as a chat task
            return {
                "tasks": [{"intent": "chat", "parameters": {}, "text": content.strip()}],
                "memory_update": None,
            }

        # Normalise: older single-task format → tasks list
        if "tasks" not in parsed:
            tasks = [{
                "intent": parsed.get("intent", "chat"),
                "parameters": parsed.get("parameters", {}),
                "text": parsed.get("text", ""),
            }]
        else:
            tasks = parsed["tasks"]

        # Validate each task has required keys
        clean_tasks = []
        for t in tasks:
            if not isinstance(t, dict):
                continue
            clean_tasks.append({
                "intent": t.get("intent", "chat"),
                "parameters": t.get("parameters", {}),
                "text": t.get("text", ""),
            })

        if not clean_tasks:
            return _error_response("Sir, I couldn't parse a valid task.")

        return {
            "tasks": clean_tasks,
            "memory_update": parsed.get("memory_update"),
        }

    except requests.exceptions.Timeout:
        print("API timeout!")
        return _error_response("Sir, the connection timed out.")

    except Exception as e:
        print(f"LLM error: {e}")
        return _error_response("Sir, I encountered an unexpected error.")
