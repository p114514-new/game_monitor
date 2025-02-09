__all__ = ['record_mouse_events', 'record_mouse_position', 
           'start_recording', 'save_log', 'init_keyboard_listener']

import datetime
import time
import os
import threading
import json
import keyboard
import win32api
import win32con
import win32gui
import ctypes
from ctypes import windll

# Initialize data structure for logging
log_data = {
    "keyboard_events": [],
    "mouse_events": [],
    "mouse_positions": []
}

# Mouse recording
last_mouse_pos = (0, 0)
mouse_position_lock = threading.Lock()

# Add variables to track recording start time and log filename
recording_start_time = None
log_filename = None

# Add screen info as global variables
SCREEN_WIDTH = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
SCREEN_HEIGHT = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

def get_relative_timestamp():
    """Get timestamp relative to recording start time"""
    if recording_start_time is None:
        return 0.0
    return time.time() - recording_start_time

def on_key_event(event):
    """Handle keyboard events"""
    event_type = "press" if event.event_type == "down" else "release"
    event_data = {
        "type": event_type,
        "key": str(event.name),
        "timestamp": get_relative_timestamp()
    }
    log_data["keyboard_events"].append(event_data)

def get_mouse_position():
    """Get current mouse position using multiple methods"""
    try:
        # 尝试使用 win32api 获取物理鼠标位置
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        point = POINT()
        ctypes.windll.user32.GetPhysicalCursorPos(ctypes.byref(point))
        x, y = point.x, point.y
        
        # 验证坐标是否在合理范围内
        if 0 <= x <= SCREEN_WIDTH and 0 <= y <= SCREEN_HEIGHT:
            return (x, y)
            
        # 如果坐标不合理，尝试使用其他方法
        cursor_info = win32gui.GetCursorInfo()
        x, y = cursor_info[2]
        
        if 0 <= x <= SCREEN_WIDTH and 0 <= y <= SCREEN_HEIGHT:
            return (x, y)
            
        return None  # 如果都获取不到合理的位置，返回 None
        
    except Exception as e:
        print(f"Error getting mouse position: {e}")
        return None

def get_mouse_delta():
    """Get mouse movement using GetAsyncKeyState"""
    dx = 0
    dy = 0
    
    # 检查各个方向键的状态
    if win32api.GetAsyncKeyState(win32con.VK_LEFT) & 0x8000:
        dx -= 1
    if win32api.GetAsyncKeyState(win32con.VK_RIGHT) & 0x8000:
        dx += 1
    if win32api.GetAsyncKeyState(win32con.VK_UP) & 0x8000:
        dy -= 1
    if win32api.GetAsyncKeyState(win32con.VK_DOWN) & 0x8000:
        dy += 1
    
    return dx, dy

def record_mouse_position(mouse_boundary_threshold, fps=60, debug=True, print_interval=100):
    """Record mouse movement with configurable parameters"""
    print("Starting mouse movement tracking...")
    
    BOUNDARY_THRESHOLD = mouse_boundary_threshold
    
    def get_safe_reset_position(current_x, current_y):
        """根据当前位置计算最近的安全重置位置"""
        if current_x < BOUNDARY_THRESHOLD:
            reset_x = BOUNDARY_THRESHOLD + 10
        elif current_x > SCREEN_WIDTH - BOUNDARY_THRESHOLD:
            reset_x = SCREEN_WIDTH - BOUNDARY_THRESHOLD - 10
        else:
            reset_x = current_x
            
        if current_y < BOUNDARY_THRESHOLD:
            reset_y = BOUNDARY_THRESHOLD + 10
        elif current_y > SCREEN_HEIGHT - BOUNDARY_THRESHOLD:
            reset_y = SCREEN_HEIGHT - BOUNDARY_THRESHOLD - 10
        else:
            reset_y = current_y
            
        return reset_x, reset_y
    
    # 保存上一次的位置
    last_x, last_y = win32api.GetCursorPos()
    
    # 累积的总移动量
    total_dx = 0
    total_dy = 0
    
    while True:
        try:
            # 获取当前鼠标位置
            current_x, current_y = win32api.GetCursorPos()
            
            # 计算移动增量
            dx = current_x - last_x
            dy = current_y - last_y
            
            if dx != 0 or dy != 0:
                # 更新累积移动量
                total_dx += dx
                total_dy += dy
                
                position_data = {
                    "delta": {
                        "dx": dx,
                        "dy": dy
                    },
                    "cumulative": {
                        "x": total_dx,
                        "y": total_dy
                    },
                    "timestamp": get_relative_timestamp()
                }
                log_data["mouse_positions"].append(position_data)
                
                # 使用配置中的打印间隔
                if len(log_data["mouse_positions"]) % print_interval == 0:
                    if debug:
                        print(f"Mouse delta: dx={dx}, dy={dy}")
                
                # 只在非常接近边界时重置位置
                if (current_x < BOUNDARY_THRESHOLD or 
                    current_x > SCREEN_WIDTH - BOUNDARY_THRESHOLD or
                    current_y < BOUNDARY_THRESHOLD or 
                    current_y > SCREEN_HEIGHT - BOUNDARY_THRESHOLD):
                    try:
                        # 重置到最近的安全位置
                        reset_x, reset_y = get_safe_reset_position(current_x, current_y)
                        win32api.SetCursorPos((reset_x, reset_y))
                        last_x = reset_x
                        last_y = reset_y
                    except:
                        pass
                else:
                    last_x = current_x
                    last_y = current_y
            
            time.sleep(1/fps)  # 使用传入的 fps 参数，而不是 global_config
            
        except Exception as e:
            print(f"Error tracking mouse movement: {e}")
            time.sleep(0.1)

