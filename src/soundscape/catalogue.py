"""Manifest validation and generated catalogue reports."""
import hashlib
import json
import math
import re
import wave
import shutil
import subprocess
from pathlib import Path


class CollectionError(ValueError):
    """The collection manifest or referenced media is invalid."""


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectionError(f"Cannot read manifest: {exc}") from exc
    if data.get("schema_version") != 1 or not isinstance(data.get("assets"), list):
        raise CollectionError("Expected schema_version 1 and an assets array")
    return data


def _asset_path(root: Path, value: str) -> Path:
    candidate = (root / value).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise CollectionError(f"Asset path escapes collection: {value}")
    return candidate


def import_media(source: Path, manifest_path: Path, destination: str, dry_run: bool = False) -> Path:
    """Copy one local recording beneath the collection root without overwriting."""
    root = manifest_path.resolve().parent
    source = source.resolve(strict=True)
    if not source.is_file():
        raise CollectionError(f"Source is not a file: {source}")
    target = _asset_path(root, destination)
    if target.exists():
        raise CollectionError(f"Refusing to overwrite existing file: {target}")
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return target


def inspect_media(path: Path) -> dict:
    """Return basic file/hash and, when available, ffprobe media properties."""
    path = path.resolve(strict=True)
    if not path.is_file():
        raise CollectionError(f"Not a file: {path}")
    result = {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        probe = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration,format_name", "-show_entries", "stream=codec_name,codec_type,sample_rate,channels,width,height", "-of", "json", str(path)],
            check=False, capture_output=True, text=True,
        )
        if probe.returncode == 0:
            result["ffprobe"] = json.loads(probe.stdout)
    elif path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as wav:
            result["audio"] = {"duration_seconds": wav.getnframes() / wav.getframerate(), "sample_rate_hz": wav.getframerate(), "channels": wav.getnchannels(), "sample_width_bytes": wav.getsampwidth()}
    return result


def validate(manifest_path: Path) -> list[str]:
    root = manifest_path.resolve().parent
    data = load_manifest(manifest_path)
    errors: list[str] = []
    seen: set[str] = set()
    for i, asset in enumerate(data["assets"]):
        prefix = f"assets[{i}]"
        for key in ("id", "title", "category", "file", "source_url", "source_sha256", "creator", "license", "license_url", "license_verified_on", "attribution", "commercial_use", "authenticity", "authenticity_confidence", "quality_notes", "playback", "event_guidance", "processing", "review"):
            if key not in asset or asset[key] is None or asset[key] == "":
                errors.append(f"{prefix}: missing {key}")
        asset_id = asset.get("id")
        if asset_id in seen:
            errors.append(f"{prefix}: duplicate id {asset_id}")
        seen.add(asset_id)
        try:
            media = _asset_path(root, asset["file"])
            if not media.is_file():
                errors.append(f"{prefix}: file not found: {asset['file']}")
                continue
            digest = hashlib.sha256(media.read_bytes()).hexdigest()
            if asset.get("sha256") != digest:
                errors.append(f"{prefix}: sha256 mismatch")
            if not re.fullmatch(r"[0-9a-f]{64}", asset.get("source_sha256", "")):
                errors.append(f"{prefix}: source_sha256 must be a 64-character lowercase SHA-256")
            if not re.fullmatch(r"[0-9a-f]{64}", asset.get("sha256", "")):
                errors.append(f"{prefix}: sha256 must be a 64-character lowercase SHA-256")
            if asset.get("processing") == [] and asset.get("source_sha256") != digest:
                errors.append(f"{prefix}: unprocessed source_sha256 must match file sha256")
            if media.suffix.lower() == ".wav":
                with wave.open(str(media), "rb") as wav:
                    frames, rate, channels, width = wav.getnframes(), wav.getframerate(), wav.getnchannels(), wav.getsampwidth()
                    if not frames or not rate or not channels or width not in (1, 2, 3, 4):
                        errors.append(f"{prefix}: invalid WAV signal or format")
                    if asset.get("sample_rate_hz") and asset["sample_rate_hz"] != rate:
                        errors.append(f"{prefix}: sample rate does not match manifest")
                    if asset.get("channels") and asset["channels"] != channels:
                        errors.append(f"{prefix}: channel count does not match manifest")
                    if asset.get("duration_seconds") and not math.isclose(asset["duration_seconds"], frames / rate, abs_tol=0.01):
                        errors.append(f"{prefix}: duration does not match manifest")
        except (KeyError, OSError, wave.Error, CollectionError) as exc:
            errors.append(f"{prefix}: {exc}")
        if asset.get("commercial_use") not in ("allowed", "not_allowed", "unknown"):
            errors.append(f"{prefix}: commercial_use must be allowed, not_allowed, or unknown")
        if asset.get("review", {}).get("status") == "release_ready":
            review = asset.get("review", {})
            if not review.get("listener") or not review.get("reviewed_on") or not review.get("outcome"):
                errors.append(f"{prefix}: release_ready requires a named listener, review date, and outcome")
            if review.get("loop_boundary_review") not in ("reviewed", "not_applicable"):
                errors.append(f"{prefix}: release_ready requires loop-boundary review or not_applicable")
            if asset.get("commercial_use") == "unknown" or not asset.get("license_verified_on"):
                errors.append(f"{prefix}: release_ready requires verified item-level rights")
            if not asset.get("source_sha256") or not asset.get("authenticity_confidence") or not asset.get("quality_notes"):
                errors.append(f"{prefix}: release_ready requires source hash, authenticity confidence, and quality notes")
        if not isinstance(asset.get("share_alike"), bool):
            errors.append(f"{prefix}: share_alike must explicitly be true or false")
        if not isinstance(asset.get("processing"), list):
            errors.append(f"{prefix}: processing must be an array")
    return errors


def render_catalogue(manifest_path: Path) -> str:
    data = load_manifest(manifest_path)
    rows = ["# Audio catalogue", "", "Generated from `manifest.json`. Unknown rights or unauditioned recordings are not release-ready. Share-alike obligations and authenticity are shown per item.", "", "| ID | Recording | Category | Licence | Commercial use | Share-alike | Authenticity | Review |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for asset in data["assets"]:
        rows.append("| {id} | [{title}]({file}) | {category} | {license} | {commercial_use} | {share_alike} | {authenticity} | {review} |".format(
            id=asset.get("id", ""), title=asset.get("title", ""), file=asset.get("file", ""), category=asset.get("category", ""),
            license=asset.get("license", "unknown"), commercial_use=asset.get("commercial_use", "unknown"), share_alike=asset.get("share_alike", "unknown"), authenticity=asset.get("authenticity", "unknown"), review=asset.get("review", {}).get("status", "not reviewed")))
    return "\n".join(rows) + "\n"
