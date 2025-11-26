"""
Headless entrypoint that reuses the legacy recorder logic (backend_legacy) plus OBS control.
"""

import time
from pathlib import Path

from obs_control import OBSRecorder

HOST = "localhost"
PORT = 4455
PASSWORD = ""
SCENE = "screen"
OUTPUT_DIR = Path("recordings").resolve()
INTERVAL = 10


def main() -> None:
    recorder = OBSRecorder(
        host=HOST,
        port=PORT,
        password=PASSWORD,
        scene=SCENE,
        output_dir=str(OUTPUT_DIR),
    )
    try:
        recorder.connect()
        full_path, video_filename = recorder.start_recording()
        if not full_path:
            return
        while True:
            time.sleep(INTERVAL)
            # backend_legacy handles periodic logging via save_log in obs_control paths
            from backend_legacy import save_log

            save_log()
    except KeyboardInterrupt:
        print("\nRecording stopped by user")
    except Exception as exc:
        print(f"Error: {exc}")
    finally:
        recorder.stop_recording()
        recorder.disconnect()


if __name__ == "__main__":
    main()
