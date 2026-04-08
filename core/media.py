import base64
import io
import tempfile
from dataclasses import dataclass, field

from PIL import Image, ImageTk

from .assets import (
    IDLE_PNG, RUNNING_GIF, TIMES_UP_PNG,
    ANIMATION_GIF, ALERT_WAV, ALERT2_WAV, ALERT3_WAV, ALERT4_WAV,
    TRAY_ICON_PNG,
)


@dataclass
class Assets:
    idle_image: ImageTk.PhotoImage = None
    bg_image: ImageTk.PhotoImage = None
    running_frames: list = field(default_factory=list)
    running_gif_delay: int = 60
    gif_frames: list = field(default_factory=list)
    gif_frames_flipped: list = field(default_factory=list)
    gif_delay: int = 100
    tray_icon_image: Image.Image = None
    alert_paths: list = field(default_factory=list)


def _decode(b64_str):
    return io.BytesIO(base64.b64decode(b64_str))


def _resize(img, width, height):
    return img.resize((width, height), Image.LANCZOS)


def _fit(img, width, height):
    """Scale proportionally to fit within the given dimensions without distortion."""
    scale = min(width / img.width, height / img.height)
    return img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)


def load_assets(canvas_w, canvas_h):
    """Load all image, GIF, and sound assets. Returns an Assets instance."""
    assets = Assets()

    # Idle background
    assets.idle_image = ImageTk.PhotoImage(_resize(Image.open(_decode(IDLE_PNG)), canvas_w, canvas_h))

    # Running GIF frames
    running_gif = Image.open(_decode(RUNNING_GIF))
    assets.running_gif_delay = running_gif.info.get("duration", 60)
    for i in range(running_gif.n_frames):
        running_gif.seek(i)
        assets.running_frames.append(ImageTk.PhotoImage(_fit(running_gif.copy().convert("RGBA"), canvas_w, canvas_h)))

    # Times-up background
    assets.bg_image = ImageTk.PhotoImage(_resize(Image.open(_decode(TIMES_UP_PNG)), canvas_w, canvas_h))

    # Times-up animation GIF frames
    anim_gif = Image.open(_decode(ANIMATION_GIF))
    assets.gif_delay = anim_gif.info.get("duration", 100)
    for i in range(anim_gif.n_frames):
        anim_gif.seek(i)
        frame = _fit(anim_gif.copy().convert("RGBA"), canvas_w, canvas_h)
        assets.gif_frames.append(ImageTk.PhotoImage(frame))
        assets.gif_frames_flipped.append(ImageTk.PhotoImage(frame.transpose(Image.FLIP_LEFT_RIGHT)))

    # Tray icon (raw PIL image for pystray)
    assets.tray_icon_image = Image.open(_decode(TRAY_ICON_PNG))

    # Alert sounds written to temp files (winsound needs file paths)
    for alert_data in (ALERT_WAV, ALERT2_WAV, ALERT3_WAV, ALERT4_WAV):
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(base64.b64decode(alert_data))
        tmp.close()
        assets.alert_paths.append(tmp.name)

    return assets


class Animator:
    def __init__(self, root, canvas, assets):
        self._root = root
        self._canvas = canvas
        self._assets = assets
        self.gif_animating = False
        self.running_gif_animating = False
        self._gif_frame_index = 0
        self._running_frame_index = 0
        self._left_item = None
        self._right_item = None
        self._running_item = None

    def start_times_up(self, left_item, right_item):
        self.gif_animating = True
        self._gif_frame_index = 0
        self._left_item = left_item
        self._right_item = right_item
        self._animate_gif()

    def start_running(self, item):
        self.running_gif_animating = True
        self._running_frame_index = 0
        self._running_item = item
        self._animate_running()

    def stop_all(self):
        self.gif_animating = False
        self.running_gif_animating = False

    def _animate_gif(self):
        if not self.gif_animating:
            return
        a = self._assets
        self._canvas.itemconfig(self._left_item, image=a.gif_frames[self._gif_frame_index])
        self._canvas.itemconfig(self._right_item, image=a.gif_frames_flipped[self._gif_frame_index])
        self._gif_frame_index = (self._gif_frame_index + 1) % len(a.gif_frames)
        self._root.after(a.gif_delay, self._animate_gif)

    def _animate_running(self):
        if not self.running_gif_animating:
            return
        a = self._assets
        self._canvas.itemconfig(self._running_item, image=a.running_frames[self._running_frame_index])
        self._running_frame_index = (self._running_frame_index + 1) % len(a.running_frames)
        self._root.after(a.running_gif_delay, self._animate_running)
