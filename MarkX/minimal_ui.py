# minimal_ui.py
#
# Minimal Workspace Interface for Mark-X
# Compact, distraction-free floating command bar designed for active workflows.
# Features a small glowing logo, medium prompt input, transient status toast,
# and zero window clutter.

import os
import time
import threading
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw

COLOR_BG            = "#080c14"  # Deep cosmic obsidian
COLOR_SURFACE       = "#0f172a"  # Slate panel surface
COLOR_BORDER        = "#1e293b"  # Border stroke
COLOR_BORDER_FOCUS  = "#0284c7"  # Active focus cyan
COLOR_CYAN          = "#38bdf8"  # Sky cyan
COLOR_AMBER         = "#fbbf24"  # Listening amber
COLOR_ROSE          = "#f43f5e"  # Stop rose
COLOR_TEXT_MAIN     = "#f8fafc"  # Primary typography
COLOR_TEXT_MUTED    = "#64748b"  # Secondary typography
COLOR_TEXT_TOAST    = "#7dd3fc"  # Response toast text


class MinimalUI:
    def __init__(self, face_path: str, size: tuple[int, int] = (640, 110)):
        self.root = tk.Tk()
        self.root.title("Mark-X Workspace")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG)

        # Style as a sleek floating window
        self.width, self.height = size
        self.root.geometry(f"{self.width}x{self.height}")

        # Center on screen (slightly above center for natural command-bar placement)
        self.root.update_idletasks()
        scr_w = self.root.winfo_screenwidth()
        scr_h = self.root.winfo_screenheight()
        pos_x = max(0, (scr_w - self.width) // 2)
        pos_y = max(0, (scr_h - self.height) // 2 - 120)
        self.root.geometry(f"+{pos_x}+{pos_y}")

        # Make draggable
        self._drag_data = {"x": 0, "y": 0}
        self.root.bind("<Button-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._on_drag)

        # Main container card
        self.main_card = tk.Frame(
            self.root,
            bg=COLOR_SURFACE,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            padx=12,
            pady=10,
        )
        self.main_card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ── Row 1: Logo + Text Prompt + Action Buttons ────────────────────────
        row1 = tk.Frame(self.main_card, bg=COLOR_SURFACE)
        row1.pack(fill=tk.X, pady=(2, 6))

        # Small circular avatar
        self.avatar_size = 46
        self.avatar_canvas = tk.Canvas(
            row1,
            width=self.avatar_size,
            height=self.avatar_size,
            bg=COLOR_SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self.avatar_canvas.pack(side=tk.LEFT, padx=(0, 10))

        # Load & crop circular face
        self.face_img = self._load_circular_avatar(face_path, self.avatar_size)
        self.avatar_canvas.create_image(
            self.avatar_size // 2, self.avatar_size // 2, image=self.face_img
        )

        # Medium-sized prompt text box container
        input_container = tk.Frame(
            row1,
            bg=COLOR_BG,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER_FOCUS,
            padx=8,
            pady=3,
        )
        input_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.input_var = tk.StringVar()
        self.input_box = tk.Entry(
            input_container,
            textvariable=self.input_var,
            font=("Segoe UI", 12),
            bg=COLOR_BG,
            fg=COLOR_TEXT_MAIN,
            insertbackground=COLOR_CYAN,
            borderwidth=0,
            relief="flat",
        )
        self.input_box.pack(fill=tk.X, expand=True, ipady=4)
        self.input_box.bind("<Return>", lambda _: self._on_send())

        # Placeholder text support
        self.placeholder = "Ask Mark-X anything... (Enter to send, Esc to stop)"
        self.input_box.insert(0, self.placeholder)
        self.input_box.config(fg=COLOR_TEXT_MUTED)
        self.input_box.bind("<FocusIn>", self._clear_placeholder)
        self.input_box.bind("<FocusOut>", self._restore_placeholder)

        # Action Buttons frame
        actions = tk.Frame(row1, bg=COLOR_SURFACE)
        actions.pack(side=tk.RIGHT)

        # Mode toggle button
        self._mode = "text"
        self.mode_btn = tk.Button(
            actions,
            text="🎙",
            font=("Segoe UI", 11),
            bg="#0c4a6e",
            fg=COLOR_CYAN,
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            width=3,
            bd=0,
            command=self._toggle_mode,
        )
        self.mode_btn.pack(side=tk.LEFT, padx=(0, 4))

        # Stop speech button
        self.stop_btn = tk.Button(
            actions,
            text="⏹",
            font=("Segoe UI", 11),
            bg="#4c0519",
            fg="#fb7185",
            activebackground="#881337",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            width=3,
            bd=0,
            command=self._on_stop,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 4))

        # Full HUD switch button
        self.expand_btn = tk.Button(
            actions,
            text="⛶",
            font=("Segoe UI", 11),
            bg="#1e293b",
            fg=COLOR_TEXT_MUTED,
            activebackground="#334155",
            activeforeground=COLOR_TEXT_MAIN,
            relief="flat",
            cursor="hand2",
            width=3,
            bd=0,
            command=self._on_switch_to_full,
        )
        self.expand_btn.pack(side=tk.LEFT)

        # ── Row 2: Transient Status Toast Pill ────────────────────────────────
        row2 = tk.Frame(self.main_card, bg=COLOR_SURFACE)
        row2.pack(fill=tk.X, pady=(2, 0))

        self.status_var = tk.StringVar(value="● READY")
        self.status_badge = tk.Label(
            row2,
            textvariable=self.status_var,
            font=("Consolas", 8, "bold"),
            fg="#34d399",
            bg="#064e3b",
            padx=8,
            pady=2,
            relief="flat",
        )
        self.status_badge.pack(side=tk.LEFT, padx=(0, 8))

        self.toast_var = tk.StringVar(value="Workspace mode active • Minimal distraction")
        self.toast_label = tk.Label(
            row2,
            textvariable=self.toast_var,
            font=("Segoe UI", 9),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_SURFACE,
            anchor="w",
        )
        self.toast_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Animation & state variables
        self.speaking = False
        self.thinking = False
        self.user_input_callback = None
        self.switch_ui_callback = None

        # Hotkeys
        self.root.bind("<Escape>", lambda _: self._on_stop())
        self.root.bind("<Control-m>", lambda _: self._toggle_mode())
        self.root.bind("<Control-M>", lambda _: self._toggle_mode())
        self.root.bind("<Control-w>", lambda _: self._on_switch_to_full())
        self.root.bind("<Control-W>", lambda _: self._on_switch_to_full())

        self._start_animation_loop()
        self.root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))

    # ── Circular Avatar Loader ────────────────────────────────────────────────

    def _load_circular_avatar(self, path: str, size: int) -> ImageTk.PhotoImage:
        try:
            img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
        except Exception:
            img = Image.new("RGBA", (size, size), (2, 132, 199, 255))

        # Circular mask with anti-aliasing
        mask = Image.new("L", (size * 4, size * 4), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size * 4, size * 4), fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)

        img.putalpha(mask)
        return ImageTk.PhotoImage(img)

    # ── Draggable Window Helpers ──────────────────────────────────────────────

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    # ── Placeholder Management ────────────────────────────────────────────────

    def _clear_placeholder(self, _):
        if self.input_box.get() == self.placeholder:
            self.input_box.delete(0, tk.END)
            self.input_box.config(fg=COLOR_TEXT_MAIN)

    def _restore_placeholder(self, _):
        if not self.input_box.get().strip():
            self.input_box.insert(0, self.placeholder)
            self.input_box.config(fg=COLOR_TEXT_MUTED)

    # ── Switcher Callback ─────────────────────────────────────────────────────

    def set_switch_ui_callback(self, callback):
        self.switch_ui_callback = callback

    def _on_switch_to_full(self):
        if self.switch_ui_callback:
            self.switch_ui_callback()

    # ── Stop Speech ───────────────────────────────────────────────────────────

    def _on_stop(self):
        from tts import stop_speaking
        stop_speaking()
        self.stop_speaking()
        self.write_log("[Mark-X] Speech stopped.")

    # ── Mode Toggle ───────────────────────────────────────────────────────────

    def _toggle_mode(self):
        if self._mode == "text":
            self._mode = "voice"
            self.mode_btn.config(text="⌨", bg="#1e293b", fg=COLOR_AMBER)
            self.input_box.config(state="disabled")
            self.toast_var.set("Voice mode active • Listening for speech...")
            self.toast_label.config(fg=COLOR_AMBER)
        else:
            self._mode = "text"
            self.mode_btn.config(text="🎙", bg="#0c4a6e", fg=COLOR_CYAN)
            self.input_box.config(state="normal")
            self.input_box.focus_set()
            self.toast_var.set("Text mode active • Ready for input")
            self.toast_label.config(fg=COLOR_TEXT_MUTED)

    def get_mode(self) -> str:
        return self._mode

    # ── Status Updates ────────────────────────────────────────────────────────

    def set_thinking(self, active: bool):
        self.thinking = active

    def start_speaking(self):
        self.speaking = True

    def stop_speaking(self):
        self.speaking = False

    # ── Input Handler ─────────────────────────────────────────────────────────

    def _on_send(self):
        text = self.input_var.get().strip()
        if text == self.placeholder:
            return
        if text and self.user_input_callback:
            self.toast_var.set(f"You: {text}")
            self.toast_label.config(fg=COLOR_TEXT_MAIN)
            self.user_input_callback(text)
            self.input_var.set("")

    def set_user_input_callback(self, callback):
        self.user_input_callback = callback

    # ── Transient Toast Logger (Replaces Chat History) ────────────────────────

    def write_log(self, text: str):
        """Displays transient status message without cluttering workspace."""
        clean = text.strip()
        if clean.startswith("Mark-X:"):
            clean = clean[len("Mark-X:"):].strip()
            self.toast_var.set(f"Mark-X: {clean}")
            self.toast_label.config(fg=COLOR_TEXT_TOAST)
        elif clean.startswith("You:"):
            self.toast_var.set(clean)
            self.toast_label.config(fg=COLOR_TEXT_MAIN)
        else:
            self.toast_var.set(clean)
            self.toast_label.config(fg=COLOR_TEXT_MUTED)

    # ── State Loop ────────────────────────────────────────────────────────────

    def _start_animation_loop(self):
        def _loop():
            now = time.time()
            if self.speaking:
                self.status_var.set("● SPEAKING")
                self.status_badge.config(fg="#38bdf8", bg="#0c4a6e")
            elif self.thinking:
                dots = "." * (int(now * 2) % 4)
                self.status_var.set(f"▲ THINKING{dots}")
                self.status_badge.config(fg="#818cf8", bg="#1e1b4b")
            elif self._mode == "voice":
                self.status_var.set("🎙 LISTENING")
                self.status_badge.config(fg=COLOR_AMBER, bg="#451a03")
            else:
                self.status_var.set("● READY")
                self.status_badge.config(fg="#34d399", bg="#064e3b")

            self.root.after(100, _loop)

        self.root.after(100, _loop)
