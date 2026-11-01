"""Manifest validation and generated catalogue reports."""
import hashlib
import json
import math
import re
import struct
import wave
import shutil
import subprocess
from pathlib import Path


class CollectionError(ValueError):
    """The collection manifest or referenced media is invalid."""


def _decode_signal(path: Path) -> tuple[float, int] | None:
    """Decode audio to float samples and return peak magnitude and full-scale count."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    process = subprocess.Popen(
        [ffmpeg, "-v", "error", "-i", str(path), "-map", "0:a:0", "-f", "f32le", "-acodec", "pcm_f32le", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    peak = 0.0
    full_scale_samples = 0
    assert process.stdout is not None
    remainder = b""
    while chunk := process.stdout.read(1024 * 1024):
        data = remainder + chunk
        usable_length = len(data) - (len(data) % 4)
        for (sample,) in struct.iter_unpack("<f", data[:usable_length]):
            magnitude = abs(sample)
            peak = max(peak, magnitude)
            if magnitude >= 1.0:
                full_scale_samples += 1
        remainder = data[usable_length:]
    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    return_code = process.wait()
    if process.stdout:
        process.stdout.close()
    if process.stderr:
        process.stderr.close()
    if return_code != 0 or remainder or peak == 0.0:
        detail = stderr.strip() or "no decodable audio samples"
        raise CollectionError(f"FFmpeg could not decode audio: {detail}")
    return peak, full_scale_samples


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectionError(f"Cannot read manifest: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("assets"), list):
        raise CollectionError("Expected schema_version 1 and an assets array")
    return data


def _asset_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value:
        raise CollectionError("Asset file must be a non-empty relative path")
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
        signal_check = None
        if not isinstance(asset, dict):
            errors.append(f"{prefix}: expected an object")
            continue
        review = asset.get("review")
        if not isinstance(review, dict):
            errors.append(f"{prefix}: review must be an object")
            review = {}
        for key in ("id", "title", "category", "file", "source_url", "source_sha256", "source_downloaded_on", "creator", "license", "license_url", "license_verified_on", "attribution", "commercial_use", "authenticity", "authenticity_confidence", "codec", "bit_depth", "file_size_bytes", "quality_notes", "playback", "event_guidance", "processing", "derivatives", "review"):
            if key not in asset or asset[key] is None or asset[key] == "":
                errors.append(f"{prefix}: missing {key}")
        asset_id = asset.get("id")
        if isinstance(asset_id, str):
            if asset_id in seen:
                errors.append(f"{prefix}: duplicate id {asset_id}")
            seen.add(asset_id)
        else:
            errors.append(f"{prefix}: id must be a string")
        try:
            media = _asset_path(root, asset["file"])
            if not media.is_file():
                errors.append(f"{prefix}: file not found: {asset['file']}")
                continue
            if asset.get("file_size_bytes") != media.stat().st_size:
                errors.append(f"{prefix}: file size does not match manifest")
            digest = hashlib.sha256(media.read_bytes()).hexdigest()
            if asset.get("sha256") != digest:
                errors.append(f"{prefix}: sha256 mismatch")
            if not re.fullmatch(r"[0-9a-f]{64}", asset.get("source_sha256", "")):
                errors.append(f"{prefix}: source_sha256 must be a 64-character lowercase SHA-256")
            if not re.fullmatch(r"[0-9a-f]{64}", asset.get("sha256", "")):
                errors.append(f"{prefix}: sha256 must be a 64-character lowercase SHA-256")
            if asset.get("processing") == [] and asset.get("source_sha256") != digest:
                errors.append(f"{prefix}: unprocessed source_sha256 must match file sha256")
            try:
                peak, full_scale_samples = _decode_signal(media)
                if peak is not None:
                    signal_check = {"peak": peak, "full_scale_samples": full_scale_samples}
            except CollectionError as exc:
                errors.append(f"{prefix}: {exc}")
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
        if review.get("status") == "release_ready":
            if not review.get("listener") or not review.get("reviewed_on") or not review.get("outcome"):
                errors.append(f"{prefix}: release_ready requires a named listener, review date, and outcome")
            if review.get("loop_boundary_review") not in ("reviewed", "not_applicable"):
                errors.append(f"{prefix}: release_ready requires loop-boundary review or not_applicable")
            if asset.get("commercial_use") == "unknown" or not asset.get("license_verified_on"):
                errors.append(f"{prefix}: release_ready requires verified item-level rights")
            if not asset.get("source_sha256") or not asset.get("authenticity_confidence") or not asset.get("quality_notes"):
                errors.append(f"{prefix}: release_ready requires source hash, authenticity confidence, and quality notes")
            if not signal_check:
                errors.append(f"{prefix}: release_ready requires an FFmpeg decode and signal check")
            elif signal_check["full_scale_samples"]:
                errors.append(f"{prefix}: release_ready signal check found full-scale samples requiring clipping review")
        if not isinstance(asset.get("share_alike"), bool):
            errors.append(f"{prefix}: share_alike must explicitly be true or false")
        if not isinstance(asset.get("processing"), list):
            errors.append(f"{prefix}: processing must be an array")
        derivatives = asset.get("derivatives")
        if not isinstance(derivatives, list):
            errors.append(f"{prefix}: derivatives must be an array")
        else:
            for j, derivative in enumerate(derivatives):
                derivative_prefix = f"{prefix}.derivatives[{j}]"
                if not isinstance(derivative, dict) or not isinstance(derivative.get("file"), str) or not isinstance(derivative.get("sha256"), str):
                    errors.append(f"{derivative_prefix}: expected file and sha256 fields")
                    continue
                try:
                    derivative_path = _asset_path(root, derivative["file"])
                    if not derivative_path.is_file():
                        errors.append(f"{derivative_prefix}: file not found: {derivative['file']}")
                    elif hashlib.sha256(derivative_path.read_bytes()).hexdigest() != derivative["sha256"]:
                        errors.append(f"{derivative_prefix}: sha256 mismatch")
                except (OSError, CollectionError) as exc:
                    errors.append(f"{derivative_prefix}: {exc}")
    return errors


def render_catalogue(manifest_path: Path) -> str:
    data = load_manifest(manifest_path)
    rows = ["# Audio catalogue", "", "Generated from `manifest.json`. Unknown rights or unauditioned recordings are not release-ready. Share-alike obligations and authenticity are shown per item.", "", "| ID | Recording | Category | Licence | Commercial use | Share-alike | Authenticity | Review |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for asset in data["assets"]:
        rows.append("| {id} | [{title}]({file}) | {category} | {license} | {commercial_use} | {share_alike} | {authenticity} | {review} |".format(
            id=asset.get("id", ""), title=asset.get("title", ""), file=asset.get("file", ""), category=asset.get("category", ""),
            license=asset.get("license", "unknown"), commercial_use=asset.get("commercial_use", "unknown"), share_alike=asset.get("share_alike", "unknown"), authenticity=asset.get("authenticity", "unknown"), review=asset.get("review", {}).get("status", "not reviewed")))
    return "\n".join(rows) + "\n"


def render_attribution(manifest_path: Path) -> str:
    data = load_manifest(manifest_path)
    rows = ["# Audio attribution", "", "Generated from `manifest.json`. Apply each item's licence terms when redistributing it. Candidate review status is explicit.", ""]
    for asset in data["assets"]:
        rows.extend((f"## {asset.get('title', asset.get('id', 'Untitled'))}", "", f"- File: `{asset.get('file', '')}`", f"- Attribution: {asset.get('attribution', 'Missing')}", f"- Licence: [{asset.get('license', 'unknown')}]({asset.get('license_url', '')})", f"- Commercial use: `{asset.get('commercial_use', 'unknown')}`", f"- Share-alike: `{asset.get('share_alike', 'unknown')}`", f"- Authenticity: `{asset.get('authenticity', 'unknown')}`", f"- Review: `{asset.get('review', {}).get('status', 'not reviewed')}`", ""))
    return "\n".join(rows)


def coverage_data(manifest_path: Path) -> dict:
    data = load_manifest(manifest_path)
    categories = {
        "crane_hoist_movement": {"manifest_categories": ["crane_movement"], "candidate_count": 0, "release_ready_count": 0, "duration_seconds": 0.0},
        "container_contact_placement": {"manifest_categories": ["container_contact_placement"], "candidate_count": 0, "release_ready_count": 0, "duration_seconds": 0.0},
        "carrier_tractor_movement": {"manifest_categories": ["carrier_movement"], "candidate_count": 0, "release_ready_count": 0, "duration_seconds": 0.0},
        "terminal_warnings": {"manifest_categories": ["terminal_warning_candidate"], "candidate_count": 0, "release_ready_count": 0, "duration_seconds": 0.0},
        "reefer_ambience": {"manifest_categories": ["reefer_ambience"], "candidate_count": 0, "release_ready_count": 0, "duration_seconds": 0.0},
        "harbour_ambience": {"manifest_categories": ["harbour_ambience"], "candidate_count": 0, "release_ready_count": 0, "duration_seconds": 0.0},
        "port_harbour_soundscapes": {"manifest_categories": ["port_harbour_soundscape"], "candidate_count": 0, "release_ready_count": 0, "duration_seconds": 0.0},
        "terminal_cargo_port_candidates": {"manifest_categories": ["terminal_or_cargo_port_candidate"], "candidate_count": 0, "release_ready_count": 0, "duration_seconds": 0.0},
    }
    for category in categories.values():
        for asset in data["assets"]:
            if asset.get("category") in category["manifest_categories"]:
                category["candidate_count"] += 1
                if asset.get("review", {}).get("status") == "release_ready":
                    category["release_ready_count"] += 1
                category["duration_seconds"] += float(asset.get("duration_seconds", 0) or 0)
    assets = data["assets"]
    return {
        "schema_version": 1,
        "audio_candidate_count": len(assets),
        "release_ready_count": sum(1 for asset in assets if asset.get("review", {}).get("status") == "release_ready"),
        "browser_ready_count": 0,
        "browser_compatible_preview_count": sum(1 for asset in assets if (manifest_path.resolve().parent / "assets" / "browser-candidates" / f"{asset.get('id', '')}.mp3").is_file()),
        "duration_seconds": round(sum(float(asset.get("duration_seconds", 0) or 0) for asset in assets), 3),
        "commercial_use_allowed_count": sum(1 for asset in assets if asset.get("commercial_use") == "allowed"),
        "share_alike_count": sum(1 for asset in assets if asset.get("share_alike") is True),
        "unauditioned_count": sum(1 for asset in assets if asset.get("review", {}).get("status") != "release_ready"),
        "categories": categories,
        "note": "Counts reflect manifest entries, including unauditioned candidates. Candidates are not release-ready or browser-ready.",
    }


def render_browser_mapping(manifest_path: Path) -> str:
    data = load_manifest(manifest_path)
    mapping = {
        "schema_version": 1,
        "status": "candidate_inventory_only",
        "note": "No reviewed browser-ready clips exist. These entries are source candidates, not validated event mappings.",
        "assets": [
            {"asset_id": asset.get("id"), "category": asset.get("category"), "source_file": asset.get("file"), "preview_file": f"assets/browser-candidates/{asset.get('id', '')}.mp3" if (manifest_path.resolve().parent / "assets" / "browser-candidates" / f"{asset.get('id', '')}.mp3").is_file() else None, "browser_compatible_preview": (manifest_path.resolve().parent / "assets" / "browser-candidates" / f"{asset.get('id', '')}.mp3").is_file(), "browser_ready": False, "event_mapping": None, "license": asset.get("license"), "commercial_use": asset.get("commercial_use"), "share_alike": asset.get("share_alike"), "review_status": asset.get("review", {}).get("status")}
            for asset in data["assets"]
        ],
    }
    return json.dumps(mapping, indent=2) + "\n"


def prepare_browser_candidates(manifest_path: Path, output_dir: str, dry_run: bool = False) -> Path:
    """Transcode candidates to MP3 previews while preserving an explicit review gate."""
    root = manifest_path.resolve().parent
    data = load_manifest(manifest_path)
    destination = _asset_path(root, output_dir)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise CollectionError("FFmpeg is required for browser preview conversion")
    plans = []
    for asset in data["assets"]:
        source = _asset_path(root, asset["file"])
        target = destination / f"{asset['id']}.mp3"
        _asset_path(root, str(target.relative_to(root)))
        if target.exists() and not dry_run:
            raise CollectionError(f"Refusing to overwrite existing file: {target}")
        plans.append((asset, source, target))
    report_path = destination / "preview-manifest.json"
    if report_path.exists() and not dry_run:
        raise CollectionError(f"Refusing to overwrite existing file: {report_path}")
    if dry_run:
        return destination
    destination.mkdir(parents=True, exist_ok=True)
    previews = []
    for asset, source, target in plans:
        completed = subprocess.run(
            [ffmpeg, "-v", "error", "-n", "-i", str(source), "-map", "0:a:0", "-vn", "-map_metadata", "-1", "-codec:a", "libmp3lame", "-b:a", "192k", str(target)],
            check=False, capture_output=True, text=True,
        )
        if completed.returncode != 0:
            raise CollectionError(f"FFmpeg conversion failed for {source.name}: {completed.stderr.strip()}")
        output_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        probe = inspect_media(target)
        previews.append({
            "asset_id": asset["id"], "file": str(target.relative_to(root)),
            "source_file": asset["file"], "source_sha256": asset["sha256"],
            "sha256": output_hash, "license": asset["license"],
            "license_url": asset["license_url"], "attribution": asset["attribution"],
            "commercial_use": asset["commercial_use"], "share_alike": asset["share_alike"],
            "codec": "MP3", "browser_compatible_preview": True,
            "review_status": "preview_not_auditioned", "release_ready": False,
            "processing": "FFmpeg libmp3lame, 192 kbit/s CBR; metadata stripped; no normalization or fades.",
            "media_info": probe,
        })
    report = {"schema_version": 1, "status": "preview_only_not_release_ready", "assets": previews}
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return destination
