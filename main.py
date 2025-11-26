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
        self.root.geometry("480x620")
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 480) // 2
        y = (screen_height - 620) // 2
        self.root.geometry(f"480x620+{x}+{y}")
        
        self.root.configure(bg="#f8fafc")

        style = ttk.Style()
        style.theme_use("clam")
        
        # Modern Color Palette
        bg_color = "#f8fafc"      # Slate 50
        card_bg = "#ffffff"       # White
        text_main = "#0f172a"     # Slate 900
        text_muted = "#64748b"    # Slate 500
        primary = "#3b82f6"       # Blue 500
        primary_hover = "#2563eb" # Blue 600
        danger = "#ef4444"        # Red 500
        danger_hover = "#dc2626"  # Red 600

        # Styles
        style.configure("TFrame", background=bg_color)
        style.configure("Card.TFrame", background=card_bg)
        
        style.configure("TLabel", background=bg_color, foreground=text_main, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=card_bg, foreground=text_main, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=bg_color, foreground=text_main, font=("Segoe UI", 18, "bold"))
        style.configure("SubHeader.TLabel", background=bg_color, foreground=text_muted, font=("Segoe UI", 10))
        style.configure("Status.TLabel", background=card_bg, foreground=text_muted, font=("Segoe UI", 9))

        style.configure("TButton", font=("Segoe UI Semibold", 10), padding=6)
        
        style.configure("Accent.TButton", background=primary, foreground="white", borderwidth=0)
        style.map("Accent.TButton", background=[("active", primary_hover), ("disabled", "#94a3b8")])
        
        style.configure("Danger.TButton", background=danger, foreground="white", borderwidth=0)
        style.map("Danger.TButton", background=[("active", danger_hover), ("disabled", "#94a3b8")])

        style.configure("TLabelframe", background=card_bg, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=card_bg, foreground=text_main, font=("Segoe UI", 10, "bold"))

        self.host_var = tk.StringVar(value="localhost")
        self.port_var = tk.IntVar(value=4455)
        self.password_var = tk.StringVar(value="")
        self.scene_var = tk.StringVar(value="screen")
        self.output_dir_var = tk.StringVar(value=str(Path("recordings").resolve()))
        self.status_var = tk.StringVar(value="Ready")

        self.recorder: OBSRecorder | None = None
        self.recording_active = False

        self._build_ui()

    def _build_ui(self) -> None:
        # Main Layout
        main_frame = ttk.Frame(self.root, padding=24)
        main_frame.pack(fill="both", expand=True)

        # Header
        header = ttk.Frame(main_frame)
        header.pack(fill="x", pady=(0, 24))
        ttk.Label(header, text="Game Monitor", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text=f"OBS & Input Recorder · Auto-save {LOG_INTERVAL_SECONDS}s",
            style="SubHeader.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        # Content Card
        card = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)

        # OBS Connection Group
        obs_group = ttk.LabelFrame(card, text=" OBS Connection ", padding=16)
        obs_group.pack(fill="x", pady=(0, 16))
        
        self._add_field(obs_group, "Host", self.host_var, 0)
        self._add_field(obs_group, "Port", self.port_var, 1)
        self._add_field(obs_group, "Password", self.password_var, 2, show="*")
        obs_group.columnconfigure(1, weight=1)

        # Recording Settings Group
        rec_group = ttk.LabelFrame(card, text=" Recording Settings ", padding=16)
        rec_group.pack(fill="x", pady=(0, 24))
        
        self._add_field(rec_group, "Scene", self.scene_var, 0)
        
        # Output Dir Custom Field
        ttk.Label(rec_group, text="Output Dir", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        dir_frame = ttk.Frame(rec_group, style="Card.TFrame")
        dir_frame.grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Entry(dir_frame, textvariable=self.output_dir_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(dir_frame, text="Browse", command=self._choose_dir).pack(side="right")
        rec_group.columnconfigure(1, weight=1)

        # Buttons
        self.start_btn = ttk.Button(card, text="Start Recording", command=self._start, style="Accent.TButton", cursor="hand2")
        self.start_btn.pack(fill="x", pady=(0, 12), ipady=4)
        
        self.stop_btn = ttk.Button(card, text="Stop Recording", command=self._stop, state="disabled", style="Danger.TButton", cursor="hand2")
        self.stop_btn.pack(fill="x", ipady=4)

        # Status Bar
        status_bar = ttk.Frame(self.root, style="Card.TFrame", padding=(12, 8))
        status_bar.pack(fill="x", side="bottom")
        ttk.Label(status_bar, textvariable=self.status_var, style="Status.TLabel").pack(side="left")

    def _add_field(self, parent, label, var, row, **kwargs):
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        ttk.Entry(parent, textvariable=var, **kwargs).grid(row=row, column=1, sticky="ew", pady=6)

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
