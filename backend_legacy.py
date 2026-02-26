import datetime
import json
import threading
import time
from pathlib import Path
from typing import Optional

import keyboard
import ctypes
from ctypes import wintypes

# --- Timer Resolution Setup ---
# This forces Windows to use 1ms timer precision, which is critical for 60Hz stability.
winmm = ctypes.WinDLL("winmm")
winmm.timeBeginPeriod(1)

if not hasattr(wintypes, "HCURSOR"):
    wintypes.HCURSOR = wintypes.HANDLE

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# Pointer-sized (works on 32-bit + 64-bit Windows)
LRESULT = ctypes.c_ssize_t 

# ---- Win32 constants ----
WM_INPUT = 0x00FF
PM_REMOVE = 0x0001
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIDEV_INPUTSINK = 0x00000100
MOUSE_MOVE_ABSOLUTE = 0x0001

RI_MOUSE_LEFT_BUTTON_DOWN   = 0x0001
RI_MOUSE_LEFT_BUTTON_UP     = 0x0002
RI_MOUSE_RIGHT_BUTTON_DOWN  = 0x0004
RI_MOUSE_RIGHT_BUTTON_UP    = 0x0008
RI_MOUSE_MIDDLE_BUTTON_DOWN = 0x0010
RI_MOUSE_MIDDLE_BUTTON_UP   = 0x0020
RI_MOUSE_BUTTON_4_DOWN      = 0x0040
RI_MOUSE_BUTTON_4_UP        = 0x0080
RI_MOUSE_BUTTON_5_DOWN      = 0x0100
RI_MOUSE_BUTTON_5_UP        = 0x0200
RI_MOUSE_WHEEL               = 0x0400
RI_MOUSE_HWHEEL              = 0x0800
WHEEL_DELTA = 120

# ---- Win32 structs ----
class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]

class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]

class _RAWMOUSE_BUTTONS(ctypes.Structure):
    _fields_ = [
        ("usButtonFlags", wintypes.USHORT),
        ("usButtonData", wintypes.USHORT),
    ]

class _RAWMOUSE_BUTTONS_UNION(ctypes.Union):
    _fields_ = [
        ("ulButtons", wintypes.ULONG),
        ("buttons", _RAWMOUSE_BUTTONS),
    ]

class RAWMOUSE(ctypes.Structure):
    _anonymous_ = ("uButtons",)
    _fields_ = [
        ("usFlags", wintypes.USHORT),
        ("uButtons", _RAWMOUSE_BUTTONS_UNION),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    ]

class _RAWINPUT_DATA(ctypes.Union):
    _fields_ = [("mouse", RAWMOUSE)]

class RAWINPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data", _RAWINPUT_DATA),
    ]

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]

WNDPROCTYPE = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.GetRawInputData.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPVOID, ctypes.POINTER(wintypes.UINT), wintypes.UINT]
user32.GetRawInputData.restype = wintypes.UINT
user32.RegisterRawInputDevices.argtypes = [ctypes.POINTER(RAWINPUTDEVICE), wintypes.UINT, wintypes.UINT]
user32.RegisterRawInputDevices.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.PeekMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
user32.PeekMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
]

class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROCTYPE),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]

user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASS)]
user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
user32.DestroyWindow.argtypes = [wintypes.HWND]

