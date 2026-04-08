# ⓛωⓛ

A Nerco-Arc break reminder timer to help me with my hand injury.

## Features

- Configurable countdown timer (default: 40 minutes)
- Minimizes to the system tray notification area
- Pops up and plays an alert sound when the timer finishes

## Requirements

- Python 3.10+
- Dependencies:
  - [Pillow](https://pypi.org/project/Pillow/)
  - [pystray](https://pypi.org/project/pystray/)

Install dependencies:

```
pip install Pillow pystray
```

## Project Structure

| File               | Description                                           |
|--------------------|-------------------------------------------------------|
| `neco_timer.py`    | Main application script and timer orchestration       |
| `core/ui.py`       | Canvas, widgets, and visual state transitions         |
| `core/tray.py`     | System tray icon and minimize-to-tray behavior        |
| `core/media.py`    | Asset loading (images, GIFs, sounds) and animation    |
| `core/assets.py`   | All images and audio embedded as base64 constants     |

## Usage

```
python neco_timer.py
```

- Set the desired minutes and click **Start**
- The window can be minimized to the system tray using the minimize button
- When the timer finishes, the window pops up with an alert
- Close the window with the X button to quit
