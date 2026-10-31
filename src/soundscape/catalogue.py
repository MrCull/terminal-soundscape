"""Manifest validation and generated catalogue reports."""
import hashlib
import json
import math
import wave
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


def validate(manifest_path: Path) -> list[str]:
    root = manifest_path.resolve().parent
    data = load_manifest(manifest_path)
    errors: list[str] = []
    seen: set[str] = set()
    for i, asset in enumerate(data["assets"]):
        prefix = f"assets[{i}]"
        for key in ("id", "title", "category", "file", "source_url", "creator", "license", "attribution", "commercial_use", "authenticity", "playback", "review"):
            if not asset.get(key):
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
        if asset.get("review", {}).get("status") == "release_ready" and not asset.get("review", {}).get("listener"):
            errors.append(f"{prefix}: release_ready requires a named listener")
    return errors


def render_catalogue(manifest_path: Path) -> str:
    data = load_manifest(manifest_path)
    rows = ["# Audio catalogue", "", "Generated from `manifest.json`. Unknown rights or unauditioned recordings are not release-ready.", "", "| ID | Recording | Category | Licence | Commercial use | Review |", "| --- | --- | --- | --- | --- | --- |"]
    for asset in data["assets"]:
        rows.append("| {id} | [{title}]({file}) | {category} | {license} | {commercial_use} | {review} |".format(
            id=asset.get("id", ""), title=asset.get("title", ""), file=asset.get("file", ""), category=asset.get("category", ""),
            license=asset.get("license", "unknown"), commercial_use=asset.get("commercial_use", "unknown"), review=asset.get("review", {}).get("status", "not reviewed")))
    return "\n".join(rows) + "\n"
