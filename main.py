import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from obs_control import OBSRecorder

LOG_INTERVAL_SECONDS = 10


class GameMonitorUI:
    """UI shell that drives the legacy OBS + key/mouse recorder logic."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Game Monitor")
        self.root.geometry("600x420")
        self.root.minsize(560, 380)
        self.root.configure(bg="#eef2f7")

        style = ttk.Style()
        style.theme_use("clam")
        accent = "#2563eb"
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Card.TLabel", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#eef2f7", foreground="#0f172a", font=("Segoe UI Semibold", 16))
        style.configure("SubTitle.TLabel", background="#eef2f7", foreground="#475569", font=("Segoe UI", 10))
        style.configure("Status.TLabel", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI Semibold", 10), padding=8)
        style.configure("Accent.TButton", background=accent, foreground="#ffffff", relief="flat")
        style.map("Accent.TButton", background=[["active", "#1d4ed8"]], foreground=[["active", "#ffffff"]])
        style.configure("Danger.TButton", background="#ef4444", foreground="#ffffff", relief="flat")
        style.map("Danger.TButton", background=[["active", "#dc2626"]], foreground=[["active", "#ffffff"]])

        self.host_var = tk.StringVar(value="localhost")
        self.port_var = tk.IntVar(value=4455)
        self.password_var = tk.StringVar(value="")
        self.scene_var = tk.StringVar(value="screen")
        self.output_dir_var = tk.StringVar(value=str(Path("recordings").resolve()))

        self.recorder: OBSRecorder | None = None
        self.recording_active = False

        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Frame(self.root, style="Card.TFrame", padding=14)
        header.pack(fill="x", padx=14, pady=(12, 8))
        ttk.Label(header, text="Game Monitor", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text=f"OBS + keyboard/mouse capture · autosave every {LOG_INTERVAL_SECONDS}s",
            style="SubTitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        frame = ttk.Frame(self.root, style="Card.TFrame", padding=14)
        frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        grid = [
            ("Host", self.host_var),
            ("Port", self.port_var),
            ("Password", self.password_var, {"show": "*"}),
            ("Scene", self.scene_var),
            ("Output dir", self.output_dir_var),
        ]
        for idx, (label, var, *opt) in enumerate(grid):
            ttk.Label(frame, text=label, style="Card.TLabel").grid(row=idx, column=0, sticky="w", pady=4)
            entry = ttk.Entry(frame, textvariable=var, width=34, **(opt[0] if opt else {}))
            entry.grid(row=idx, column=1, sticky="we", pady=4)
            if label == "Output dir":
                ttk.Button(frame, text="Browse", command=self._choose_dir).grid(row=idx, column=2, padx=6)

        btn_row = ttk.Frame(frame, style="Card.TFrame")
        btn_row.grid(row=len(grid), column=0, columnspan=3, pady=(14, 6), sticky="w")
        self.start_btn = ttk.Button(btn_row, text="Start Recording", command=self._start, style="Accent.TButton")
        self.stop_btn = ttk.Button(btn_row, text="Stop Recording", command=self._stop, state="disabled", style="Danger.TButton")
        self.start_btn.pack(side="left", padx=(0, 8))
        self.stop_btn.pack(side="left")

        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(frame, textvariable=self.status_var, style="Status.TLabel").grid(
            row=len(grid) + 1, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        frame.columnconfigure(1, weight=1)

    def _choose_dir(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.output_dir_var.get() or ".")
        if chosen:
            self.output_dir_var.set(chosen)

    def _start(self) -> None:
        if self.recording_active:
            return
        self.start_btn.state(["disabled"])
        self.stop_btn.state(["!disabled"])
        self.status_var.set("Starting...")
        threading.Thread(target=self._start_worker, daemon=True).start()

    def _start_worker(self) -> None:
        try:
            self.recorder = OBSRecorder(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                password=self.password_var.get(),
                scene=self.scene_var.get(),
                output_dir=self.output_dir_var.get(),
                log_interval_seconds=LOG_INTERVAL_SECONDS,
            )
            self.recorder.connect()
            full_path, _ = self.recorder.start_recording()
            if not full_path:
                raise RuntimeError("OBS is already recording.")
            self.recording_active = True
            self._set_status(f"Recording -> {full_path} | Log every {LOG_INTERVAL_SECONDS}s")
        except Exception as exc:
            self._set_status(f"Failed to start: {exc}")
            self.root.after(0, lambda: self.start_btn.state(["!disabled"]))
            self.root.after(0, lambda: self.stop_btn.state(["disabled"]))

    def _stop(self) -> None:
        if not self.recording_active:
            return
        self.start_btn.state(["disabled"])
        self.stop_btn.state(["disabled"])
        self.status_var.set("Stopping...")
        threading.Thread(target=self._stop_worker, daemon=True).start()

    def _stop_worker(self) -> None:
        final_path = None
        try:
            if self.recorder:
                final_path = self.recorder.stop_recording()
                self.recorder.disconnect()
        finally:
            self.recording_active = False
            if final_path:
                self._set_status(f"Stopped. Saved: {final_path}")
            else:
                self._set_status("Stopped.")
            self.root.after(0, lambda: self.start_btn.state(["!disabled"]))
            self.root.after(0, lambda: self.stop_btn.state(["disabled"]))

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status_var.set(text))


def main() -> None:
    root = tk.Tk()
    GameMonitorUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
