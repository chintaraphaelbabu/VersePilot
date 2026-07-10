from __future__ import annotations

import logging
import queue
import threading
import time
import requests

from book_ids import BOOK_IDS
from config import AppConfig
from parser import BibleReference


def _reference_to_freeshow(reference: BibleReference) -> str:
    book_id = BOOK_IDS.get(reference.book)
    if book_id is None:
        raise ValueError(f"Unknown Bible book: {reference.book}")
    
    ref_str = f"{book_id}.{reference.chapter}"
    if reference.verse is not None:
        ref_str += f".{reference.verse}"
    return ref_str


class FreeShowClient:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = logging.getLogger("verses.freeshow")
        self.url = f"http://{config.freeshow_host}:{config.freeshow_port}"
        self.queue: queue.Queue[tuple[BibleReference, float, float, float, float, float]] = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def send_reference(
        self,
        reference: BibleReference,
        start_time: float,
        end_time: float,
        whisper_start: float,
        whisper_end: float,
        parser_end: float
    ) -> None:
        self.queue.put((reference, start_time, end_time, whisper_start, whisper_end, parser_end))

    def _worker(self) -> None:
        while True:
            try:
                reference, start_time, end_time, whisper_start, whisper_end, parser_end = self.queue.get()
                self._send_now(reference, start_time, end_time, whisper_start, whisper_end, parser_end)
                self.queue.task_done()
            except Exception as exc:
                self.logger.error("Error in FreeShow worker thread: %s", exc)

    def _send_now(
        self,
        reference: BibleReference,
        start_time: float,
        end_time: float,
        whisper_start: float,
        whisper_end: float,
        parser_end: float
    ) -> None:
        http_start = time.time()
        try:
            payload = {
                "action": "start_scripture",
                "reference": _reference_to_freeshow(reference)
            }
        except ValueError as exc:
            self.logger.error("Error formatting reference: %s", exc)
            return

        try:
            response = requests.post(self.url, json=payload, timeout=5)
            http_end = time.time()
            if response.status_code in (200, 204):
                print("✓ Sent")
                self.logger.info("Sent: %s", payload["reference"])
            else:
                print("HTTP error")
                print(f"Status Code: {response.status_code}")
                print(f"Response Body:\n{response.text}")
                self.logger.warning("HTTP error. Status code: %s", response.status_code)
        except requests.exceptions.ConnectionError:
            http_end = time.time()
            print("FreeShow is not running.")
            self.logger.warning("FreeShow is not running (connection refused).")
        except requests.exceptions.Timeout:
            http_end = time.time()
            print("HTTP error")
            print("Request timed out.")
            self.logger.warning("Request timed out.")
        except Exception as exc:
            http_end = time.time()
            print("HTTP error")
            print(f"Error: {exc}")
            self.logger.warning("Failed to send reference: %s", exc)

        speech_duration = end_time - start_time
        whisper_latency = whisper_end - whisper_start
        parser_latency = parser_end - whisper_end
        http_latency = http_end - http_start
        total_latency = http_end - end_time

        print(f"Speech duration: {speech_duration:.2f} s")
        print(f"Whisper: {whisper_latency:.2f} s")
        print(f"Parser: {parser_latency * 1000:.0f} ms")
        print(f"HTTP: {http_latency * 1000:.0f} ms")
        print(f"Total: {total_latency:.2f} s")
        print(f"Total latency: {total_latency:.2f} s")
        print(f"Whisper latency: {whisper_latency:.2f} s")