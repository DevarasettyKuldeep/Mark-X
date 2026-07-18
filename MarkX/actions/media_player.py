# actions/media_player.py
#
# Media player and YouTube automation action for Mark-X:
# - Search and play songs, videos, or podcasts on YouTube
# - Hardware media key emulation (play/pause, next track, prev track, stop)

import urllib.parse
import webbrowser
import pyautogui
from tts import edge_speak


def _play_youtube(query: str) -> str:
    """Launch YouTube video or search query."""
    try:
        import pywhatkit
        pywhatkit.playonyt(query)
        return f"Sir, playing {query} on YouTube."
    except Exception:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(url)
        return f"Sir, searching and opening {query} on YouTube."


def _handle_media_control(control: str) -> str:
    """Emulate media control keypresses."""
    c = control.lower().strip()
    try:
        pyautogui.PAUSE = 0.05
        if c in ("play", "pause", "play_pause", "toggle"):
            pyautogui.press("playpause")
            return "Sir, toggling media playback."
        elif c in ("next", "next_track", "skip"):
            pyautogui.press("nexttrack")
            return "Sir, skipping to the next track."
        elif c in ("prev", "previous", "previous_track", "back"):
            pyautogui.press("prevtrack")
            return "Sir, returning to the previous track."
        elif c in ("stop", "halt"):
            pyautogui.press("stop")
            return "Sir, media playback stopped."
        else:
            return f"Sir, unknown media control '{control}'."
    except Exception as e:
        return f"Sir, failed to execute media control: {e}"


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


def media_action(parameters: dict, player=None, session_memory=None) -> str:
    """
    Main media player action handler.

    parameters:
        - query (str, optional): song name, video title, or artist
        - control (str, optional): 'play_pause' | 'next' | 'previous' | 'stop'
    """
    params = parameters or {}
    query = (params.get("query") or params.get("song") or params.get("video") or "").strip()
    control = (params.get("control") or params.get("command") or "").strip()

    if control and not query:
        msg = _handle_media_control(control)
    elif query:
        msg = _play_youtube(query)
    else:
        msg = "Sir, what would you like me to play or control?"

    _speak_and_log(msg, player)

    if session_memory:
        try:
            if query:
                session_memory.set_last_search(query=f"play {query}", answer=msg)
            session_memory.set_last_ai_response(msg)
        except Exception:
            pass

    return msg
