# ui.py
#
# Mark-X Primary Cyber-HUD Interface
# High-aesthetic dark obsidian theme with glowing avatar, animated halo,
# elegant chat cards, micro-animations, and hotkey controls.

import os
import time
import random
import threading
import tkinter as tk
from collections import deque
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from tkinter.scrolledtext import ScrolledText

# ── Design Tokens ─────────────────────────────────────────────────────────────
COLOR_BG            = "#080c14"  # Deep cosmic obsidian
COLOR_SURFACE       = "#0f172a"  # Slate panel surface
COLOR_SURFACE_HOVER = "#1e293b"  # Interactive hover slate
COLOR_BORDER        = "#1e293b"  # Subtle structural border
COLOR_BORDER_FOCUS  = "#0284c7"  # Active cyan focus ring
COLOR_CYAN          = "#38bdf8"  # Neon sky cyan
COLOR_BLUE          = "#6366f1"  # Electric indigo
COLOR_AMBER         = "#fbbf24"  # Listening amber
COLOR_ROSE          = "#f43f5e"  # Alert / Stop rose
COLOR_TEXT_MAIN     = "#f8fafc"  # Primary typography
COLOR_TEXT_MUTED    = "#64748b"  # Secondary typography
COLOR_TEXT_AI       = "#7dd3fc"  # Mark-X dialogue text
COLOR_TEXT_USER     = "#e2e8f0"  # User dialogue text


