"""Command line interface for the audio collection."""
import argparse
import json
from pathlib import Path
from .catalogue import CollectionError, import_media, inspect_media, render_catalogue, validate


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
        else:
            print(json.dumps(inspect_media(args.file), indent=2))
    except CollectionError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