class RawInputMouseThread(threading.Thread):
    def __init__(self, on_delta, on_click, on_wheel, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.on_delta = on_delta
        self.on_click = on_click
        self.on_wheel = on_wheel
        self.stop_event = stop_event
        self.hwnd = None
        self._wndproc = None
        self._class_name = "RawInputMouseSink"

    def run(self):
        hInstance = kernel32.GetModuleHandleW(None)

        @WNDPROCTYPE
        def wndproc(hwnd, msg, wParam, lParam):
            if msg == WM_INPUT:
                self._handle_wm_input(lParam)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wParam, lParam)

        self._wndproc = wndproc
        wc = WNDCLASS()
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = hInstance
        wc.lpszClassName = self._class_name

        atom = user32.RegisterClassW(ctypes.byref(wc))
        HWND_MESSAGE = wintypes.HWND(-3)
        self.hwnd = user32.CreateWindowExW(0, self._class_name, self._class_name, 0, 0, 0, 0, 0, HWND_MESSAGE, None, hInstance, None)

        rid = RAWINPUTDEVICE()
        rid.usUsagePage = 0x01
        rid.usUsage = 0x02
        rid.dwFlags = RIDEV_INPUTSINK
        rid.hwndTarget = self.hwnd
        user32.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE))

        msg = MSG()
        while not self.stop_event.is_set():
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.001)

        user32.DestroyWindow(self.hwnd)
        user32.UnregisterClassW(self._class_name, hInstance)

    def _handle_wm_input(self, hRawInput_lparam):
        dwSize = wintypes.UINT(0)
        user32.GetRawInputData(wintypes.HANDLE(hRawInput_lparam), RID_INPUT, None, ctypes.byref(dwSize), ctypes.sizeof(RAWINPUTHEADER))
        
        buf = ctypes.create_string_buffer(dwSize.value)
        user32.GetRawInputData(wintypes.HANDLE(hRawInput_lparam), RID_INPUT, buf, ctypes.byref(dwSize), ctypes.sizeof(RAWINPUTHEADER))
        
        raw = ctypes.cast(buf, ctypes.POINTER(RAWINPUT)).contents
        if raw.header.dwType != RIM_TYPEMOUSE: return
        m = raw.mouse
        dx, dy = int(m.lLastX), int(m.lLastY)

        if m.usFlags & MOUSE_MOVE_ABSOLUTE:
            dx, dy = 0, 0

        if dx or dy:
            self.on_delta(dx, dy)

        bf = int(m.buttons.usButtonFlags)
        bd = int(m.buttons.usButtonData)

        def cursor_pos():
            pt = POINT()
            if user32.GetCursorPos(ctypes.byref(pt)): return int(pt.x), int(pt.y)
            return 0, 0

        def emit_click(name, action):
            x, y = cursor_pos()
            self.on_click(name, action, x, y)

        if bf & RI_MOUSE_LEFT_BUTTON_DOWN:   emit_click("left", "press")
        if bf & RI_MOUSE_LEFT_BUTTON_UP:     emit_click("left", "release")
        if bf & RI_MOUSE_RIGHT_BUTTON_DOWN:  emit_click("right", "press")
        if bf & RI_MOUSE_RIGHT_BUTTON_UP:    emit_click("right", "release")
        if bf & RI_MOUSE_MIDDLE_BUTTON_DOWN: emit_click("middle", "press")
        if bf & RI_MOUSE_MIDDLE_BUTTON_UP:   emit_click("middle", "release")
        if bf & RI_MOUSE_WHEEL:
            wheel = ctypes.c_short(bd).value
            self.on_wheel("vertical", wheel / WHEEL_DELTA, wheel)

# ---- Recording Logic ----
mouse_accum_lock = threading.Lock()
mouse_accum_dx = 0
mouse_accum_dy = 0

log_data = {"keyboard_events": [], "mouse_events": [], "mouse_positions": []}
log_data_lock = threading.Lock()
recording_start_time = None
recording_start_perf = None
log_file_path = None
log_video_file = None
currently_pressed = set()
raw_mouse_stop = threading.Event()
raw_mouse_thread = None
mouse_delta_thread = None
keyboard_hook = None

def get_relative_timestamp() -> float:
    if recording_start_perf is not None:
        return time.perf_counter() - recording_start_perf
    return time.time() - (recording_start_time or time.time())

def set_recording_start(start_perf: Optional[float] = None, start_wall: Optional[float] = None) -> None:
    global recording_start_time, recording_start_perf
    recording_start_perf = start_perf if start_perf is not None else time.perf_counter()
    recording_start_time = start_wall if start_wall is not None else time.time()

def start_recording() -> None:
    global log_file_path, log_video_file, mouse_accum_dx, mouse_accum_dy
    set_recording_start()
    with mouse_accum_lock:
        mouse_accum_dx = 0
        mouse_accum_dy = 0
    with log_data_lock:
        log_data["keyboard_events"] = []
        log_data["mouse_events"] = []
        log_data["mouse_positions"] = []
    currently_pressed.clear()
    log_file_path = None
    log_video_file = None

def save_log(video_path: Optional[str] = None) -> None:
    global log_file_path, log_video_file
    if video_path:
        video_file = Path(video_path)
        log_file_path = video_file.with_name(f"{video_file.stem}_log.jsonl")
        log_video_file = video_file.name
    if not log_file_path:
        return

    with log_data_lock:
        keyboard_events = list(log_data["keyboard_events"])
        mouse_events = list(log_data["mouse_events"])
        mouse_positions = list(log_data["mouse_positions"])
        log_data["keyboard_events"].clear()
        log_data["mouse_events"].clear()
        log_data["mouse_positions"].clear()

    duration = get_relative_timestamp()
    payload = {
        "timestamp": datetime.datetime.now().isoformat(),
        "relative_timestamp": duration,
        "keyboard_events": keyboard_events,
        "mouse_events": mouse_events,
        "mouse_positions": mouse_positions,
        "stats": {
            "keyboard_events_count": len(keyboard_events),
            "mouse_clicks_count": len([e for e in mouse_events if e.get("type") == "click"]),
            "mouse_scrolls_count": len([e for e in mouse_events if e.get("type") == "scroll"]),
            "mouse_positions_count": len(mouse_positions),
        },
        "video_file": log_video_file,
        "recording_duration": duration,
    }

    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    with log_file_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")