class JarvisUI:
    def __init__(self, face_path: str, size: tuple[int, int] = (680, 420)):
        self.root = tk.Tk()
        self.root.title("M A R K - X // A.I. SYSTEM")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG)

        self.canvas_size = size
        win_w = size[0]
        win_h = size[1] + 340  # Extra room for HUD header, chat card & controls
        self.root.geometry(f"{win_w}x{win_h}")

        # Center on screen
        self.root.update_idletasks()
        scr_w = self.root.winfo_screenwidth()
        scr_h = self.root.winfo_screenheight()
        pos_x = max(0, (scr_w - win_w) // 2)
        pos_y = max(0, (scr_h - win_h) // 2 - 20)
        self.root.geometry(f"+{pos_x}+{pos_y}")

        # ── Top Glass Navigation Bar ──────────────────────────────────────────
        nav_bar = tk.Frame(self.root, bg=COLOR_BG, height=36)
        nav_bar.pack(side=tk.TOP, fill=tk.X, padx=16, pady=(10, 2))

        # Title / Brand
        brand_frame = tk.Frame(nav_bar, bg=COLOR_BG)
        brand_frame.pack(side=tk.LEFT)

        brand_logo = tk.Label(
            brand_frame, text="◈", font=("Segoe UI", 12, "bold"), fg=COLOR_CYAN, bg=COLOR_BG
        )
        brand_logo.pack(side=tk.LEFT, padx=(0, 6))

        brand_title = tk.Label(
            brand_frame, text="MARK-X", font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT_MAIN, bg=COLOR_BG
        )
        brand_title.pack(side=tk.LEFT)

        brand_sub = tk.Label(
            brand_frame, text=" // CORE V2.0", font=("Consolas", 8), fg=COLOR_TEXT_MUTED, bg=COLOR_BG
        )
        brand_sub.pack(side=tk.LEFT, padx=(4, 0), pady=(2, 0))

        # Status badge (pill container)
        self.status_var = tk.StringVar(value="● ONLINE")
        self.status_pill = tk.Label(
            nav_bar,
            textvariable=self.status_var,
            font=("Consolas", 9, "bold"),
            fg=COLOR_CYAN,
            bg=COLOR_SURFACE,
            padx=12,
            pady=4,
            relief="flat",
        )
        self.status_pill.pack(side=tk.RIGHT)

        # ── Face / Avatar Canvas ──────────────────────────────────────────────
        self.canvas = tk.Canvas(
            self.root,
            width=size[0],
            height=size[1],
            bg=COLOR_BG,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(side=tk.TOP)

        # Load avatar asset
        try:
            self.face_base = (
                Image.open(face_path).convert("RGBA").resize(size, Image.LANCZOS)
            )
        except Exception as e:
            print(f"Could not load face image: {e}")
            self.face_base = Image.new("RGBA", size, (11, 15, 25, 255))

        self.halo_base = self._create_halo(size, radius=180, y_offset=-20)

        # Animation state
        self.speaking = False
        self.thinking = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.halo_alpha = 65.0
        self.target_halo_alpha = 65.0
        self.last_target_time = time.time()

        # ── Chat Log Container Card ───────────────────────────────────────────
        chat_card = tk.Frame(
            self.root,
            bg=COLOR_SURFACE,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER_FOCUS,
            padx=2,
            pady=2,
        )
        chat_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))

        self.text_box = ScrolledText(
            chat_card,
            fg=COLOR_TEXT_AI,
            bg=COLOR_SURFACE,
            insertbackground=COLOR_CYAN,
            height=7,
            borderwidth=0,
            wrap="word",
            font=("Consolas", 10),
            padx=12,
            pady=8,
            relief="flat",
        )
        self.text_box.pack(fill=tk.BOTH, expand=True)
        self.text_box.configure(state="disabled")

        # ── Controls & Prompt Input Bar ───────────────────────────────────────
        controls_card = tk.Frame(
            self.root,
            bg=COLOR_SURFACE,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            padx=6,
            pady=6,
        )
        controls_card.pack(fill=tk.X, padx=16, pady=(0, 12))

        # Mode toggle button
        self._mode = "text"
        self.mode_btn = tk.Button(
            controls_card,
            text="🎙 Voice",
            font=("Segoe UI", 9, "bold"),
            bg="#0c4a6e",
            fg=COLOR_CYAN,
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            bd=0,
            command=self._toggle_mode,
        )
        self.mode_btn.pack(side=tk.LEFT, padx=(0, 6))

        # Stop speech button
        self.stop_btn = tk.Button(
            controls_card,
            text="⏹ Stop",
            font=("Segoe UI", 9, "bold"),
            bg="#4c0519",
            fg="#fb7185",
            activebackground="#881337",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            bd=0,
            command=self._on_stop,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 6))

        # Clear chat button
        self.clear_btn = tk.Button(
            controls_card,
            text="🗑",
            font=("Segoe UI", 9),
            bg=COLOR_SURFACE_HOVER,
            fg=COLOR_TEXT_MUTED,
            activebackground="#334155",
            activeforeground=COLOR_TEXT_MAIN,
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=4,
            bd=0,
            command=self.clear_log,
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 6))

        # Minimal UI Switcher button
        self.minimal_btn = tk.Button(
            controls_card,
            text="🗗 Minimal",
            font=("Segoe UI", 9),
            bg=COLOR_SURFACE_HOVER,
            fg=COLOR_TEXT_MUTED,
            activebackground="#334155",
            activeforeground=COLOR_TEXT_MAIN,
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=4,
            bd=0,
            command=self._on_switch_to_minimal,
        )
        self.minimal_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Input container
        input_frame = tk.Frame(
            controls_card,
            bg=COLOR_BG,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER_FOCUS,
            padx=6,
            pady=2,
        )
        input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.input_var = tk.StringVar()
        self.input_box = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            font=("Consolas", 11),
            bg=COLOR_BG,
            fg=COLOR_TEXT_MAIN,
            insertbackground=COLOR_CYAN,
            borderwidth=0,
            relief="flat",
        )
        self.input_box.pack(fill=tk.X, expand=True, ipady=4)
        self.input_box.bind("<Return>", lambda _: self._on_send())

        # Send button
        self.send_btn = tk.Button(
            controls_card,
            text="➤",
            font=("Segoe UI", 11, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0ea5e9",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=3,
            bd=0,
            command=self._on_send,
        )
        self.send_btn.pack(side=tk.LEFT, padx=(6, 0))

        # ── Typing Queue & State ──────────────────────────────────────────────
        self.typing_queue: deque[str] = deque()
        self.is_typing = False
        self._typing_lock = threading.Lock()

        # Callbacks
        self.user_input_callback = None
        self.switch_ui_callback = None

        # ── Keyboard Shortcuts ────────────────────────────────────────────────
        self.root.bind("<Escape>", lambda _: self._on_stop())
        self.root.bind("<Control-l>", lambda _: self.clear_log())
        self.root.bind("<Control-L>", lambda _: self.clear_log())
        self.root.bind("<Control-m>", lambda _: self._toggle_mode())
        self.root.bind("<Control-M>", lambda _: self._toggle_mode())
        self.root.bind("<Control-w>", lambda _: self._on_switch_to_minimal())
        self.root.bind("<Control-W>", lambda _: self._on_switch_to_minimal())

        self.input_box.focus_set()
        self._animate()
        self.root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))

    # ── Minimal UI Switcher ───────────────────────────────────────────────────

    def set_switch_ui_callback(self, callback):
        self.switch_ui_callback = callback

    def _on_switch_to_minimal(self):
        if self.switch_ui_callback:
            self.switch_ui_callback()

    # ── Stop Speech ───────────────────────────────────────────────────────────

    def _on_stop(self):
        from tts import stop_speaking
        stop_speaking()
        self.stop_speaking()
        self.write_log("[Mark-X] Speech stopped.")

    # ── Clear Chat Log ────────────────────────────────────────────────────────

    def clear_log(self):
        with self._typing_lock:
            self.typing_queue.clear()
            self.is_typing = False
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", tk.END)
        self.text_box.configure(state="disabled")

    # ── Mode Toggle ───────────────────────────────────────────────────────────

    def _toggle_mode(self):
        if self._mode == "text":
            self._mode = "voice"
            self.mode_btn.config(text="⌨ Text", bg="#1e293b", fg=COLOR_AMBER)
            self.input_box.config(state="disabled")
            self.write_log("── Voice mode active. Speak clearly into microphone. ──")
        else:
            self._mode = "text"
            self.mode_btn.config(text="🎙 Voice", bg="#0c4a6e", fg=COLOR_CYAN)
            self.input_box.config(state="normal")
            self.input_box.focus_set()
            self.write_log("── Text input mode active. ──")

    def get_mode(self) -> str:
        return self._mode

    # ── Status Indicator ──────────────────────────────────────────────────────

    def set_thinking(self, active: bool):
        self.thinking = active

    def start_speaking(self):
        self.speaking = True

    def stop_speaking(self):
        self.speaking = False

    # ── Input Handler ─────────────────────────────────────────────────────────

    def _on_send(self):
        text = self.input_var.get().strip()
        if text and self.user_input_callback:
            self.user_input_callback(text)
            self.input_var.set("")

    def set_user_input_callback(self, callback):
        self.user_input_callback = callback

    # ── Chat Log Writer (Smooth Typewriter) ───────────────────────────────────

    def write_log(self, text: str):
        with self._typing_lock:
            self.typing_queue.append(text)
        if not self.is_typing:
            self.root.after(0, self._start_typing)

    def _start_typing(self):
        with self._typing_lock:
            if not self.typing_queue:
                self.is_typing = False
                return
            text = self.typing_queue.popleft()

        self.is_typing = True
        self.text_box.configure(state="normal")

        # Distinguish styling
        if text.startswith("You:"):
            self.text_box.insert(tk.END, text + "\n")
            self.text_box.see(tk.END)
            self.text_box.configure(state="disabled")
            self.is_typing = False
            self.root.after(10, self._start_typing)
        else:
            self._type_char(text, 0)

    def _type_char(self, text: str, i: int):
        if i < len(text):
            self.text_box.insert(tk.END, text[i])
            self.text_box.see(tk.END)
            self.root.after(6, self._type_char, text, i + 1)
        else:
            self.text_box.insert(tk.END, "\n")
            self.text_box.configure(state="disabled")
            self.root.after(12, self._start_typing)

    # ── Halo Generator ────────────────────────────────────────────────────────

    def _create_halo(self, size: tuple[int, int], radius: int, y_offset: int) -> Image.Image:
        w, h = size
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = w // 2, h // 2 + y_offset

        # Radial soft cyan/sapphire glow rings
        for r in range(radius, 0, -8):
            alpha = int(70 * (1 - r / radius))
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(2, 132, 199, alpha))

        return img.filter(ImageFilter.GaussianBlur(32))

    # ── 60 FPS Animation Loop ─────────────────────────────────────────────────

    def _animate(self):
        now = time.time()

        # Update status pill in top bar
        if self.speaking:
            self.status_var.set("● SPEAKING")
            self.status_pill.config(fg="#38bdf8", bg="#0c4a6e")
        elif self.thinking:
            dots = "." * (int(now * 2) % 4)
            self.status_var.set(f"▲ PROCESSING{dots}")
            self.status_pill.config(fg="#818cf8", bg="#1e1b4b")
        elif self._mode == "voice":
            self.status_var.set("🎙 LISTENING")
            self.status_pill.config(fg=COLOR_AMBER, bg="#451a03")
        else:
            self.status_var.set("● ONLINE")
            self.status_pill.config(fg="#34d399", bg="#064e3b")

        # Subtle dynamic pulse
        interval = 0.16 if self.speaking else 0.5
        if now - self.last_target_time > interval:
            if self.speaking:
                self.target_scale = random.uniform(1.025, 1.09)
                self.target_halo_alpha = random.uniform(130, 165)
            elif self.thinking:
                self.target_scale = random.uniform(1.01, 1.035)
                self.target_halo_alpha = random.uniform(85, 115)
            else:
                self.target_scale = random.uniform(1.001, 1.012)
                self.target_halo_alpha = random.uniform(50, 70)
            self.last_target_time = now

        # Smooth interpolation
        spd_s = 0.35 if self.speaking else 0.18
        spd_h = 0.30 if self.speaking else 0.15
        self.scale += (self.target_scale - self.scale) * spd_s
        self.halo_alpha += (self.target_halo_alpha - self.halo_alpha) * spd_h

        # Frame composition
        frame = Image.new("RGBA", self.canvas_size, (8, 12, 20, 255))

        # Composite glowing halo
        halo = self.halo_base.copy()
        halo.putalpha(int(max(0, min(255, self.halo_alpha))))
        frame.alpha_composite(halo)

        # Composite avatar
        w, h = self.canvas_size
        sw = int(w * self.scale)
        sh = int(h * self.scale)
        face = self.face_base.resize((sw, sh), Image.LANCZOS)
        fx = (w - sw) // 2
        fy = (h - sh) // 2
        frame.alpha_composite(face, (fx, fy))

        img = ImageTk.PhotoImage(frame)
        self.canvas.delete("all")
        self.canvas.create_image(w // 2, h // 2, image=img)
        self.canvas.image = img

        self.root.after(16, self._animate)
