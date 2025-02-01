import pynput.keyboard
import datetime
import time
import os
import threading
import json
from collections import defaultdict

# Remove KEYS_TO_RECORD set since we'll record all keys
# Initialize data structure for logging
log_data = {
    "keyboard_events": [],
    "mouse_events": [],
    "mouse_positions": []
}

# Mouse recording
mouse_log = ""

# Keyboard recording
currently_pressed = set()  # Keep track of currently pressed keys
last_mouse_pos = (0, 0)
mouse_position_lock = threading.Lock()

# Add a new variable to track recording start time
recording_start_time = None

# Add a global variable for log filename
log_filename = None

def get_relative_timestamp():
    """Get timestamp relative to recording start time"""
    if recording_start_time is None:
        return 0.0
    return time.time() - recording_start_time

def on_press(key):
    # Record all keys
    currently_pressed.add(str(key))
    pressed_chars = sorted(list(currently_pressed))
    event = {
        "type": "press",
        "keys": pressed_chars,
        "timestamp": get_relative_timestamp()
    }
    log_data["keyboard_events"].append(event)

def on_release(key):
    key_str = str(key)
    if key_str in currently_pressed:
        currently_pressed.remove(key_str)
        event = {
            "type": "release",
            "key": key_str,
            "timestamp": get_relative_timestamp()
        }
        log_data["keyboard_events"].append(event)
    if key == pynput.keyboard.Key.esc:
        return False

def on_click(x, y, button, pressed):
    event = {
        "type": "click",
        "action": "press" if pressed else "release",
        "button": str(button),
        "position": {"x": x, "y": y},
        "timestamp": get_relative_timestamp()
    }
    log_data["mouse_events"].append(event)

def on_move(x, y):
    global last_mouse_pos
    with mouse_position_lock:
        last_mouse_pos = (x, y)

def on_scroll(x, y, dx, dy):
    event = {
        "type": "scroll",
        "delta": {"dx": dx, "dy": dy},
        "position": {"x": x, "y": y},
        "timestamp": get_relative_timestamp()
    }
    log_data["mouse_events"].append(event)

def record_mouse_position():
    frame_interval = 1.0 / 60  # 60 FPS
    while True:
        start_time = time.time()
        
        with mouse_position_lock:
            x, y = last_mouse_pos
        
        position_data = {
            "position": {"x": x, "y": y},
            "timestamp": get_relative_timestamp()
        }
        log_data["mouse_positions"].append(position_data)
        
        elapsed = time.time() - start_time
        sleep_time = max(0, frame_interval - elapsed)
        time.sleep(sleep_time)

def save_log(video_filename=None):
    """Save log as JSONL by appending to existing file"""
    global log_filename
    current_time = get_relative_timestamp()
    
    # Set log filename if not set yet
    if video_filename and not log_filename:
        log_filename = video_filename.replace(".mp4", "_log.jsonl")
    
    # Prepare the log entry
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "relative_timestamp": current_time,
        "keyboard_events": log_data["keyboard_events"],
        "mouse_events": log_data["mouse_events"],
        "mouse_positions": log_data["mouse_positions"]
    }
    
    # Calculate statistics
    stats = {
        "keyboard_events_count": len(log_data["keyboard_events"]),
        "mouse_clicks_count": len([e for e in log_data["mouse_events"] if e["type"] == "click"]),
        "mouse_scrolls_count": len([e for e in log_data["mouse_events"] if e["type"] == "scroll"]),
        "mouse_positions_count": len(log_data["mouse_positions"])
    }
    log_entry["stats"] = stats
    
    if video_filename:
        log_entry["video_file"] = video_filename
        log_entry["recording_duration"] = current_time
    
    # Only save if we have a log filename
    if log_filename:
        # Append the log entry to the file
        with open(log_filename, "a", encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Print statistics
        print(f"\nLog statistics at {current_time:.1f}s:")
        print(f"  Keyboard events: {stats['keyboard_events_count']}")
        print(f"  Mouse clicks: {stats['mouse_clicks_count']}")
        print(f"  Mouse scrolls: {stats['mouse_scrolls_count']}")
        print(f"  Mouse positions: {stats['mouse_positions_count']}")
        print(f"Log appended to {log_filename}")
    else:
        print("Warning: No log file specified yet, data not saved")
    
    # Clear the current logs after saving
    log_data["keyboard_events"].clear()
    log_data["mouse_events"].clear()
    log_data["mouse_positions"].clear()

def start_recording():
    """Initialize recording state"""
    global recording_start_time
    recording_start_time = time.time()

# Run the listener in a separate thread for background operation
def start_listener():
    with pynput.keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()

# Start mouse listener in a separate thread
def start_mouse_listener():
    with pynput.mouse.Listener(
            on_click=on_click,
            on_move=on_move,
            on_scroll=on_scroll) as listener:
        listener.join()

if __name__ == '__main__':
    # Start mouse position recording thread (60 FPS)
    mouse_position_thread = threading.Thread(target=record_mouse_position)
    mouse_position_thread.daemon = True
    mouse_position_thread.start()

    # Start mouse event listener thread
    mouse_listener_thread = threading.Thread(target=start_mouse_listener)
    mouse_listener_thread.daemon = True
    mouse_listener_thread.start()

    # Start keyboard listener thread
    listener_thread = threading.Thread(target=start_listener)
    listener_thread.daemon = True
    listener_thread.start()

    try:
        while True:
            time.sleep(60)  # Save the log every minute
            save_log()

    except KeyboardInterrupt:
        print("Recording stopped.")
        save_log()
    except Exception as e:
        print(f"An error occurred: {e}")
        save_log()
    finally:
        print("Exiting...")
