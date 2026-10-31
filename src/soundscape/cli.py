"""Command line interface for the audio collection."""
import argparse
from pathlib import Path
from .catalogue import CollectionError, render_catalogue, validate


def main() -> None:
    parser = argparse.ArgumentParser(prog="soundscape")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "catalogue"):
        command = commands.add_parser(name)
        command.add_argument("manifest", type=Path, nargs="?", default=Path("manifest.json"))
        if name == "catalogue":
            command.add_argument("--output", type=Path, default=Path("CATALOGUE.md"))
            command.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            errors = validate(args.manifest)
            if errors:
                print("\n".join(errors))
                raise SystemExit(1)
            print("Collection is valid")
        else:
            output = args.output.resolve()
            if output.exists() and not args.dry_run:
                parser.error(f"refusing to overwrite {output}; remove it or choose another output")
            rendered = render_catalogue(args.manifest)
            if args.dry_run:
                print(rendered, end="")
            else:
                output.write_text(rendered, encoding="utf-8")
    except CollectionError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
