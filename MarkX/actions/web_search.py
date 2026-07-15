import os
import re
import webbrowser
from urllib.parse import quote_plus

from dotenv import load_dotenv
from serpapi import GoogleSearch
from tts import edge_speak


MAX_SNIPPETS = 3
MIN_SENTENCE_LENGTH = 30

load_dotenv()


def clean(text: str) -> str:
    """Clean text: remove extra spaces, ..., brackets."""
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\.\.\.+", ".", text)          
    text = re.sub(r"\[.*?\]", "", text)           
    text = re.sub(r"\(.*?\)", "", text)           
    return text.strip()


def split_sentences(text: str):
    """Split text into sentences and avoid very short or incomplete ones."""
    sentences = re.split(r"(?<=[.!?])\s+", text)

    valid_sentences = []
    buffer = ""

    for s in sentences:
        s = clean(s)
        if not s:
            continue

        last_word = s.split()[-1].lower()
        if last_word in [
            "of", "in", "at", "on", "by",
            "after", "before", "with", "for", "to"
        ]:
            buffer += s + " "
            continue

        if buffer:
            s = buffer + s
            buffer = ""

        if len(s) >= MIN_SENTENCE_LENGTH:
            valid_sentences.append(s)

    return valid_sentences


def is_noise(text: str) -> bool:
    """Check if a sentence is noise or irrelevant."""
    t = text.lower()

    noise_keywords = [
        "read more",
        "learn more",
        "click here",
        "infographic",
        "google trends",
        "year in search",
        "most searched",
        "top 100",
        "subscribe",
        "share this",
        "advertisement",
        "ad:"
    ]

    return any(word in t for word in noise_keywords)


def select_best_sentence(snippets):
    """Combine up to MAX_SNIPPETS and return a single coherent sentence."""
    final_text = ""
    count = 0

    for snippet in snippets:
        if not snippet or is_noise(snippet):
            continue

        sentences = split_sentences(snippet)

        for s in sentences:
            if is_noise(s):
                continue

            final_text = f"{final_text} {s}".strip()
            count += 1

            if count >= MAX_SNIPPETS:
                return final_text

    return final_text if final_text else None


def _is_local_search(query: str) -> bool:
    query_lower = query.lower()
    local_words = [
        "near me",
        "nearby",
        "around me",
        "closest",
        "restaurant",
        "coffee",
        "shop",
        "hospital",
        "pharmacy",
        "hotel",
        "atm",
        "gas station",
    ]
    return any(word in query_lower for word in local_words)


def _open_browser_search(query: str) -> str:
    encoded_query = quote_plus(query)
    if _is_local_search(query):
        url = f"https://www.google.com/maps/search/{encoded_query}"
        webbrowser.open(url)
        return f"Sir, I opened nearby results for {query} in Google Maps."

    url = f"https://www.google.com/search?q={encoded_query}"
    webbrowser.open(url)
    return f"Sir, I opened web results for {query}."


def _answer_from_answer_box(data: dict) -> str | None:
    answer_box = data.get("answer_box") or {}
    for key in ("answer", "snippet", "definition"):
        value = answer_box.get(key)
        if value:
            return clean(str(value))
    return None


def _answer_from_local_results(data: dict) -> str | None:
    local_results = data.get("local_results") or {}
    places = local_results.get("places") or []
    if not places:
        return None

    names = []
    for place in places[:3]:
        title = place.get("title")
        rating = place.get("rating")
        address = place.get("address")
        if not title:
            continue

        detail = title
        if rating:
            detail += f" ({rating} stars)"
        if address:
            detail += f", {address}"
        names.append(detail)

    if not names:
        return None

    return "Nearby options I found: " + "; ".join(names)


def serpapi_answer(query: str, api_key: str | None = None) -> str:
    """Perform search and return a short useful answer."""
    api_key = api_key or os.getenv("SERPAPI_API_KEY") or os.getenv("SERP_API_KEY")
    if not api_key:
        return _open_browser_search(query)

    params = {
        "q": query,
        "engine": "google",
        "hl": "en",
        "gl": "us",
        "num": 3,
        "api_key": api_key
    }

    try:
        data = GoogleSearch(params).get_dict()
    except Exception as e:
        return f"Sir, the web search failed: {e}"

    search_error = data.get("error")
    if search_error:
        return f"Sir, the search API returned an error: {search_error}"

    answer_box = _answer_from_answer_box(data)
    if answer_box:
        return answer_box

    local_answer = _answer_from_local_results(data)
    if local_answer:
        return local_answer

    organic = data.get("organic_results", [])
    if not organic:
        return _open_browser_search(query)

    snippets = [
        r.get("snippet", "")
        for r in organic
        if r.get("snippet")
    ]

    answer = select_best_sentence(snippets)

    if not answer:
        return "Sir, I found information online, but couldn't summarize it clearly."

    return answer



def web_search(
    parameters: dict,
    player=None,
    session_memory=None,
    api_key: str = ""
):
    """
    Main web search:
    - Returns 1 coherent sentence
    - Does NOT append previous answers
    - Combines multiple snippets if needed to avoid cut-offs
    """

    query = (parameters or {}).get("query", "").strip()

    if not query:
        msg = "Sir, I couldn't understand the search request."
        if player:
            player.write_log(msg)
        edge_speak(msg)
        return msg

    answer = serpapi_answer(query, api_key)

    if player:
        player.write_log(f"AI: {answer}")

    edge_speak(answer)

    if session_memory:
        session_memory.set_last_search(query, answer)

    return answer
