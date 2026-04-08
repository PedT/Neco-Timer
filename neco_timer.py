import tkinter as tk
from tkinter import ttk
import base64
import io
import threading
import time
import tempfile
import winsound

from PIL import Image, ImageTk
import pystray

from assets import (
    IDLE_PNG, RUNNING_GIF, TIMES_UP_PNG,
    ANIMATION_GIF, ALERT_WAV, TRAY_ICON_PNG,
)


class BreakTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Break Timer")
        self.root.resizable(False, False)

        self.CANVAS_W = 500
        self.CANVAS_H = 281
        self.root.protocol("WM_DELETE_WINDOW", self._quit_app)
        self.root.bind("<Unmap>", self._on_minimize)

        self.running = False
        self.remaining = 0
        self.tray_icon = None
        self.gif_animating = False
        self.running_gif_animating = False

        # Animation GIF frames (times-up)
        self.gif_frames = []
        self.gif_frames_flipped = []
        self.gif_frame_index = 0
        self.gif_delay = 100

        # Running GIF frames
        self.running_frames = []
        self.running_frame_index = 0
        self.running_gif_delay = 60

        self._load_assets()
        self._build_ui()
        self._setup_tray()
        self._show_idle()

    def _resize(self, img):
        return img.resize((self.CANVAS_W, self.CANVAS_H), Image.LANCZOS)

    def _fit(self, img):
        """Scale proportionally to fit within the canvas without distortion."""
        scale = min(self.CANVAS_W / img.width, self.CANVAS_H / img.height)
        return img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)

    def _decode(self, b64_str):
        return io.BytesIO(base64.b64decode(b64_str))

    def _load_assets(self):
        # Idle background
        self.idle_image = ImageTk.PhotoImage(self._resize(Image.open(self._decode(IDLE_PNG))))

        # Running GIF
        running_gif = Image.open(self._decode(RUNNING_GIF))
        self.running_gif_delay = running_gif.info.get("duration", 60)
        for i in range(running_gif.n_frames):
            running_gif.seek(i)
            self.running_frames.append(ImageTk.PhotoImage(self._fit(running_gif.copy().convert("RGBA"))))

        # Times-up background
        self.bg_image = ImageTk.PhotoImage(self._resize(Image.open(self._decode(TIMES_UP_PNG))))

        # Times-up animation GIF
        anim_gif = Image.open(self._decode(ANIMATION_GIF))
        self.gif_delay = anim_gif.info.get("duration", 100)
        for i in range(anim_gif.n_frames):
            anim_gif.seek(i)
            frame = self._fit(anim_gif.copy().convert("RGBA"))
            self.gif_frames.append(ImageTk.PhotoImage(frame))
            self.gif_frames_flipped.append(ImageTk.PhotoImage(frame.transpose(Image.FLIP_LEFT_RIGHT)))

        # Write alert.wav to a temp file (winsound needs a file path)
        self._alert_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self._alert_wav.write(base64.b64decode(ALERT_WAV))
        self._alert_wav.close()
        self._alert_path = self._alert_wav.name

    def _build_ui(self):
        # Main canvas — used for all states
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Canvas items (created once, shown/hidden per state)
        self.canvas_bg = self.canvas.create_image(0, 0, anchor="nw")
        self.canvas_timer = self.canvas.create_text(0, 0, text="", font=("Segoe UI", 48, "bold"), fill="white")
        self.canvas_gif_left = self.canvas.create_image(0, 0)
        self.canvas_gif_right = self.canvas.create_image(0, 0)
        self.canvas_running_gif = self.canvas.create_image(0, 0)

        # Duration picker
        self.frame_top = ttk.Frame(self.root, padding=10)
        self.frame_top.pack(fill="x")
        ttk.Label(self.frame_top, text="Minutes:", font=("Segoe UI", 12)).pack(side="left")
        self.minutes_var = tk.StringVar(value="40")
        ttk.Entry(self.frame_top, textvariable=self.minutes_var, width=5, font=("Segoe UI", 12)).pack(side="left", padx=(10, 0))

        # Status
        self.status_label = ttk.Label(self.root, text="Ready", font=("Segoe UI", 11), foreground="gray")
        self.status_label.pack()

        # Buttons
        frame_btn = ttk.Frame(self.root, padding=(20, 10))
        frame_btn.pack(fill="x")
        self.start_btn = ttk.Button(frame_btn, text="Start", command=self._start)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=5)
        self.stop_btn = ttk.Button(frame_btn, text="Stop", command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=5)

    def _show_idle(self):
        self.gif_animating = False
        self.running_gif_animating = False
        self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H)
        self.canvas.itemconfig(self.canvas_bg, image=self.idle_image)
        self.canvas.coords(self.canvas_bg, 0, 0)
        # Hide everything else
        self.canvas.itemconfig(self.canvas_timer, text="")
        self.canvas.itemconfig(self.canvas_gif_left, image="")
        self.canvas.itemconfig(self.canvas_gif_right, image="")
        self.canvas.itemconfig(self.canvas_running_gif, image="")
        # Show duration picker
        self.frame_top.pack(fill="x", after=self.canvas)
        self.root.geometry("")

    def _show_running(self):
        self.gif_animating = False
        self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H)
        # Hide idle background and times-up items
        self.canvas.itemconfig(self.canvas_bg, image="")
        self.canvas.itemconfig(self.canvas_timer, text="")
        self.canvas.itemconfig(self.canvas_gif_left, image="")
        self.canvas.itemconfig(self.canvas_gif_right, image="")
        # Hide duration picker while running
        self.frame_top.pack_forget()
        # Start running gif animation as the background
        self.running_gif_animating = True
        self.running_frame_index = 0
        self.canvas.coords(self.canvas_running_gif, self.CANVAS_W // 2, self.CANVAS_H // 2)
        self._animate_running_gif()
        self.root.geometry("")

    def _show_times_up(self):
        self.running_gif_animating = False
        self.canvas.itemconfig(self.canvas_running_gif, image="")
        self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H)
        self.canvas.itemconfig(self.canvas_bg, image=self.bg_image)
        self.canvas.coords(self.canvas_bg, 0, 0)
        # Position GIFs and timer
        mid_x, mid_y = self.CANVAS_W // 2, self.CANVAS_H // 2
        self.canvas.coords(self.canvas_gif_left, mid_x - 150, mid_y)
        self.canvas.coords(self.canvas_timer, mid_x, mid_y)
        self.canvas.coords(self.canvas_gif_right, mid_x + 150, mid_y)
        self.canvas.itemconfig(self.canvas_timer, text="00:00")
        # Show duration picker again
        self.frame_top.pack(fill="x", after=self.canvas)
        # Start animation
        self.gif_animating = True
        self.gif_frame_index = 0
        self._animate_gif()
        self.root.geometry("")

    def _setup_tray(self):
        icon_image = Image.open(self._decode(TRAY_ICON_PNG))
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._restore_from_tray, default=True),
            pystray.MenuItem("Quit", self._quit),
        )
        self.tray_icon = pystray.Icon("break_timer", icon_image, "Break Timer", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _on_minimize(self, event):
        if self.root.state() == "iconic":
            self.root.withdraw()

    def _quit_app(self):
        self.running = False
        self.gif_animating = False
        self.running_gif_animating = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()

    def _restore_from_tray(self, icon=None, item=None):
        self.root.after(0, self._show_window)

    def _show_window(self):
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()
        self.root.after(300, lambda: self.root.attributes("-topmost", False))

    def _quit(self, icon=None, item=None):
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def _format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _start(self):
        try:
            minutes = int(self.minutes_var.get())
        except ValueError:
            self.status_label.config(text="Enter a valid number", foreground="red")
            return
        self.remaining = minutes * 60
        self.running = True
        self._show_running()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="Running...", foreground="green")
        threading.Thread(target=self._tick, daemon=True).start()

    def _stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Stopped", foreground="gray")
        self._show_idle()

    def _tick(self):
        while self.running and self.remaining > 0:
            self.root.after(0, self._update_display)
            time.sleep(1)
            self.remaining -= 1

        if self.running:
            self.running = False
            self.root.after(0, self._times_up)

    def _update_display(self):
        self.status_label.config(text=self._format_time(self.remaining))

    def _times_up(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Time for a break!", foreground="red")

        self._show_times_up()

        # Force window to front from tray
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()

        # Play alert sound
        winsound.PlaySound(self._alert_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

        # Keep on top briefly, then allow normal behavior
        self.root.after(3000, lambda: self.root.attributes("-topmost", False))

    def _animate_gif(self):
        if not self.gif_animating:
            return
        frame = self.gif_frames[self.gif_frame_index]
        frame_flipped = self.gif_frames_flipped[self.gif_frame_index]
        self.canvas.itemconfig(self.canvas_gif_left, image=frame)
        self.canvas.itemconfig(self.canvas_gif_right, image=frame_flipped)
        self.gif_frame_index = (self.gif_frame_index + 1) % len(self.gif_frames)
        self.root.after(self.gif_delay, self._animate_gif)

    def _animate_running_gif(self):
        if not self.running_gif_animating:
            return
        frame = self.running_frames[self.running_frame_index]
        self.canvas.itemconfig(self.canvas_running_gif, image=frame)
        self.running_frame_index = (self.running_frame_index + 1) % len(self.running_frames)
        self.root.after(self.running_gif_delay, self._animate_running_gif)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    BreakTimer().run()
