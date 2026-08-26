from __future__ import annotations

import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk


class ListenerWindow:
    def __init__(self, root: tk.Tk, listener_args: list[str]) -> None:
        self.root = root
        self.listener_args = listener_args
        self.project_root = Path(__file__).resolve().parents[2]
        self.events: queue.Queue[str] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None
        self.closed = False
        self.raw_text = tk.StringVar(value="Waiting for audio...")
        self.corrected_text = tk.StringVar(value="-")
        self.intent = tk.StringVar(value="-")
        self.builder = tk.StringVar(value="Waiting for a Bible reference")
        self.candidate = tk.StringVar(value="-")
        self.connection = tk.StringVar(value="Stopped")
        self.current_reference = tk.StringVar(value="Waiting for a reference")
        self.confidence = tk.StringVar(value="--")
        self.event_count = tk.IntVar(value=0)
        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._drain_events)
        self._start_listener()

    def _build_layout(self) -> None:
        self.root.title("VersePilot - Live Reference Monitor")
        self.root.geometry("1080x760")
        self.root.minsize(820, 600)
        self.root.configure(background="#0D141B")

        colors = {
            "bg": "#0D141B", "panel": "#151F28", "panel_alt": "#1B2833",
            "line": "#2A3A47", "text": "#E7EEF2", "muted": "#91A4AF",
            "teal": "#4DD4C6", "amber": "#F2B96B", "red": "#F07F7F",
        }
        self.colors = colors

        outer = tk.Frame(self.root, bg=colors["bg"])
        outer.pack(fill=tk.BOTH, expand=True, padx=28, pady=24)

        header = tk.Frame(outer, bg=colors["bg"])
        header.pack(fill=tk.X, pady=(0, 22))
        tk.Label(header, text="VERSEPILOT", bg=colors["bg"], fg=colors["teal"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(header, text="Live reference monitor", bg=colors["bg"], fg=colors["text"],
                 font=("Segoe UI", 24, "bold")).pack(anchor="w", pady=(3, 0))
        status = tk.Frame(header, bg=colors["bg"])
        status.pack(anchor="e", side=tk.RIGHT, pady=(8, 0))
        self.status_dot = tk.Label(status, text="●", bg=colors["bg"], fg=colors["amber"],
                                   font=("Segoe UI", 14))
        self.status_dot.pack(side=tk.LEFT, padx=(0, 7))
        tk.Label(status, textvariable=self.connection, bg=colors["bg"], fg=colors["muted"],
                 font=("Segoe UI", 10)).pack(side=tk.LEFT)

        hero = tk.Frame(outer, bg=colors["panel"], highlightbackground=colors["line"], highlightthickness=1)
        hero.pack(fill=tk.X, pady=(0, 18))
        hero_left = tk.Frame(hero, bg=colors["panel"])
        hero_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=22, pady=18)
        tk.Label(hero_left, text="CURRENT REFERENCE", bg=colors["panel"], fg=colors["muted"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(hero_left, textvariable=self.current_reference, bg=colors["panel"], fg=colors["text"],
                 font=("Segoe UI", 25, "bold"), anchor="w").pack(anchor="w", pady=(5, 0))
        tk.Label(hero_left, text="The pipeline will only send a reference after it is resolved.",
                 bg=colors["panel"], fg=colors["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))
        metric = tk.Frame(hero, bg=colors["panel_alt"], width=170)
        metric.pack(side=tk.RIGHT, fill=tk.Y)
        metric.pack_propagate(False)
        tk.Label(metric, text="CONFIDENCE", bg=colors["panel_alt"], fg=colors["muted"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(20, 4))
        tk.Label(metric, textvariable=self.confidence, bg=colors["panel_alt"], fg=colors["teal"],
                 font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=18)

        content = tk.Frame(outer, bg=colors["bg"])
        content.pack(fill=tk.BOTH, expand=True)
        stages = tk.Frame(content, bg=colors["panel"], highlightbackground=colors["line"], highlightthickness=1)
        stages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        tk.Label(stages, text="PROCESSING PIPELINE", bg=colors["panel"], fg=colors["muted"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        self._stage(stages, "01", "Heard from stream", self.raw_text)
        self._stage(stages, "02", "Corrected", self.corrected_text)
        self._stage(stages, "03", "Intent", self.intent)
        self._stage(stages, "04", "Reference builder", self.builder)
        self._stage(stages, "05", "Candidate decision", self.candidate)

        log_frame = tk.Frame(content, bg=colors["panel"], highlightbackground=colors["line"], highlightthickness=1, width=430)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        log_frame.pack_propagate(False)
        log_header = tk.Frame(log_frame, bg=colors["panel"])
        log_header.pack(fill=tk.X, padx=16, pady=(16, 8))
        tk.Label(log_header, text="DIAGNOSTICS", bg=colors["panel"], fg=colors["muted"],
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        tk.Label(log_header, textvariable=self.event_count, bg=colors["panel"], fg=colors["teal"],
                 font=("Segoe UI", 9, "bold")).pack(side=tk.RIGHT)
        self.log = tk.Text(log_frame, height=16, wrap=tk.WORD, state=tk.DISABLED,
                           relief=tk.FLAT, borderwidth=0, padx=12, pady=8,
                           font=("Consolas", 9), background="#101820", foreground="#D7E3EA",
                           insertbackground=colors["text"])
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10), padx=(0, 10))

        footer = tk.Frame(outer, bg=colors["bg"])
        footer.pack(fill=tk.X, pady=(16, 0))
        tk.Label(footer, text="Local Faster-Whisper  •  One listener  •  FreeShow output", bg=colors["bg"],
                 fg=colors["muted"], font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Button(footer, text="Stop listener", command=self.stop_listener, relief=tk.FLAT,
                  bg=colors["red"], fg="#201215", activebackground="#FF9A9A", activeforeground="#201215",
                  font=("Segoe UI", 9, "bold"), padx=14, pady=7, cursor="hand2").pack(side=tk.RIGHT)

    def _stage(self, parent: tk.Frame, number: str, title: str, value: tk.StringVar) -> None:
        row = tk.Frame(parent, bg=self.colors["panel"])
        row.pack(fill=tk.X, padx=16, pady=5)
        tk.Label(row, text=number, width=4, bg=self.colors["panel_alt"], fg=self.colors["teal"],
                 font=("Consolas", 9, "bold"), pady=8).pack(side=tk.LEFT, anchor="n")
        detail = tk.Frame(row, bg=self.colors["panel"])
        detail.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 0))
        tk.Label(detail, text=title, bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(detail, textvariable=value, bg=self.colors["panel"], fg=self.colors["text"],
                 font=("Segoe UI", 10), wraplength=480, justify=tk.LEFT, anchor="w").pack(anchor="w", pady=(2, 5))

    def _start_listener(self) -> None:
        command = [sys.executable, str(self.project_root / "main.py"), *self.listener_args]
        try:
            self.process = subprocess.Popen(
                command,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            self.connection.set(f"Could not start listener: {exc}")
            return
        self.connection.set("Listening locally")
        threading.Thread(target=self._read_output, daemon=True).start()

    def _read_output(self) -> None:
        if self.process is None or self.process.stdout is None:
            return
        for line in self.process.stdout:
            self.events.put(line.rstrip())
        self.events.put(f"Listener exited with code {self.process.poll()}")

    def _drain_events(self) -> None:
        while True:
            try:
                line = self.events.get_nowait()
            except queue.Empty:
                break
            self._apply_line(line)
        if not self.closed:
            self.root.after(100, self._drain_events)

    def _apply_line(self, line: str) -> None:
        self.event_count.set(self.event_count.get() + 1)
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

        match = re.search(r"Heard raw: (.*)", line)
        if match:
            self.raw_text.set(match.group(1))
        elif "Processing audio with duration" in line:
            self.raw_text.set("Audio captured - transcribing locally...")
            self.connection.set("Transcribing locally")
            self.status_dot.configure(fg=self.colors["teal"])
        match = re.search(r"Heard corrected: (.*)", line)
        if match:
            self.corrected_text.set(match.group(1))
        match = re.search(r"Intent = (\w+) \| Confidence = ([\d.]+)", line)
        if match:
            self.intent.set(f"{match.group(1)} (confidence {match.group(2)})")
        match = re.search(
            r"State: (\w+) \| Book: (.*?) \| Chapter: (.*?) \| Verse: (.*?) \| Range: (.*?) \| Confidence: ([\d.]+)",
            line,
        )
        if match:
            state, book, chapter, verse, end_verse, confidence = match.groups()
            self.builder.set(
                f"{state} | {book} {chapter}:{verse}-{end_verse} | confidence {confidence}"
            )
            self.confidence.set(confidence)
            if book not in {"None", "-"} and chapter not in {"None", "-"}:
                reference = f"{book} {chapter}"
                if verse not in {"None", "-"}:
                    reference += f":{verse}"
                    if end_verse not in {"None", "-"}:
                        reference += f"-{end_verse}"
                self.current_reference.set(reference)
        match = re.search(r"CandidateEngine cycle .*", line)
        if match:
            self.candidate.set(match.group(0))
        match = re.search(r"(CANDIDATE ENGINE EMIT|TEXT MATCH|Sending chapter-only ref|Navigation):?\s*(.*)", line)
        if match:
            self.candidate.set(f"{match.group(1)} {match.group(2)}".strip())
            emitted = match.group(2).strip()
            if emitted:
                self.current_reference.set(emitted)
        if "Error" in line or "error" in line or "WARNING" in line:
            self.connection.set("Running - inspect diagnostic log")
            self.status_dot.configure(fg=self.colors["amber"])
        elif "Listening on microphone" in line or "Local Whisper model ready" in line:
            self.connection.set("Listening locally")
            self.status_dot.configure(fg=self.colors["teal"])

    def stop_listener(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.connection.set("Stopping...")

    def close(self) -> None:
        self.closed = True
        self.stop_listener()
        self.root.destroy()


def run_gui(listener_args: list[str]) -> int:
    root = tk.Tk()
    ListenerWindow(root, listener_args)
    root.mainloop()
    return 0
