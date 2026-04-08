import tkinter as tk
import random
import threading
import time
import winsound

from core import load_assets, Animator, TrayManager, UI


class BreakTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Neco-Arc Timer")
        self.root.resizable(False, False)

        self.CANVAS_W = 500
        self.CANVAS_H = 281
        self.running = False
        self.remaining = 0

        self.assets = load_assets(self.CANVAS_W, self.CANVAS_H)
        self.ui = UI(self.root, self.CANVAS_W, self.CANVAS_H, self._start, self._stop)
        self.animator = Animator(self.root, self.ui.canvas, self.assets)
        self.tray = TrayManager(self.root, self.assets.tray_icon_image, self._show_window, self._quit)
        self.root.protocol("WM_DELETE_WINDOW", self._quit_app)
        self.ui.show_idle(self.assets)

    def _show_window(self):
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()
        self.root.after(300, lambda: self.root.attributes("-topmost", False))

    def _quit_app(self):
        self.running = False
        self.animator.stop_all()
        self.tray.stop()
        self.root.destroy()

    def _quit(self):
        self.running = False
        self.tray.stop()
        self.root.after(0, self.root.destroy)

    def _format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _start(self):
        try:
            minutes = int(self.ui.minutes_var.get())
        except ValueError:
            self.ui.status_label.config(text="Enter a valid number", foreground="red")
            return
        self.remaining = minutes * 60
        self._alert_path = random.choice(self.assets.alert_paths)
        self.running = True
        self.animator.stop_all()
        self.ui.show_running()
        self.animator.start_running(self.ui.running_gif)
        self.ui.start_btn.config(state="disabled")
        self.ui.stop_btn.config(state="normal")
        self.ui.status_label.config(text="Running...", foreground="green")
        threading.Thread(target=self._tick, daemon=True).start()

    def _stop(self):
        self.running = False
        self.animator.stop_all()
        self.ui.start_btn.config(state="normal")
        self.ui.stop_btn.config(state="disabled")
        self.ui.status_label.config(text="Stopped", foreground="gray")
        self.tray.title = "Neco-Arc Timer"
        self.ui.show_idle(self.assets)

    def _tick(self):
        while self.running and self.remaining > 0:
            self.root.after(0, self._update_display)
            time.sleep(1)
            self.remaining -= 1
        if self.running:
            self.running = False
            self.root.after(0, self._times_up)

    def _update_display(self):
        time_str = self._format_time(self.remaining)
        self.ui.status_label.config(text=time_str)
        self.tray.title = time_str

    def _times_up(self):
        self.ui.start_btn.config(state="normal")
        self.ui.stop_btn.config(state="disabled")
        self.ui.status_label.config(text="Time for a break!", foreground="red")
        self.tray.title = "Neco-Arc Timer - Time's up!"
        self.animator.stop_all()
        self.ui.show_times_up(self.assets)
        self.animator.start_times_up(self.ui.gif_left, self.ui.gif_right)
        self.ui.bring_to_front()
        winsound.PlaySound(self._alert_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    BreakTimer().run()
