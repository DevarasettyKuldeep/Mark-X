# actions/system_control.py
#
# Desktop system control action for Mark-X:
# - Audio volume adjustments (volume up, volume down, mute)
# - Screen capture saved to screenshots/
# - Battery and power status query using Windows kernel32
# - Workstation screen lock

import os
import time
import ctypes
from datetime import datetime
import pyautogui
from tts import edge_speak

# Windows SYSTEM_POWER_STATUS structure
class _SystemPowerStatus(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_byte),
        ("BatteryFlag", ctypes.c_byte),
        ("BatteryLifePercent", ctypes.c_byte),
        ("Reserved1", ctypes.c_byte),
        ("BatteryLifeTime", ctypes.c_ulong),
        ("BatteryFullLifeTime", ctypes.c_ulong),
    ]


def _get_battery_status() -> str:
    """Read Windows system power status via kernel32."""
    try:
        status = _SystemPowerStatus()
        result = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
        if not result:
            return "Sir, I could not query the system battery status."

        percent = status.BatteryLifePercent
        ac = status.ACLineStatus

        if percent == 255:
            return "Sir, no battery is detected on this machine."

        charging_str = "plugged in and charging" if ac == 1 else "running on battery power"
        return f"Sir, the battery is at {percent}% and currently {charging_str}."
    except Exception as e:
        return f"Sir, failed to check battery status: {e}"


def _take_screenshot() -> tuple[bool, str]:
    """Capture full desktop and save to screenshots/ directory."""
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        screenshots_dir = os.path.join(root_dir, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)

        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(screenshots_dir, filename)

        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return True, f"Sir, screenshot captured and saved to {filename}."
    except Exception as e:
        return False, f"Sir, failed to take screenshot: {e}"


def _adjust_volume(command: str, steps: int = 5) -> str:
    """Adjust system volume using media hotkeys."""
    try:
        pyautogui.PAUSE = 0.05
        if command in ("volume_up", "increase_volume", "louder"):
            for _ in range(steps):
                pyautogui.press("volumeup")
            return "Sir, I have increased the volume."
        elif command in ("volume_down", "decrease_volume", "lower_volume"):
            for _ in range(steps):
                pyautogui.press("volumedown")
            return "Sir, I have decreased the volume."
        elif command in ("mute", "unmute", "toggle_mute"):
            pyautogui.press("volumemute")
            return "Sir, I have toggled system mute."
        else:
            return "Sir, unknown volume adjustment command."
    except Exception as e:
        return f"Sir, could not adjust volume: {e}"


def _lock_workstation() -> str:
    """Lock the Windows workstation."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Sir, locking the workstation now."
    except Exception as e:
        return f"Sir, failed to lock screen: {e}"


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


def system_control_action(parameters: dict, player=None, session_memory=None) -> str:
    """
    Main system control action dispatcher.

    parameters:
        - command (str): 'volume_up' | 'volume_down' | 'mute' | 'screenshot' | 'battery' | 'lock'
        - steps (int, optional): amount of volume steps (default 5)
    """
    command = (parameters or {}).get("command", "").lower().strip()
    steps = int((parameters or {}).get("steps", 5))

    if not command:
        # Fallback inspection of raw query or intent parameters
        action_type = (parameters or {}).get("action", "").lower().strip()
        command = action_type or "unknown"

    if any(k in command for k in ("vol", "loud", "sound", "mute")):
        msg = _adjust_volume(command, steps=steps)
    elif "screen" in command or "capture" in command:
        _, msg = _take_screenshot()
    elif "battery" in command or "power" in command:
        msg = _get_battery_status()
    elif "lock" in command:
        msg = _lock_workstation()
    else:
        msg = f"Sir, I recognized system control command '{command}', but couldn't execute it."

    _speak_and_log(msg, player)

    if session_memory:
        try:
            session_memory.set_last_ai_response(msg)
        except Exception:
            pass

    return msg