def record_mouse_events():
    """Record mouse clicks"""
    LEFT_BUTTON = 0x01
    RIGHT_BUTTON = 0x02
    MIDDLE_BUTTON = 0x04
    
    last_left = win32api.GetKeyState(win32con.VK_LBUTTON)
    last_right = win32api.GetKeyState(win32con.VK_RBUTTON)
    last_middle = win32api.GetKeyState(win32con.VK_MBUTTON)
    
    while True:
        try:
            # Check mouse buttons
            left = win32api.GetKeyState(win32con.VK_LBUTTON)
            right = win32api.GetKeyState(win32con.VK_RBUTTON)
            middle = win32api.GetKeyState(win32con.VK_MBUTTON)
            
            x, y = win32api.GetCursorPos()
            
            # Left button
            if left != last_left:
                pressed = left < 0
                event = {
                    "type": "click",
                    "action": "press" if pressed else "release",
                    "button": "Button.left",
                    "position": {"x": x, "y": y},
                    "timestamp": get_relative_timestamp()
                }
                log_data["mouse_events"].append(event)
                last_left = left
                
            # Right button
            if right != last_right:
                pressed = right < 0
                event = {
                    "type": "click",
                    "action": "press" if pressed else "release",
                    "button": "Button.right",
                    "position": {"x": x, "y": y},
                    "timestamp": get_relative_timestamp()
                }
                log_data["mouse_events"].append(event)
                last_right = right
                
            # Middle button
            if middle != last_middle:
                pressed = middle < 0
                event = {
                    "type": "click",
                    "action": "press" if pressed else "release",
                    "button": "Button.middle",
                    "position": {"x": x, "y": y},
                    "timestamp": get_relative_timestamp()
                }
                log_data["mouse_events"].append(event)
                last_middle = middle
            
            time.sleep(0.001)  # Small sleep to prevent high CPU usage
            
        except Exception as e:
            print(f"Error recording mouse events: {e}")
            time.sleep(0.1)

def save_log(logs_dir, video_filename=None, debug=True):
    """Save log with configurable directory"""
    global log_filename
    current_time = get_relative_timestamp()
    
    try:
        if video_filename and not log_filename:
            log_basename = os.path.basename(video_filename) + "_log.jsonl"
            log_filename = os.path.join(logs_dir, log_basename)
            
            os.makedirs(logs_dir, exist_ok=True)
            
            with open(log_filename, "w", encoding='utf-8') as f:
                screen_info = {
                    "type": "screen_info",
                    "width": SCREEN_WIDTH,
                    "height": SCREEN_HEIGHT
                }
                f.write(json.dumps(screen_info) + "\n")
        
        if log_filename:
            with open(log_filename, "a", encoding='utf-8') as f:
                log_entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "relative_timestamp": current_time,
                    "keyboard_events": log_data["keyboard_events"],
                    "mouse_events": log_data["mouse_events"],
                    "mouse_positions": log_data["mouse_positions"]
                }
                f.write(json.dumps(log_entry) + "\n")
            
            if debug:
                print(f"\nLog statistics at {current_time:.1f}s:")
                print(f"  Keyboard events: {len(log_data['keyboard_events'])}")
                print(f"  Mouse clicks: {len([e for e in log_data['mouse_events'] if e['type'] == 'click'])}")
                print(f"  Mouse positions: {len(log_data['mouse_positions'])}")
                print(f"Log appended to {log_filename}")
        
        # 清除当前日志
        log_data["keyboard_events"].clear()
        log_data["mouse_events"].clear()
        log_data["mouse_positions"].clear()
        
    except Exception as e:
        print(f"Error saving log: {e}")

def init_keyboard_listener():
    """Initialize keyboard listener"""
    try:
        keyboard.hook(on_key_event)
        # 不要调用 keyboard.wait()，因为它会阻塞线程
    except Exception as e:
        print(f"Error initializing keyboard listener: {e}")

def start_recording():
    """Initialize recording state"""
    global recording_start_time, log_filename
    recording_start_time = time.time()
    log_filename = None  # 重置日志文件名
    
    # 初始化键盘监听
    init_keyboard_listener()

def start_listener():
    """Start keyboard listener"""
    try:
        keyboard.hook(on_key_event)
        keyboard.wait()  # Keep the listener running
    except Exception as e:
        print(f"Error in keyboard listener: {e}")

if __name__ == '__main__':
    # Start mouse position recording thread
    mouse_position_thread = threading.Thread(target=record_mouse_position)
    mouse_position_thread.daemon = True
    mouse_position_thread.start()

    # Start mouse event recording thread
    mouse_event_thread = threading.Thread(target=record_mouse_events)
    mouse_event_thread.daemon = True
    mouse_event_thread.start()

    # Start keyboard listener thread
    keyboard_thread = threading.Thread(target=start_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()

    try:
        while True:
            time.sleep(10)  # Save the log every 10 seconds
            save_log()

    except KeyboardInterrupt:
        print("Recording stopped.")
        save_log()
    except Exception as e:
        print(f"An error occurred: {e}")
        save_log()
    finally:
        print("Exiting...")
