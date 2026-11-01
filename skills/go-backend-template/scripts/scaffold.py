#!/usr/bin/env python3
"""Render the bundled Go backend skeleton into a new or empty directory."""

import argparse
from pathlib import Path
import re


GO_KEYWORDS = set(
    "break default func interface select case defer go map struct chan else goto "
    "package switch const fallthrough if range type continue for import return var".split()
)


class DirectoryNotEmptyError(ValueError):
    """The destination already contains files."""


def render(text, replacements):
    for token, value in replacements.items():
        text = text.replace(token, value)
    if re.search(r"__[A-Z_]+__", text):
        raise ValueError("Unresolved template token")
    return text


def scaffold(args):
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", args.name):
        raise ValueError("Project name must use lowercase letters, digits, hyphens or underscores")
    for name in (args.context, args.model):
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name in GO_KEYWORDS or name == "_":
            raise ValueError(f"Invalid Go package name: {name}")
    if args.context in {"bootstrap", "platform"}:
        raise ValueError("Context name is reserved: bootstrap/platform")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", args.module):
        raise ValueError("Invalid module path")
    if any(part in {"", ".", ".."} for part in args.module.split("/")):
        raise ValueError("Module path must not contain empty, dot or parent segments")
    if not re.fullmatch(r"1\.\d+(?:\.\d+)?", args.go_version):
        raise ValueError("Go version must look like 1.27.0 or 1.27")

    destination = args.destination.expanduser().resolve()
    if destination.exists() and not destination.is_dir():
        raise ValueError("Destination must be a directory")
    if destination.exists() and any(destination.iterdir()):
        raise DirectoryNotEmptyError("Директория должна быть пустой.")

    replacements = {
        "__PROJECT_NAME__": args.name,
        "__MODULE_PATH__": args.module,
        "__GO_VERSION__": args.go_version,
        "__GO_IMAGE_TAG__": ".".join(args.go_version.split(".")[:2]),
        "__CONTEXT_NAME__": args.context,
        "__MODEL_NAME__": args.model,
    }
    template = Path(__file__).resolve().parents[1] / "assets" / "template"
    planned = []
    for source in sorted(template.rglob("*")):
        if source.is_file():
            relative = render(source.relative_to(template).as_posix(), replacements)
            planned.append((destination / relative, render(source.read_text(encoding="utf-8"), replacements)))
    if not planned:
        raise ValueError("Template assets are missing")

    destination.mkdir(parents=True, exist_ok=True)
    for path, content in planned:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as output:
            output.write(content)
    print(f"Created {args.name}: {len(planned)} files in {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--name", required=True, help="Project and executable name")
    parser.add_argument("--module", required=True, help="Go module path")
    parser.add_argument("--go-version", required=True, help="Requested or installed Go version")
    parser.add_argument("--context", default="example", help="Bounded context package name")
    parser.add_argument("--model", default="example", help="Domain model package name")
    args = parser.parse_args()
    try:
        scaffold(args)
    except DirectoryNotEmptyError as error:
        parser.exit(2, str(error) + "\n")
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
