import tkinter as tk
from tkinter import ttk


class UI:
    def __init__(self, root, canvas_w, canvas_h, on_start, on_stop):
        self.root = root
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h

        # Main canvas
        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Canvas items (created once, shown/hidden per state)
        self.bg = self.canvas.create_image(0, 0, anchor="nw")
        self.timer_text = self.canvas.create_text(0, 0, text="", font=("Segoe UI", 48, "bold"), fill="white")
        self.gif_left = self.canvas.create_image(0, 0)
        self.gif_right = self.canvas.create_image(0, 0)
        self.running_gif = self.canvas.create_image(0, 0)

        # Duration picker
        self.frame_top = ttk.Frame(root, padding=10)
        self.frame_top.pack(fill="x")
        ttk.Label(self.frame_top, text="Minutes:", font=("Segoe UI", 12)).pack(side="left")
        self.minutes_var = tk.StringVar(value="40")
        ttk.Entry(self.frame_top, textvariable=self.minutes_var, width=5, font=("Segoe UI", 12)).pack(side="left", padx=(10, 0))

        # Status
        self.status_label = ttk.Label(root, text="Ready", font=("Segoe UI", 11), foreground="gray")
        self.status_label.pack()

        # Buttons
        frame_btn = ttk.Frame(root, padding=(20, 10))
        frame_btn.pack(fill="x")
        self.start_btn = ttk.Button(frame_btn, text="Start", command=on_start)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=5)
        self.stop_btn = ttk.Button(frame_btn, text="Stop", command=on_stop, state="disabled")
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=5)

    def show_idle(self, assets):
        self.canvas.config(width=self.canvas_w, height=self.canvas_h)
        self.canvas.itemconfig(self.bg, image=assets.idle_image)
        self.canvas.coords(self.bg, 0, 0)
        self.canvas.itemconfig(self.timer_text, text="")
        self.canvas.itemconfig(self.gif_left, image="")
        self.canvas.itemconfig(self.gif_right, image="")
        self.canvas.itemconfig(self.running_gif, image="")
        self.frame_top.pack(fill="x", after=self.canvas)
        self.root.geometry("")

    def show_running(self):
        self.canvas.config(width=self.canvas_w, height=self.canvas_h)
        self.canvas.itemconfig(self.bg, image="")
        self.canvas.itemconfig(self.timer_text, text="")
        self.canvas.itemconfig(self.gif_left, image="")
        self.canvas.itemconfig(self.gif_right, image="")
        self.frame_top.pack_forget()
        self.canvas.coords(self.running_gif, self.canvas_w // 2, self.canvas_h // 2)
        self.root.geometry("")

    def show_times_up(self, assets):
        self.canvas.itemconfig(self.running_gif, image="")
        self.canvas.config(width=self.canvas_w, height=self.canvas_h)
        self.canvas.itemconfig(self.bg, image=assets.bg_image)
        self.canvas.coords(self.bg, 0, 0)
        mid_x, mid_y = self.canvas_w // 2, self.canvas_h // 2
        self.canvas.coords(self.gif_left, mid_x - 150, mid_y)
        self.canvas.coords(self.timer_text, mid_x, mid_y)
        self.canvas.coords(self.gif_right, mid_x + 150, mid_y)
        self.canvas.itemconfig(self.timer_text, text="00:00")
        self.frame_top.pack(fill="x", after=self.canvas)
        self.root.geometry("")

    def bring_to_front(self):
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()
        self.root.after(3000, lambda: self.root.attributes("-topmost", False))
