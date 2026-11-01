#!/usr/bin/env python3
"""Generate in staging, then publish or compare only the designated output trees."""

import argparse
import io
import json
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile


IDL = Path(__file__).resolve().parents[1]
ROOT = IDL.parent
TOOLS = json.loads((IDL / "toolchain.json").read_text())


def run(*args, **kwargs):
    return subprocess.run(args, cwd=IDL, check=True, **kwargs)


def check_tools():
    actual = run("buf", "--version", capture_output=True, text=True).stdout.strip()
    if actual != TOOLS["buf"]:
        raise ValueError(f"Expected Buf {TOOLS['buf']}, got {actual}")
    actual = run("node", "--version", capture_output=True, text=True).stdout.strip().lstrip("v")
    if actual != TOOLS["node"]:
        raise ValueError(f"Expected Node {TOOLS['node']}, got {actual}")


def files(directory):
    if not directory.exists():
        return {}
    result = {}
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlink inside generated output: {path}")
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = path.read_bytes()
    return result


def check_output(path):
    for candidate in (path, *path.parents):
        if candidate == ROOT:
            break
        if candidate.is_symlink() or (candidate.exists() and not candidate.is_dir()):
            raise ValueError(f"Invalid generated output directory: {candidate}")
    files(path)


def generate(compare):
    check_tools()
    targets = [ROOT / "internal/gen", IDL / "openapi", ROOT / "ui/src/api/generated"]
    for path in targets:
        check_output(path)
    with tempfile.TemporaryDirectory(prefix="contracts-") as temporary:
        stage = Path(temporary)
        outputs = [stage / "go", stage / "openapi", stage / "ts"]
        config = json.loads((IDL / "buf.gen.yaml").read_text())
        for plugin in config["plugins"]:
            plugin["out"] = str(outputs[1] if plugin["out"] == "openapi" else outputs[0])
        template = stage / "buf.gen.json"
        template.write_text(json.dumps(config))
        run("buf", "generate", "--template", str(template))
        generated = list(outputs[1].glob("*.swagger.yaml"))
        if len(generated) != 1:
            raise ValueError("Expected exactly one merged OpenAPI document")
        document = outputs[1] / TOOLS["openapi"]
        generated[0].rename(document)
        run("node", "scripts/generate-client.mjs", str(document), str(outputs[2]))
        differences = []
        for target, output in zip(targets, outputs):
            if files(target) != files(output):
                differences.append(str(target.relative_to(ROOT)))
        if compare:
            if differences:
                raise ValueError("Generated code is stale: " + ", ".join(differences) + "; run make generate")
            print("Generated outputs match their specifications")
            return
        # Generation succeeded before any tracked output is replaced.
        for target, output in zip(targets, outputs):
            target.parent.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix=".generated-", dir=target.parent))
            backup = staging / "previous"
            replacement = staging / "next"
            shutil.copytree(output, replacement)
            try:
                if target.exists():
                    target.rename(backup)
                replacement.rename(target)
            except Exception:
                if backup.exists() and not target.exists():
                    backup.rename(target)
                raise
            finally:
                shutil.rmtree(staging)
        print("Updated Go, OpenAPI and TypeScript outputs")


def breaking():
    check_tools()
    base = os.environ.get("IDL_BASE_REF", TOOLS["breakingBase"])
    previous = run("git", "ls-tree", "-r", "--name-only", base, "--", "proto", capture_output=True, text=True).stdout
    if not any(path.endswith(".proto") for path in previous.splitlines()):
        print(f"No previous proto contracts at {base}; first publication, compatibility check skipped")
        return
    archive = run("git", "archive", "--format=tar", base, capture_output=True).stdout
    with tempfile.TemporaryDirectory(prefix="contracts-base-") as temporary:
        directory = Path(temporary).resolve()
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                path = (directory / member.name).resolve()
                if (path != directory and directory not in path.parents) or member.issym() or member.islnk():
                    raise ValueError("Unsafe path in baseline archive")
            tar.extractall(directory)
        run("buf", "breaking", "--against", str(directory))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "check", "breaking"))
    command = parser.parse_args().command
    try:
        if command == "breaking":
            breaking()
        else:
            generate(compare=command == "check")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
