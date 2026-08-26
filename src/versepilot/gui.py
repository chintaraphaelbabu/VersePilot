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
        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._drain_events)
        self._start_listener()

    def _build_layout(self) -> None:
        self.root.title("VersePilot - Live Reference Monitor")
        self.root.geometry("900x650")
        self.root.minsize(700, 500)

        style = ttk.Style(self.root)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Stage.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Value.TLabel", font=("Segoe UI", 12))

        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="VersePilot Live Monitor", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, textvariable=self.connection).pack(anchor="w", pady=(3, 14))

        stages = ttk.LabelFrame(frame, text="Reference being built", padding=12)
        stages.pack(fill=tk.X)
        self._stage(stages, "1. Heard", self.raw_text)
        self._stage(stages, "2. Corrected", self.corrected_text)
        self._stage(stages, "3. Intent", self.intent)
        self._stage(stages, "4. Builder", self.builder)
        self._stage(stages, "5. Candidate", self.candidate)

        log_frame = ttk.LabelFrame(frame, text="Live diagnostic log", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        self.log = tk.Text(log_frame, height=16, wrap=tk.WORD, state=tk.DISABLED,
                           font=("Consolas", 9), background="#101820", foreground="#D7E3EA")
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(frame, text="Stop listener", command=self.stop_listener).pack(anchor="e", pady=(10, 0))

    def _stage(self, parent: ttk.LabelFrame, title: str, value: tk.StringVar) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text=title, width=16, style="Stage.TLabel").pack(side=tk.LEFT, anchor="n")
        ttk.Label(row, textvariable=value, style="Value.TLabel", wraplength=680).pack(
            side=tk.LEFT, fill=tk.X, expand=True, anchor="w"
        )

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
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

        match = re.search(r"Heard raw: (.*)", line)
        if match:
            self.raw_text.set(match.group(1))
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
        match = re.search(r"CandidateEngine cycle .*", line)
        if match:
            self.candidate.set(match.group(0))
        match = re.search(r"(CANDIDATE ENGINE EMIT|TEXT MATCH|Sending chapter-only ref|Navigation):?\s*(.*)", line)
        if match:
            self.candidate.set(f"{match.group(1)} {match.group(2)}".strip())
        if "Error" in line or "error" in line or "WARNING" in line:
            self.connection.set("Running - inspect diagnostic log")

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
