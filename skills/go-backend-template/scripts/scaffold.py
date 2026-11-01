#!/usr/bin/env python3
"""Render a backend skeleton or scaffold fullstack in initialized UI/IDL submodules."""

import argparse
from pathlib import Path
import re
import configparser
import subprocess


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
    if args.context in {"bootstrap", "platform"} or (args.profile == "fullstack" and args.context in {"gen", "health"}):
        raise ValueError("Context name is reserved: bootstrap/platform/gen (and health in fullstack)")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", args.module):
        raise ValueError("Invalid module path")
    if any(part in {"", ".", ".."} for part in args.module.split("/")):
        raise ValueError("Module path must not contain empty, dot or parent segments")
    if not re.fullmatch(r"1\.\d+(?:\.\d+)?", args.go_version):
        raise ValueError("Go version must look like 1.27.0 or 1.27")
    if args.profile == "fullstack" and tuple(map(int, args.go_version.split(".")[:2])) < (1, 26):
        raise ValueError("fullstack requires Go 1.26.0 or newer for the pinned dependencies")

    destination = args.destination.expanduser().resolve()
    if destination.exists() and not destination.is_dir():
        raise ValueError("Destination must be a directory")
    if args.profile == "backend" and destination.exists() and any(destination.iterdir()):
        raise DirectoryNotEmptyError("Директория должна быть пустой.")

    replacements = {
        "__PROJECT_NAME__": args.name,
        "__API_NAMESPACE__": re.sub(r"[-_]", "", args.name),
        "__MODULE_PATH__": args.module,
        "__GO_VERSION__": args.go_version,
        "__GO_IMAGE_TAG__": ".".join(args.go_version.split(".")[:2]),
        "__CONTEXT_NAME__": args.context,
        "__MODEL_NAME__": args.model,
    }
    assets = Path(__file__).resolve().parents[1] / "assets"
    planned = {}
    for template in [assets / "template"] + ([assets / "fullstack"] if args.profile == "fullstack" else []):
        for source in sorted(template.rglob("*")):
            if source.is_file():
                relative = render(source.relative_to(template).as_posix(), replacements)
                planned[relative] = render(source.read_text(encoding="utf-8"), replacements)
    if not planned:
        raise ValueError("Template assets are missing")
    if args.profile == "fullstack":
        check_submodules(destination)
        # Generation is a separate, explicit step. It must only write into new paths.
        for relative in ("internal/gen", "idl/openapi", "ui/src/api/generated"):
            path = safe_path(destination, relative)
            if path.exists():
                raise ValueError(f"Generated output already exists: {relative}")
    originals = {}
    for relative, content in list(planned.items()):
        path = safe_path(destination, relative)
        if not path.exists():
            continue
        if args.profile == "fullstack" and path.name == "README.md" and path.is_file():
            original = path.read_text(encoding="utf-8")
            marker = "<!-- go-backend-template:fullstack -->"
            if marker in original:
                raise ValueError(f"Template README block already exists: {relative}")
            originals[path] = original
            planned[relative] = original.rstrip() + "\n\n" + marker + "\n" + content
        else:
            raise ValueError(f"File conflict: {relative}")
    # All destinations, including parents in each submodule, were checked before writing.
    created = []
    rewritten = []
    try:
        for relative, content in planned.items():
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if path in originals:
                rewritten.append(path)
                path.write_text(content, encoding="utf-8")
            else:
                with path.open("x", encoding="utf-8", newline="\n") as output:
                    created.append(path)
                    output.write(content)
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        for path in rewritten:
            path.write_text(originals[path], encoding="utf-8")
        raise
    print(f"Created {args.name} ({args.profile}): {len(planned)} files in {destination}")
    if args.profile == "fullstack":
        print("Next: npm ci --prefix idl && npm ci --prefix ui && make generate && go mod tidy && make check build")


def safe_path(destination, relative):
    path = destination / relative
    for candidate in (path, *path.parents):
        if candidate == destination:
            break
        if candidate.is_symlink():
            raise ValueError(f"Symlink in output path: {relative}")
        if candidate != path and candidate.exists() and not candidate.is_dir():
            raise ValueError(f"Output parent is not a directory: {relative}")
    return path


def check_submodules(destination):
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read_string((destination / ".gitmodules").read_text(encoding="utf-8"))
    except (OSError, configparser.Error) as error:
        raise ValueError("fullstack requires existing initialized ui and idl Git submodules") from error
    paths = {config.get(section, "path", fallback="") for section in config.sections()}
    for name in ("ui", "idl"):
        path = safe_path(destination, name)
        if name not in paths or not path.is_dir():
            raise ValueError(f"Missing initialized submodule: {name}")
        result = subprocess.run(["git", "-C", str(destination), "ls-files", "--stage", "--", name], capture_output=True, text=True)
        top = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if result.returncode or not result.stdout.startswith("160000 ") or top.returncode or Path(top.stdout.strip()).resolve() != path.resolve():
            raise ValueError(f"Not an initialized Git submodule: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--profile", choices=("backend", "fullstack"), default="backend")
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
