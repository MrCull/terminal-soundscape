#!/usr/bin/env python3
"""Generate local YAMNet sound-event tags without uploading source audio."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from collections import Counter
from pathlib import Path

MODEL_ID = "thelou1s/yamnet"
MODEL_REVISION = "156527da8fb34f53a3798d6011810fa975738062"
MODEL_NAME = "lite-model_yamnet_tflite_1.tflite"
LABELS_NAME = "labels_yamnet.txt"
MODEL_SHA256 = "141fba1cdaae842c816f28edc4937e8b4f0af4c8df21862ccc6b52dc567993c3"
LABELS_SHA256 = "7d8f037d4f496d26fa910a0381b3d47042adcb89b7706e976785b6d3943ccd59"
CHUNK_SECONDS = 5
SAMPLE_RATE = 16000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_checked(path: Path, name: str, expected: str) -> None:
    if path.exists():
        if sha256(path) != expected:
            raise RuntimeError(f"Checksum mismatch for cached model file: {path}")
        return
    url = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{name}?download=true"
    temporary = path.with_suffix(path.suffix + ".download")
    try:
        urllib.request.urlretrieve(url, temporary)
        if sha256(temporary) != expected:
            raise RuntimeError(f"Checksum mismatch for downloaded model file: {name}")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_model(model_dir: Path) -> tuple[Path, Path]:
    model_dir.mkdir(parents=True, exist_ok=True)
    model = model_dir / MODEL_NAME
    labels = model_dir / LABELS_NAME
    download_checked(model, MODEL_NAME, MODEL_SHA256)
    download_checked(labels, LABELS_NAME, LABELS_SHA256)
    return model, labels


def read_manifests(root: Path) -> list[dict]:
    current = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    first = json.loads((root / "first-collection/manifest.json").read_text(encoding="utf-8-sig"))
    records = []
    for asset in current["assets"]:
        records.append({
            "collection": "current",
            "id": asset["id"],
            "file": asset["file"],
            "description": asset.get("title", asset["id"]),
            "expected_sha256": asset.get("sha256"),
        })
    for asset in first["assets"]:
        records.append({
            "collection": "first-collection",
            "id": asset["id"],
            "file": "first-collection/" + asset["path"],
            "description": asset.get("description", asset["id"]),
            "expected_sha256": asset.get("sha256"),
        })
    return records


def decode_chunks(path: Path):
    command = [
        "ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
        "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE),
        "-f", "f32le", "pipe:1",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    chunk_bytes = CHUNK_SECONDS * SAMPLE_RATE * 4
    index = 0
    try:
        while block := process.stdout.read(chunk_bytes):
            if len(block) % 4:
                raise RuntimeError(f"FFmpeg returned an incomplete float sample for {path}")
            yield index * CHUNK_SECONDS, block
            index += 1
    finally:
        process.stdout.close()
    error = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    return_code = process.wait()
    if return_code:
        raise RuntimeError(f"FFmpeg decode failed for {path}: {error.strip()}")


def label_map(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [data[str(i)] for i in range(len(data))]


def classify(path: Path, interpreter, labels: list[str]) -> dict:
    import numpy as np

    inputs = interpreter.get_input_details()
    outputs = interpreter.get_output_details()
    input_index = inputs[0]["index"]
    scores_index = outputs[0]["index"]
    sum_scores = np.zeros(len(labels), dtype=np.float64)
    max_scores = np.zeros(len(labels), dtype=np.float32)
    frame_count = 0
    segments = []
    audio_seconds = 0.0
    for start, raw in decode_chunks(path):
        samples = np.frombuffer(raw, dtype="<f4")
        if not samples.size:
            continue
        interpreter.resize_tensor_input(input_index, samples.shape, strict=True)
        interpreter.allocate_tensors()
        interpreter.set_tensor(input_index, samples)
        interpreter.invoke()
        frame_scores = interpreter.get_tensor(scores_index)
        if frame_scores.ndim == 1:
            frame_scores = frame_scores[None, :]
        chunk_scores = frame_scores.mean(axis=0)
        sum_scores += frame_scores.sum(axis=0)
        max_scores = np.maximum(max_scores, frame_scores.max(axis=0))
        frame_count += frame_scores.shape[0]
        duration = len(samples) / SAMPLE_RATE
        audio_seconds += duration
        top_index = int(np.argmax(chunk_scores))
        segments.append({
            "start_seconds": round(start, 2),
            "end_seconds": round(start + duration, 2),
            "label": labels[top_index],
            "score": round(float(chunk_scores[top_index]), 4),
        })
    if not frame_count:
        raise RuntimeError(f"No audio samples decoded for {path}")
    mean_scores = sum_scores / frame_count
    top_indices = np.argsort(mean_scores)[::-1][:8]
    peak_indices = np.argsort(max_scores)[::-1][:8]
    highlights = sorted(segments, key=lambda item: item["score"], reverse=True)[:10]
    return {
        "audio_duration_seconds": round(audio_seconds, 3),
        "analysis_coverage": "full file, in five-second windows",
        "top_tags_by_mean_score": [
            {"label": labels[int(i)], "score": round(float(mean_scores[i]), 4)}
            for i in top_indices
        ],
        "top_tags_by_peak_score": [
            {"label": labels[int(i)], "score": round(float(max_scores[i]), 4)}
            for i in peak_indices
        ],
        "highest_scoring_windows": highlights,
    }


def render_markdown(report: dict) -> str:
    successful = [item for item in report["assets"] if "analysis" in item]
    lines = [
        "# Automated audio event tags", "",
        "These are local YAMNet AudioSet classifier predictions, not listening notes. Scores are model outputs, not calibrated probabilities. Generic or incorrect tags are possible; use the highlighted times for human follow-up.", "",
        f"Model: `{report['model']['id']}` at revision `{report['model']['revision']}` (Apache-2.0 TFLite model). Audio was decoded locally with FFmpeg to 16 kHz mono float samples; no audio files were uploaded or modified.", "",
        f"Processed {len(successful)} of {len(report['assets'])} masters. Most common top mean-score tags:", "",
    ]
    for collection, title in (("current", "Current collection"), ("first-collection", "First collection")):
        counts = Counter(
            item["analysis"]["top_tags_by_mean_score"][0]["label"]
            for item in successful
            if item["collection"] == collection and item["analysis"]["top_tags_by_mean_score"]
        )
        if counts:
            lines.append(f"- {title}: " + ", ".join(f"{label} ({count})" for label, count in counts.most_common(8)))
    lines.append("")
    for item in report["assets"]:
        tags = ", ".join(f"{tag['label']} ({tag['score']:.2f})" for tag in item.get("analysis", {}).get("top_tags_by_mean_score", [])[:5])
        peak_tags = ", ".join(f"{tag['label']} ({tag['score']:.2f})" for tag in item.get("analysis", {}).get("top_tags_by_peak_score", [])[:5])
        lines.extend([
            f"## `{item['file']}`", "",
            f"{item['description']}", "",
            f"- Mean tags: {tags or 'none'}",
            f"- Peak tags: {peak_tags or 'none'}",
            f"- Analysis: {item.get('analysis', {}).get('audio_duration_seconds', 'failed')} seconds; {item.get('analysis', {}).get('analysis_coverage', item.get('error', 'not analyzed'))}.",
        ])
        windows = item.get("analysis", {}).get("highest_scoring_windows", [])
        if windows:
            formatted = "; ".join(f"{window['start_seconds']:.0f}–{window['end_seconds']:.0f}s {window['label']} ({window['score']:.2f})" for window in sorted(windows, key=lambda entry: entry['start_seconds']))
            lines.append(f"- High-scoring windows: {formatted}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--model-dir", type=Path, default=Path.home() / ".cache/terminal-soundscape/yamnet")
    parser.add_argument("--output-json", type=Path, default=Path("docs/generated/audio-event-tags.json"))
    parser.add_argument("--output-md", type=Path, default=Path("docs/audio-event-tags.md"))
    parser.add_argument("--threads", type=int, default=max(1, min(os.cpu_count() or 1, 4)))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be at least 1")
    root = args.root.resolve()
    out_json = args.output_json if args.output_json.is_absolute() else root / args.output_json
    out_md = args.output_md if args.output_md.is_absolute() else root / args.output_md
    if not args.overwrite and (out_json.exists() or out_md.exists()):
        parser.error("report exists; use --overwrite to replace it")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.error("FFmpeg is required")
    try:
        import numpy  # noqa: F401
        try:
            from ai_edge_litert.interpreter import Interpreter
        except ImportError:
            from tflite_runtime.interpreter import Interpreter
    except ImportError as exc:
        parser.error(f"install optional dependencies with: python -m pip install -r tools/audio-tagging/requirements.txt ({exc})")
    model_path, labels_path = ensure_model(args.model_dir)
    labels = label_map(labels_path)
    interpreter = Interpreter(model_path=str(model_path), num_threads=args.threads)
    interpreter.allocate_tensors()
    results = []
    for i, item in enumerate(read_manifests(root), start=1):
        path = root / item["file"]
        print(f"[{i}/124] {item['file']}", file=sys.stderr, flush=True)
        entry = {
            **item,
            "source_sha256": item["expected_sha256"],
            "model_analysis_status": "not_auditioned_machine_tags_only",
        }
        entry.pop("expected_sha256", None)
        try:
            if not path.is_file():
                raise RuntimeError(f"missing file: {path}")
            if item["expected_sha256"] and sha256(path) != item["expected_sha256"]:
                raise RuntimeError("source SHA-256 does not match manifest")
            entry["analysis"] = classify(path, interpreter, labels)
        except Exception as exc:  # Preserve a per-file failure and continue the batch.
            entry["error"] = str(exc)
        results.append(entry)
    report = {
        "schema_version": 1,
        "purpose": "automated_sound_event_tags_for_triage",
        "warning": "Machine-generated AudioSet class scores are not listening reviews, acoustic captions, authenticity evidence, or release approval.",
        "audio_transfer": "none; source audio was processed locally",
        "model": {
            "id": MODEL_ID,
            "revision": MODEL_REVISION,
            "license": "Apache-2.0",
            "model_file": MODEL_NAME,
            "model_sha256": MODEL_SHA256,
            "labels_file": LABELS_NAME,
            "labels_sha256": LABELS_SHA256,
            "runtime": "ai-edge-litert",
            "runtime_version": "2.3.0",
            "ffmpeg_resample": "mono 16000 Hz float32",
            "window_seconds": CHUNK_SECONDS,
            "threads": args.threads,
        },
        "assets": results,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    failed = sum("error" in item for item in results)
    print(f"Analyzed {len(results)-failed}/{len(results)} recordings; {failed} failed. Reports: {out_json} and {out_md}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
