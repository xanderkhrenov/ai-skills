#!/usr/bin/env python3
"""Behavioral checks for additive generation across three Git repositories."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("scaffold.py")


def git(directory, *args):
    return subprocess.run(
        ["git", "-c", "user.name=Template Test", "-c", "user.email=template-test@example.invalid",
         "-C", str(directory), *args], check=True, capture_output=True, text=True,
    )


def snapshot(directory):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in directory.rglob("*")
            if ".git" not in path.relative_to(directory).parts and path.is_file() and not path.is_symlink()}


class ScaffoldTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "project"

    def scaffold(self, profile="backend", **kwargs):
        args = [sys.executable, str(SCRIPT), str(self.project), "--name", "curious-map",
                "--module", "example.com/curious-map", "--go-version", "1.27.0", "--profile", profile]
        for key, value in kwargs.items():
            args.extend(["--" + key, value])
        return subprocess.run(args, capture_output=True, text=True)

    def submodules(self):
        self.project.mkdir()
        git(self.project, "init", "-b", "master")
        (self.project / "README.md").write_text("# Keep project description\n")
        for name in ("ui", "idl"):
            source = self.base / (name + "-source")
            source.mkdir()
            git(source, "init", "-b", "master")
            (source / "README.md").write_text("# Keep " + name + " description\n")
            git(source, "add", ".")
            git(source, "commit", "-m", "Initial")
            git(self.project, "-c", "protocol.file.allow=always", "submodule", "add", str(source), name)
        git(self.project, "add", ".")
        git(self.project, "commit", "-m", "Submodules")

    def test_backend_creates_new_project(self):
        result = self.scaffold()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.project / "cmd/curious-map/main.go").is_file())
        self.assertFalse((self.project / "ui").exists())
        self.assertFalse((self.project / ".git").exists())

    def test_backend_refuses_nonempty_destination_without_writes(self):
        self.project.mkdir()
        (self.project / "README.md").write_text("Existing")
        before = snapshot(self.project)
        self.assertNotEqual(self.scaffold().returncode, 0)
        self.assertEqual(snapshot(self.project), before)

    def test_fullstack_requires_real_initialized_submodules(self):
        self.project.mkdir()
        for name in ("ui", "idl"):
            (self.project / name).mkdir()
        before = snapshot(self.project)
        self.assertNotEqual(self.scaffold("fullstack").returncode, 0)
        self.assertEqual(snapshot(self.project), before)

    def test_fullstack_preserves_gitlinks_and_extends_readmes(self):
        self.submodules()
        before = snapshot(self.project)
        links = git(self.project, "ls-files", "--stage", "--", "ui", "idl").stdout
        result = self.scaffold("fullstack")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.project / ".gitmodules").read_bytes(), before[".gitmodules"])
        self.assertEqual(git(self.project, "ls-files", "--stage", "--", "ui", "idl").stdout, links)
        for relative in ("README.md", "ui/README.md", "idl/README.md"):
            self.assertTrue((self.project / relative).read_bytes().startswith(before[relative]))
        self.assertTrue((self.project / "idl/proto/curious-map/health/v1/health.proto").is_file())
        self.assertTrue((self.project / "ui/package-lock.json").is_file())

    def test_late_ui_conflict_leaves_all_three_repositories_unchanged(self):
        self.submodules()
        (self.project / "ui/package.json").write_text('{"private": true}')
        before = snapshot(self.project)
        self.assertNotEqual(self.scaffold("fullstack").returncode, 0)
        self.assertEqual(snapshot(self.project), before)

    def test_parent_file_conflict_is_detected_before_writing(self):
        self.submodules()
        (self.project / "ui/src").write_text("not a directory")
        before = snapshot(self.project)
        self.assertNotEqual(self.scaffold("fullstack").returncode, 0)
        self.assertEqual(snapshot(self.project), before)

    def test_symlink_parent_cannot_redirect_output(self):
        self.submodules()
        outside = self.base / "outside"
        outside.mkdir()
        (self.project / "ui/src").symlink_to(outside, target_is_directory=True)
        before = snapshot(self.project)
        self.assertNotEqual(self.scaffold("fullstack").returncode, 0)
        self.assertEqual(snapshot(self.project), before)
        self.assertEqual(list(outside.iterdir()), [])

    def test_existing_generated_tree_prevents_all_writes(self):
        self.submodules()
        (self.project / "internal/gen").mkdir(parents=True)
        (self.project / "internal/gen/keep.go").write_text("package gen\n")
        before = snapshot(self.project)
        self.assertNotEqual(self.scaffold("fullstack").returncode, 0)
        self.assertEqual(snapshot(self.project), before)

    def test_reserved_context_does_not_create_destination(self):
        self.assertNotEqual(self.scaffold(context="bootstrap").returncode, 0)
        self.assertFalse(self.project.exists())


if __name__ == "__main__":
    unittest.main()
