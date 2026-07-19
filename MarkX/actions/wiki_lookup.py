# actions/wiki_lookup.py
#
# Direct Wikipedia knowledge retrieval for Mark-X:
# - Fetches concise, spoken encyclopedic summaries
# - Robust disambiguation handling and clean fallback

import re
import wikipedia
from tts import edge_speak


def clean_wiki_text(text: str) -> str:
    """Clean Wikipedia citation tags and parentheticals."""
    if not text:
        return ""
    # Strip citation brackets like [1], [citation needed]
    text = re.sub(r"\[.*?\]", "", text)
    # Normalize spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _speak_and_log(message: str, player=None):
    if player:
        try:
            player.write_log(f"Mark-X: {message}")
        except Exception:
            pass
    try:
        edge_speak(message)
    except Exception:
        pass


def wiki_action(parameters: dict, player=None, session_memory=None) -> str:
    """
    Look up encyclopedic summaries from Wikipedia.

    parameters:
        - query (str): Topic, person, historical event, or concept
        - sentences (int, optional): Maximum sentences to return (default 2)
    """
    params = parameters or {}
    query = (params.get("query") or params.get("topic") or "").strip()
    sentences = int(params.get("sentences", 2))

    if not query:
        msg = "Sir, what topic or person would you like me to look up on Wikipedia?"
        _speak_and_log(msg, player)
        return msg

    try:
        wikipedia.set_lang("en")
        raw_summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
        summary = clean_wiki_text(raw_summary)

        if not summary:
            msg = f"Sir, I found an entry for {query}, but couldn't extract a summary."
        else:
            msg = f"According to Wikipedia: {summary}"

    except wikipedia.exceptions.DisambiguationError as e:
        # Pick the most likely top candidate
        top_option = e.options[0] if e.options else None
        if top_option:
            try:
                raw_summary = wikipedia.summary(top_option, sentences=sentences, auto_suggest=False)
                summary = clean_wiki_text(raw_summary)
                msg = f"According to Wikipedia on {top_option}: {summary}"
            except Exception:
                msg = f"Sir, '{query}' could refer to several topics such as {', '.join(e.options[:3])}."
        else:
            msg = f"Sir, '{query}' has multiple ambiguous meanings."

    except wikipedia.exceptions.PageError:
        msg = f"Sir, I could not find a Wikipedia page matching '{query}'."

    except Exception as e:
        msg = f"Sir, Wikipedia lookup encountered an issue: {e}"

    _speak_and_log(msg, player)

    if session_memory:
        try:
            session_memory.set_last_search(query=f"wiki {query}", answer=msg)
            session_memory.set_last_ai_response(msg)
        except Exception:
            pass

    return msg
