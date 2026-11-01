"""Command line interface for the audio collection."""
import argparse
import json
from pathlib import Path
from .catalogue import CollectionError, coverage_data, import_media, inspect_media, prepare_browser_candidates, render_attribution, render_browser_mapping, render_catalogue, validate


def main() -> None:
    parser = argparse.ArgumentParser(prog="soundscape")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "catalogue"):
        command = commands.add_parser(name)
        command.add_argument("manifest", type=Path, nargs="?", default=Path("manifest.json"))
        if name == "catalogue":
            command.add_argument("--output", type=Path, default=Path("CATALOGUE.md"))
            command.add_argument("--dry-run", action="store_true")
    importing = commands.add_parser("import", help="safely copy a local recording into the collection")
    importing.add_argument("source", type=Path)
    importing.add_argument("destination", help="collection-relative destination path")
    importing.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    importing.add_argument("--dry-run", action="store_true")
    inspection = commands.add_parser("inspect", help="inspect a local media file and its hash")
    inspection.add_argument("file", type=Path)
    reports = commands.add_parser("reports", help="generate attribution, coverage, and candidate mapping reports")
    reports.add_argument("manifest", type=Path, nargs="?", default=Path("manifest.json"))
    reports.add_argument("--output-dir", type=Path, default=Path("docs/generated"))
    reports.add_argument("--dry-run", action="store_true")
    browser = commands.add_parser("browser-prepare", help="create MP3 preview derivatives, not release assets")
    browser.add_argument("manifest", type=Path, nargs="?", default=Path("manifest.json"))
    browser.add_argument("--output-dir", default="assets/browser-candidates")
    browser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            errors = validate(args.manifest)
            if errors:
                print("\n".join(errors))
                raise SystemExit(1)
            print("Collection is valid")
        elif args.command == "catalogue":
            output = args.output.resolve()
            if output.exists() and not args.dry_run:
                parser.error(f"refusing to overwrite {output}; remove it or choose another output")
            rendered = render_catalogue(args.manifest)
            if args.dry_run:
                print(rendered, end="")
            else:
                output.write_text(rendered, encoding="utf-8")
        elif args.command == "import":
            target = import_media(args.source, args.manifest, args.destination, args.dry_run)
            print(f"Would import to {target}" if args.dry_run else f"Imported to {target}")
        elif args.command == "inspect":
            print(json.dumps(inspect_media(args.file), indent=2))
        elif args.command == "browser-prepare":
            output = prepare_browser_candidates(args.manifest, args.output_dir, args.dry_run)
            print(f"Would prepare MP3 previews in {output}" if args.dry_run else f"Prepared MP3 previews in {output}")
        else:
            output_dir = args.output_dir.resolve()
            reports_to_write = {
                "ATTRIBUTION.md": render_attribution(args.manifest),
                "COVERAGE.json": json.dumps(coverage_data(args.manifest), indent=2) + "\n",
                "EVENT-MAPPING.json": render_browser_mapping(args.manifest),
            }
            existing = [name for name in reports_to_write if (output_dir / name).exists()]
            if existing and not args.dry_run:
                parser.error(f"refusing to overwrite {', '.join(existing)} in {output_dir}")
            if args.dry_run:
                print(f"Would generate {len(reports_to_write)} reports in {output_dir}")
            else:
                output_dir.mkdir(parents=True, exist_ok=True)
                for name, content in reports_to_write.items():
                    (output_dir / name).write_text(content, encoding="utf-8")
                print(f"Generated {len(reports_to_write)} reports in {output_dir}")
    except CollectionError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
