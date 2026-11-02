#!/usr/bin/env python3
"""Serve the repository locally with byte-range support for audio seeking."""
from __future__ import annotations

import argparse
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".flac", ".m4a", ".aac", ".opus"}


class RangeRequestHandler(SimpleHTTPRequestHandler):
    def _is_audio_request(self) -> bool:
        path = Path(self.translate_path(self.path))
        return path.suffix.lower() in AUDIO_EXTENSIONS

    def end_headers(self) -> None:
        if self._is_audio_request():
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def do_GET(self) -> None:
        if self._is_audio_request() and "Range" in self.headers:
            self._send_audio_range(include_body=True)
        else:
            super().do_GET()

    def do_HEAD(self) -> None:
        if self._is_audio_request() and "Range" in self.headers:
            self._send_audio_range(include_body=False)
        else:
            super().do_HEAD()

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
