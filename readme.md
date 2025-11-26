# Game Monitor

Desktop UI (`main.py`) to start/stop OBS recording and capture keyboard/mouse telemetry (legacy logic). Headless CLI (`obs.py`) uses the same logic.

## Prerequisites
- Python 3.10+
- OBS Studio with WebSocket server enabled (v5+, default port 4455)

## Install dependencies
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the desktop app
```powershell
python main.py
```
1) Fill OBS host/port/password, scene name (default `screen`), and output directory (default `recordings`).
2) Click **Start Recording**; **Stop Recording** to end. Logs auto-save every 10s to `{video_name}_log.jsonl`.

## Headless mode
```powershell
python obs.py
```
Edit HOST/PORT/PASSWORD/SCENE/OUTPUT_DIR at the top of `obs.py` if needed.

## Build a Windows exe
Install PyInstaller (`pip install pyinstaller`), then:
```powershell
pyinstaller --noconsole --onefile --name GameMonitor main.py
```
Result: `dist\GameMonitor.exe` (double-click to run). Add `--icon path\to\icon.ico` if desired.

## Log format
Each line in `{video_name}_log.jsonl` contains keyboard events, mouse events, sampled positions, stats, and timestamps.

## Notes
- Recording format is whatever OBS is configured to output (e.g., mkv/mp4). No post-conversion is performed.
- Legacy reference code remains under `game_monitor/game_monitor` (unused). Deprecated shims: `input_recorder.py`, `obs_client.py`.