def raw_on_delta(dx: int, dy: int) -> None:
    global mouse_accum_dx, mouse_accum_dy
    with mouse_accum_lock:
        mouse_accum_dx += dx
        mouse_accum_dy += dy

def raw_on_click(button: str, action: str, x: int, y: int) -> None:
    event = {"type": "click", "action": action, "button": button, "position": {"x": x, "y": y}, "timestamp": get_relative_timestamp()}
    with log_data_lock: log_data["mouse_events"].append(event)

def raw_on_wheel(axis: str, steps: float, raw_delta: int) -> None:
    event = {"type": "scroll", "axis": axis, "steps": steps, "raw_delta": raw_delta, "timestamp": get_relative_timestamp()}
    with log_data_lock: log_data["mouse_events"].append(event)

def on_keyboard_event(event: keyboard.KeyboardEvent) -> None:
    key_str = (event.name or f"scan_{event.scan_code}").lower()
    if event.event_type == "down":
        if key_str in currently_pressed: return
        currently_pressed.add(key_str)
        evt = {"type": "press", "keys": sorted(list(currently_pressed)), "timestamp": get_relative_timestamp()}
    else:
        if key_str in currently_pressed: currently_pressed.remove(key_str)
        evt = {"type": "release", "key": key_str, "timestamp": get_relative_timestamp()}
    with log_data_lock: log_data["keyboard_events"].append(evt)

def record_mouse_delta_30hz(start_perf: float) -> None:
    """High-precision 30Hz sampler aligned to a monotonic start time."""
    global mouse_accum_dx, mouse_accum_dy
    frame_interval = 1.0 / 30.0
    frame_index = 0
    next_time = start_perf

    while not raw_mouse_stop.is_set():
        # High-precision wait: sleep for most of the time, busy-wait for the last tiny bit
        while True:
            now = time.perf_counter()
            remaining = next_time - now
            if remaining <= 0:
                break
            if remaining > 0.002:
                time.sleep(0.001)

        now = time.perf_counter()
        if now - next_time > frame_interval:
            frame_index = int((now - start_perf) / frame_interval)
            next_time = start_perf + (frame_index * frame_interval)

        current_timestamp = frame_index * frame_interval
        
        with mouse_accum_lock:
            dx, dy = mouse_accum_dx, mouse_accum_dy
            mouse_accum_dx = 0
            mouse_accum_dy = 0

        entry = {"delta": {"dx": dx, "dy": dy}, "timestamp": current_timestamp, "frame_index": frame_index}
        with log_data_lock:
            log_data["mouse_positions"].append(entry)

        frame_index += 1
        next_time = start_perf + (frame_index * frame_interval)

def start_input_threads(start_perf: Optional[float] = None, start_wall: Optional[float] = None) -> None:
    global keyboard_hook, raw_mouse_thread, mouse_delta_thread
    raw_mouse_stop.clear()
    set_recording_start(start_perf=start_perf, start_wall=start_wall)

    mouse_delta_thread = threading.Thread(
        target=record_mouse_delta_30hz,
        args=(recording_start_perf or time.perf_counter(),),
        daemon=True,
    )
    mouse_delta_thread.start()
    
    raw_mouse_thread = RawInputMouseThread(raw_on_delta, raw_on_click, raw_on_wheel, raw_mouse_stop)
    raw_mouse_thread.start()
    keyboard_hook = keyboard.hook(on_keyboard_event)


def stop_input_threads() -> None:
    """Stop background mouse/key capture threads and hooks."""
    global keyboard_hook, raw_mouse_thread, mouse_delta_thread

    raw_mouse_stop.set()

    if keyboard_hook is not None:
        try:
            keyboard.unhook(keyboard_hook)
        except Exception:
            pass
        keyboard_hook = None

    if raw_mouse_thread is not None:
        raw_mouse_thread.join(timeout=1.0)
        raw_mouse_thread = None

    if mouse_delta_thread is not None:
        mouse_delta_thread.join(timeout=1.0)
        mouse_delta_thread = None

if __name__ == "__main__":
    print("Recording at precise 30Hz. Press Ctrl+C to stop.")
    set_recording_start()
    start_input_threads(recording_start_perf, recording_start_time)
    try:
        while True:
            time.sleep(1)
            with log_data_lock:
                count = len(log_data["mouse_positions"])
                # Calculate effective frequency over the last second
                print(f"Captured {count} mouse frames... (~{count/max(1, get_relative_timestamp()):.1f} Hz)")
    except KeyboardInterrupt:
        raw_mouse_stop.set()
        winmm.timeEndPeriod(1) # Cleanup timer resolution
        print("Stopped.")
