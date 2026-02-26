import datetime
import threading
import time
from pathlib import Path
from typing import Optional, Tuple

import obsws_python as obs

# Legacy input recorder logic lifted from the original working script.
import backend_legacy as legacy


class OBSRecorder:
    def __init__(
        self,
        host: str,
        port: int,
        password: str,
        scene: str,
        output_dir: str,
        log_interval_seconds: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.scene = scene
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_interval_seconds = log_interval_seconds

        self.client: Optional[obs.ReqClient] = None
        self.recording_active = False
        self._log_thread: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None
        self.current_output_path: Optional[Path] = None

    def connect(self) -> None:
        try:
            self.client = obs.ReqClient(host=self.host, port=self.port, password=self.password)
        except Exception as exc:
            raise RuntimeError(f"Failed to connect to OBS: {exc}") from exc

    def start_recording(self) -> Tuple[Optional[str], Optional[str]]:
        if not self.client:
            raise RuntimeError("Not connected to OBS")
        status = self.client.get_record_status()
        if status.output_active:
            print("Recording is already active")
            return None, None

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename_hint = f"game_recording_{timestamp}"
        # Configure OBS
        self.client.set_record_directory(str(self.output_dir))
        if self.scene:
            try:
                self.client.set_current_program_scene(self.scene)
            except Exception:
                pass
        self._ensure_cfr_30()
        self.client.start_record()
        self.recording_active = True

        start_perf, start_wall, status = self._wait_for_recording_active()
        resolved_path = self._resolve_output_path(status, filename_hint)
        filename = Path(resolved_path).name
        full_path = str(resolved_path)

        # Start input capture with legacy logic
        legacy.start_recording()
        legacy.save_log(full_path)  # initialize log file bound to this video path
        legacy.start_input_threads(start_perf=start_perf, start_wall=start_wall)

        self.current_output_path = Path(full_path)
        self._start_log_thread()
        print(f"Started recording to {full_path}")
        return full_path, filename

    def stop_recording(self) -> Optional[Path]:
        if not self.client:
            return None
        try:
            status = self.client.get_record_status()
            if not status.output_active:
                print("Recording is not active")
            else:
                self.client.stop_record()
                # Update final path after stop
                status = self.client.get_record_status()
                self.current_output_path = self._resolve_output_path(status, None)
        finally:
            self._stop_log_thread()
            legacy.stop_input_threads()
            legacy.save_log()
            self.recording_active = False
            print("Stopped recording")
            return self.current_output_path

    def disconnect(self) -> None:
        if self.client:
            try:
                if self.recording_active:
                    self.stop_recording()
            finally:
                self.client.disconnect()
        self.client = None

    # Background log persistence -----------------------------------------
    def _start_log_thread(self) -> None:
        self._stop_event = threading.Event()

        def worker() -> None:
            while self._stop_event and not self._stop_event.wait(self.log_interval_seconds):
                legacy.save_log()

        self._log_thread = threading.Thread(target=worker, name="legacy_log_writer", daemon=True)
        self._log_thread.start()

    def _stop_log_thread(self) -> None:
        if self._stop_event:
            self._stop_event.set()
        if self._log_thread:
            self._log_thread.join(timeout=1.0)
        self._log_thread = None
        self._stop_event = None

    def _resolve_output_path(self, status: object, fallback_stem: Optional[str]) -> Path:
        candidates = [
            "output_path",
            "outputPath",
            "output_filename",
            "outputFilename",
        ]
        for field in candidates:
            if hasattr(status, field):
                val = getattr(status, field)
                if val:
                    return Path(val)
        if fallback_stem:
            return self.output_dir / f"{fallback_stem}.mkv"
        return self.output_dir / "recording.mkv"

    def _wait_for_recording_active(self) -> Tuple[float, float, object]:
        start = time.monotonic()
        last_status = self.client.get_record_status() if self.client else None
        while time.monotonic() - start < 3.0:
            status = self.client.get_record_status() if self.client else None
            last_status = status
            if status and getattr(status, "output_active", False):
                return time.perf_counter(), time.time(), status
            time.sleep(0.02)
        return time.perf_counter(), time.time(), last_status

    def _ensure_cfr_30(self) -> None:
        if not self.client:
            return
        set_fn = getattr(self.client, "set_video_settings", None)
        get_fn = getattr(self.client, "get_video_settings", None)
        if not set_fn or not get_fn:
            return
        try:
            settings = get_fn()
            fps_num = getattr(settings, "fps_numerator", None) or getattr(settings, "fpsNumerator", None)
            fps_den = getattr(settings, "fps_denominator", None) or getattr(settings, "fpsDenominator", None)
            if fps_num == 30 and fps_den in (1, None):
                return
            try:
                set_fn(fps_numerator=30, fps_denominator=1)
            except TypeError:
                set_fn(fpsNumerator=30, fpsDenominator=1)
        except Exception:
            return
