import threading

import pystray


class TrayManager:
    def __init__(self, root, icon_image, on_restore, on_quit):
        self._root = root
        self._icon = pystray.Icon(
            "neco_arc_timer", icon_image, "Neco-Arc Timer",
            pystray.Menu(
                pystray.MenuItem("Show", lambda *_: root.after(0, on_restore), default=True),
                pystray.MenuItem("Quit", lambda *_: on_quit()),
            ),
        )
        root.bind("<Unmap>", self._on_minimize)
        threading.Thread(target=self._icon.run, daemon=True).start()

    @property
    def title(self):
        return self._icon.title

    @title.setter
    def title(self, value):
        self._icon.title = value

    def stop(self):
        self._icon.stop()

    def _on_minimize(self, event):
        if self._root.state() == "iconic":
            self._root.withdraw()
