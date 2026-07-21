# ui.py

import os
import time
import random
import threading
import tkinter as tk
from collections import deque
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from tkinter.scrolledtext import ScrolledText


class JarvisUI:
    def __init__(self, face_path: str, size: tuple[int, int] = (760, 760)):
        self.root = tk.Tk()
        self.root.title("M A R K - X")
        self.root.resizable(False, False)
        self.root.configure(bg="#000000")

        self.size = size
        win_w = size[0]
        win_h = size[1] + 280          # extra room for chat + input
        self.root.geometry(f"{win_w}x{win_h}")

        # ── Face canvas ───────────────────────────────────────────────────────
        self.canvas = tk.Canvas(
            self.root,
            width=size[0],
            height=size[1],
            bg="#000000",
            highlightthickness=0,
        )
        self.canvas.pack(side=tk.TOP)

        # Face / halo assets
        try:
            self.face_base = (
                Image.open(face_path).convert("RGBA").resize(size, Image.LANCZOS)
            )
        except Exception as e:
            print(f"Could not load face image: {e}")
            self.face_base = Image.new("RGBA", size, (0, 30, 60, 255))

        self.halo_base = self._create_halo(size, radius=220, y_offset=-40)

        # Animation state
        self.speaking = False
        self.thinking = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.halo_alpha = 70.0
        self.target_halo_alpha = 70.0
        self.last_target_time = time.time()
        self._blink_tick = 0

        # ── Status bar (thinking indicator) ──────────────────────────────────
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Consolas", 9),
            fg="#004466",
            bg="#000000",
        )
        self.status_label.pack(side=tk.TOP, anchor="w", padx=12)

        # ── Chat log ──────────────────────────────────────────────────────────
        self.text_box = ScrolledText(
            self.root,
            fg="#8ffcff",
            bg="#050505",
            insertbackground="#8ffcff",
            height=9,
            borderwidth=0,
            wrap="word",
            font=("Consolas", 10),
            padx=12,
            pady=8,
            relief="flat",
        )
        self.text_box.pack(fill=tk.X, padx=10)
        self.text_box.configure(state="disabled")

        # ── Bottom controls row ───────────────────────────────────────────────
        controls = tk.Frame(self.root, bg="#000000")
        controls.pack(fill=tk.X, padx=10, pady=6)

        # Mode toggle button (Text ↔ Voice)
        self._mode = "text"
        self.mode_btn = tk.Button(
            controls,
            text="🎙 Voice",
            font=("Consolas", 10),
            bg="#001a2c",
            fg="#00aaff",
            activebackground="#003355",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            width=8,
            command=self._toggle_mode,
        )
        self.mode_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Stop speech button
        self.stop_btn = tk.Button(
            controls,
            text="⏹ Stop",
            font=("Consolas", 10),
            bg="#2c0000",
            fg="#ff5555",
            activebackground="#550000",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            width=7,
            command=self._on_stop,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Text input field
        self.input_var = tk.StringVar()
        self.input_box = tk.Entry(
            controls,
            textvariable=self.input_var,
            font=("Consolas", 13),
            bg="#111111",
            fg="#00ffff",
            insertbackground="#00ffff",
            borderwidth=0,
            relief="flat",
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_box.bind("<Return>", lambda _: self._on_send())

        # Send button
        send_btn = tk.Button(
            controls,
            text="➤",
            font=("Consolas", 13),
            bg="#001a2c",
            fg="#00ffff",
            activebackground="#003355",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            width=3,
            command=self._on_send,
        )
        send_btn.pack(side=tk.LEFT, padx=(6, 0))

        # ── Typing queue ──────────────────────────────────────────────────────
        self.typing_queue: deque[str] = deque()
        self.is_typing = False
        self._typing_lock = threading.Lock()

        # ── Callback placeholder ──────────────────────────────────────────────
        self.user_input_callback = None

        # ── Start animation loop ──────────────────────────────────────────────
        self._animate()
        self.root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))

        # Hotkeys: Esc = Stop speech, Ctrl+L = Clear chat, Ctrl+M = Mode toggle
        self.root.bind("<Escape>", lambda _: self._on_stop())
        self.root.bind("<Control-l>", lambda _: self.clear_log())
        self.root.bind("<Control-L>", lambda _: self.clear_log())
        self.root.bind("<Control-m>", lambda _: self._toggle_mode())
        self.root.bind("<Control-M>", lambda _: self._toggle_mode())
        self.input_box.focus_set()

    def _on_stop(self):
        from tts import stop_speaking
        stop_speaking()
        self.stop_speaking()
        self.write_log("[Mark-X] Speech stopped.")

    def clear_log(self):
        with self._typing_lock:
            self.typing_queue.clear()
            self.is_typing = False
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", tk.END)
        self.text_box.configure(state="disabled")

    # ── Mode toggle ───────────────────────────────────────────────────────────

    def _toggle_mode(self):
        if self._mode == "text":
            self._mode = "voice"
            self.mode_btn.config(text="⌨ Text")
            self.input_box.config(state="disabled")
            self.write_log("── Voice mode activated. Speak your command. ──")
        else:
            self._mode = "text"
            self.mode_btn.config(text="🎙 Voice")
            self.input_box.config(state="normal")
            self.input_box.focus_set()
            self.write_log("── Text mode activated. ──")

    def get_mode(self) -> str:
        return self._mode

    # ── Thinking indicator ────────────────────────────────────────────────────

    def set_thinking(self, active: bool):
        self.thinking = active
        # status managed automatically in _animate() loop
        pass

    # ── Input handler ─────────────────────────────────────────────────────────

    def _on_send(self):
        text = self.input_var.get().strip()
        if text and self.user_input_callback:
            self.user_input_callback(text)
            self.input_var.set("")

    def set_user_input_callback(self, callback):
        self.user_input_callback = callback

    # ── Chat log writer (typewriter effect, thread-safe) ─────────────────────

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
        self._type_char(text, 0)

    def _type_char(self, text: str, i: int):
        if i < len(text):
            self.text_box.insert(tk.END, text[i])
            self.text_box.see(tk.END)
            self.root.after(7, self._type_char, text, i + 1)
        else:
            self.text_box.insert(tk.END, "\n")
            self.text_box.configure(state="disabled")
            self.root.after(15, self._start_typing)

    # ── Speaking state (controls animation intensity) ─────────────────────────

    def start_speaking(self):
        self.speaking = True

    def stop_speaking(self):
        self.speaking = False

    # ── Halo builder ─────────────────────────────────────────────────────────

    def _create_halo(
        self, size: tuple[int, int], radius: int, y_offset: int
    ) -> Image.Image:
        w, h = size
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = w // 2, h // 2 + y_offset
        for r in range(radius, 0, -10):
            alpha = int(80 * (1 - r / radius))
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0, 180, 255, alpha))
        return img.filter(ImageFilter.GaussianBlur(28))

    # ── Animation loop (runs every 16 ms ≈ 60 fps) ────────────────────────────

    def _animate(self):
        now = time.time()

        # Update thinking status text
        if self.speaking:
            self.status_var.set("  ● SPEAKING")
            self.status_label.config(fg="#00ffff")
        elif self.thinking:
            dots = "." * (int(now * 2) % 4)
            self.status_var.set(f"  ▲ THINKING{dots}")
            self.status_label.config(fg="#00aaff")
        elif self._mode == "voice":
            self.status_var.set("  🎙 LISTENING...")
            self.status_label.config(fg="#ffaa00")
        else:
            self.status_var.set("  ■ ONLINE | IDLE")
            self.status_label.config(fg="#004466")

        # Determine target scale / glow based on state
        interval = 0.18 if self.speaking else 0.6
        if now - self.last_target_time > interval:
            if self.speaking:
                self.target_scale = random.uniform(1.03, 1.12)
                self.target_halo_alpha = random.uniform(130, 160)
            elif self.thinking:
                self.target_scale = random.uniform(1.01, 1.04)
                self.target_halo_alpha = random.uniform(90, 120)
            else:
                self.target_scale = random.uniform(1.002, 1.01)
                self.target_halo_alpha = random.uniform(55, 75)
            self.last_target_time = now

        # Smooth lerp
        spd_s = 0.40 if self.speaking else 0.20
        spd_h = 0.35 if self.speaking else 0.18
        self.scale += (self.target_scale - self.scale) * spd_s
        self.halo_alpha += (self.target_halo_alpha - self.halo_alpha) * spd_h

        # Compose frame
        frame = Image.new("RGBA", self.size, (0, 0, 0, 255))

        halo = self.halo_base.copy()
        halo.putalpha(int(max(0, min(255, self.halo_alpha))))
        frame.alpha_composite(halo)

        w, h = self.size
        sw = int(w * self.scale)
        sh = int(h * self.scale)
        face = self.face_base.resize((sw, sh), Image.LANCZOS)
        fx = (w - sw) // 2
        fy = (h - sh) // 2
        frame.alpha_composite(face, (fx, fy))

        img = ImageTk.PhotoImage(frame)
        self.canvas.delete("all")
        self.canvas.create_image(w // 2, h // 2, image=img)
        self.canvas.image = img   # prevent GC

        self.root.after(16, self._animate)
