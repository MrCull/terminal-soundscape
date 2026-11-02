#!/usr/bin/env python3
"""Serve the repository locally with byte-range support for audio seeking."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".flac", ".m4a", ".aac", ".opus"}
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REVIEWS_PATH = REPOSITORY_ROOT / "docs/listening-reviews.json"
REVIEWS_LOCK = threading.Lock()


class RangeRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if urlsplit(self.path).path == "/api/reviews":
            with REVIEWS_LOCK:
                if REVIEWS_PATH.exists():
                    content = REVIEWS_PATH.read_bytes()
                else:
                    content = b'{"schema_version":1,"reviews":[]}\n'
            self._send_json(200, content)
            return
        if self._is_audio_request() and "Range" in self.headers:
            self._send_audio_range(include_body=True)
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/reviews":
            self.send_error(404, "Not found")
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 256_000:
                raise ValueError("Request must contain a review smaller than 256 KB")
            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, dict):
                raise ValueError("Request body must be an object")
            review = self._validate_review(payload.get("review"))
            with REVIEWS_LOCK:
                if REVIEWS_PATH.exists():
                    data = json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))
                else:
                    data = {"schema_version": 1, "reviews": []}
                if not isinstance(data, dict):
                    raise ValueError("The repository review file must contain a JSON object")
                reviews = data.get("reviews")
                if data.get("schema_version") != 1 or not isinstance(reviews, list):
                    raise ValueError("The repository review file has an unsupported format")
                key = (review["collection"], review["id"])
                review["saved_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
                for index, existing in enumerate(reviews):
                    if (existing.get("collection"), existing.get("id")) == key:
                        reviews[index] = review
                        break
                else:
                    reviews.append(review)
                self._write_reviews(data)
            self._send_json(200, json.dumps({"review": review}, ensure_ascii=False).encode("utf-8"))
        except (ValueError, TypeError, KeyError, json.JSONDecodeError, OSError) as error:
            self._send_json(400, json.dumps({"error": str(error)}).encode("utf-8"))

    def do_HEAD(self) -> None:
        if self._is_audio_request() and "Range" in self.headers:
            self._send_audio_range(include_body=False)
        else:
            super().do_HEAD()

    def _validate_review(self, value: object) -> dict:
        if not isinstance(value, dict):
            raise ValueError("Review must be an object")
        review_id = value.get("id")
        collection = value.get("collection")
        source_file = value.get("source_file")
        if not isinstance(review_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", review_id):
            raise ValueError("Invalid recording ID")
        if collection not in ("current", "first-collection"):
            raise ValueError("Invalid collection")
        if not isinstance(source_file, str):
            raise ValueError("Missing source file")
        source_path = Path(source_file)
        if source_path.is_absolute() or ".." in source_path.parts:
            raise ValueError("Source path must stay inside the repository")
        expected_prefix = "assets/candidates" if collection == "current" else "first-collection/audio"
        if not source_file.startswith(expected_prefix + "/") or not (REPOSITORY_ROOT / source_path).is_file():
            raise ValueError("Source file does not belong to the selected collection")
        rating = value.get("rating")
        if type(rating) is not int or rating < 1 or rating > 5:
            raise ValueError("Rating must be a whole number from 1 to 5")
        tags = value.get("tags", [])
        if not isinstance(tags, list) or len(tags) > 40 or any(not isinstance(tag, str) or len(tag) > 60 for tag in tags):
            raise ValueError("Tags must be a list of short text values")
        start = self._marker(value.get("start_seconds"), "start")
        end = self._marker(value.get("end_seconds"), "end")
        if start is not None and end is not None and end <= start:
            raise ValueError("End marker must come after start marker")
        notes = value.get("notes", "")
        reviewer = value.get("reviewer", "")
        if not isinstance(notes, str) or len(notes) > 4000:
            raise ValueError("Notes must be text under 4000 characters")
        if not isinstance(reviewer, str) or len(reviewer) > 200:
            raise ValueError("Reviewer name must be under 200 characters")
        return {
            "id": review_id,
            "collection": collection,
            "source_file": source_file,
            "rating": rating,
            "tags": tags,
            "start_seconds": start,
            "end_seconds": end,
            "notes": notes,
            "reviewer": reviewer,
        }

    @staticmethod
    def _marker(value: object, label: str) -> float | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{label.title()} marker must be a non-negative time")
        return round(float(value), 1)

    @staticmethod
    def _write_reviews(data: dict) -> None:
        REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=REVIEWS_PATH.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, REVIEWS_PATH)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _send_json(self, status: int, content: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _is_audio_request(self) -> bool:
        path = Path(self.translate_path(self.path))
        return path.suffix.lower() in AUDIO_EXTENSIONS

    def end_headers(self) -> None:
        if self._is_audio_request():
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def _send_audio_range(self, include_body: bool) -> None:
        path = Path(self.translate_path(self.path))
        try:
            file = path.open("rb")
        except OSError:
            self.send_error(404, "File not found")
            return
        with file:
            size = os.fstat(file.fileno()).st_size
            header = self.headers.get("Range", "")
            if not header.startswith("bytes=") or "," in header:
                self._range_not_satisfiable(size)
                return
            spec = header[6:].strip()
            try:
                left, right = spec.split("-", 1)
                if left:
                    start = int(left)
                    end = int(right) if right else size - 1
                else:
                    suffix_length = int(right)
                    if suffix_length <= 0:
                        raise ValueError
                    start = max(0, size - suffix_length)
                    end = size - 1
                if start < 0 or start >= size or end < start:
                    raise ValueError
                end = min(end, size - 1)
            except (ValueError, TypeError):
                self._range_not_satisfiable(size)
                return

            length = end - start + 1
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(str(path)))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Last-Modified", self.date_time_string(os.fstat(file.fileno()).st_mtime))
            self.end_headers()
            if include_body:
                file.seek(start)
                remaining = length
                while remaining:
                    block = file.read(min(64 * 1024, remaining))
                    if not block:
                        break
                    self.wfile.write(block)
                    remaining -= len(block)

    def _range_not_satisfiable(self, size: int) -> None:
        self.send_response(416)
        self.send_header("Content-Range", f"bytes */{size}")
        self.send_header("Content-Length", "0")
        self.end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: localhost only)")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    handler = lambda *handler_args, **handler_kwargs: RangeRequestHandler(
        *handler_args, directory=str(root), **handler_kwargs
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {root} at http://{args.host}:{args.port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
