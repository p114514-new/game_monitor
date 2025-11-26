import datetime
import json
import threading
import time
from pathlib import Path
from typing import Optional

import pynput.keyboard
import pynput.mouse

# Data buffers (mirrors original working script)
log_data = {
    "keyboard_events": [],
    "mouse_events": [],
    "mouse_positions": [],
}

currently_pressed = set()
last_mouse_pos = (0, 0)
mouse_position_lock = threading.Lock()

recording_start_time: Optional[float] = None
log_filename: Optional[str] = None

keyboard_listener: Optional[pynput.keyboard.Listener] = None
mouse_listener: Optional[pynput.mouse.Listener] = None
mouse_pos_thread: Optional[threading.Thread] = None


def get_relative_timestamp() -> float:
    if recording_start_time is None:
        return 0.0
    return time.time() - recording_start_time


def on_press(key) -> None:
    currently_pressed.add(str(key))
    pressed_chars = sorted(list(currently_pressed))
    event = {
        "type": "press",
        "keys": pressed_chars,
        "timestamp": get_relative_timestamp(),
    }
    log_data["keyboard_events"].append(event)


def on_release(key) -> Optional[bool]:
    key_str = str(key)
    if key_str in currently_pressed:
        currently_pressed.remove(key_str)
        event = {
            "type": "release",
            "key": key_str,
            "timestamp": get_relative_timestamp(),
        }
        log_data["keyboard_events"].append(event)
    if key == pynput.keyboard.Key.esc:
        return False
    return None


def on_click(x, y, button, pressed) -> None:
    event = {
        "type": "click",
        "action": "press" if pressed else "release",
        "button": str(button),
        "position": {"x": x, "y": y},
        "timestamp": get_relative_timestamp(),
    }
    log_data["mouse_events"].append(event)


def on_move(x, y) -> None:
    global last_mouse_pos
    with mouse_position_lock:
        last_mouse_pos = (x, y)


def on_scroll(x, y, dx, dy) -> None:
    event = {
        "type": "scroll",
        "delta": {"dx": dx, "dy": dy},
        "position": {"x": x, "y": y},
        "timestamp": get_relative_timestamp(),
    }
    log_data["mouse_events"].append(event)


def record_mouse_position() -> None:
    frame_interval = 1.0 / 60  # 60 FPS
    while True:
        start_time = time.time()
        with mouse_position_lock:
            x, y = last_mouse_pos
        position_data = {"position": {"x": x, "y": y}, "timestamp": get_relative_timestamp()}
        log_data["mouse_positions"].append(position_data)
        elapsed = time.time() - start_time
        sleep_time = max(0, frame_interval - elapsed)
        time.sleep(sleep_time)


def save_log(video_filename: Optional[str] = None) -> None:
    """Save log as JSONL by appending to existing file (legacy behavior)."""
    global log_filename
    current_time = get_relative_timestamp()

    if video_filename and not log_filename:
        # Keep same folder as video if a path is provided
        video_path = Path(video_filename)
        stem = video_path.stem
        log_filename = str(video_path.with_name(f"{stem}_log.jsonl"))

    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "relative_timestamp": current_time,
        "keyboard_events": log_data["keyboard_events"],
        "mouse_events": log_data["mouse_events"],
        "mouse_positions": log_data["mouse_positions"],
    }

    stats = {
        "keyboard_events_count": len(log_data["keyboard_events"]),
        "mouse_clicks_count": len([e for e in log_data["mouse_events"] if e["type"] == "click"]),
        "mouse_scrolls_count": len([e for e in log_data["mouse_events"] if e["type"] == "scroll"]),
        "mouse_positions_count": len(log_data["mouse_positions"]),
    }
    log_entry["stats"] = stats

    if video_filename:
        log_entry["video_file"] = Path(video_filename).name
        log_entry["recording_duration"] = current_time

    if log_filename:
        with open(log_filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        print(f"\nLog statistics at {current_time:.1f}s:")
        print(f"  Keyboard events: {stats['keyboard_events_count']}")
        print(f"  Mouse clicks: {stats['mouse_clicks_count']}")
        print(f"  Mouse scrolls: {stats['mouse_scrolls_count']}")
        print(f"  Mouse positions: {stats['mouse_positions_count']}")
        print(f"Log appended to {log_filename}")
    else:
        print("Warning: No log file specified yet, data not saved")

    log_data["keyboard_events"].clear()
    log_data["mouse_events"].clear()
    log_data["mouse_positions"].clear()


def start_recording() -> None:
    global recording_start_time
    global log_filename
    recording_start_time = time.time()
    log_filename = None
    currently_pressed.clear()
    with mouse_position_lock:
        last_mouse_pos = (0, 0)
    # Clear previous session buffers
    log_data["keyboard_events"].clear()
    log_data["mouse_events"].clear()
    log_data["mouse_positions"].clear()


def start_input_threads() -> None:
    global keyboard_listener, mouse_listener, mouse_pos_thread
    if mouse_pos_thread is None:
        mouse_pos_thread = threading.Thread(target=record_mouse_position, daemon=True)
        mouse_pos_thread.start()

    if mouse_listener is None:
        mouse_listener = pynput.mouse.Listener(on_click=on_click, on_move=on_move, on_scroll=on_scroll)
        mouse_listener.daemon = True
        mouse_listener.start()

    if keyboard_listener is None:
        keyboard_listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)
        keyboard_listener.daemon = True
        keyboard_listener.start()
