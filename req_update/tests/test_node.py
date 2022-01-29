from __future__ import annotations
import json
import os
import subprocess
import tempfile
from typing import Any, List, Mapping, cast
import unittest
from unittest.mock import MagicMock, patch

from req_update import node


MOCK_NPM_OUTDATED = {
    "dotenv": {
        "current": "5.0.0",
        "wanted": "5.2.0",
        "latest": "5.2.0",
    },
    "varsnap": {
        "current": "1.0.0",
        "wanted": "1.0.1",
        "latest": "1.0.1",
    },
}


class TestCheckApplicable(unittest.TestCase):
    def setUp(self) -> None:
        self.node = node.Node()
        self.mock_execute_shell = MagicMock()
        setattr(self.node.util, "execute_shell", self.mock_execute_shell)

    @patch("os.listdir")
    def test_applicable(self, mock_listdir: MagicMock) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
            suppress_output: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            return MagicMock(stdout="")

        self.mock_execute_shell.side_effect = execute_shell_returns
        mock_listdir.return_value = ["package.json", "package-lock.json"]
        applicable = self.node.check_applicable()
        self.assertTrue(applicable)

    def test_no_npm(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
            suppress_output: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            raise subprocess.CalledProcessError(1, "asdf")

        self.mock_execute_shell.side_effect = execute_shell_returns
        applicable = self.node.check_applicable()
        self.assertFalse(applicable)

    @patch("os.listdir")
    def test_no_package(self, mock_listdir: MagicMock) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
            suppress_output: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            return MagicMock(stdout="")

        self.mock_execute_shell.side_effect = execute_shell_returns
        mock_listdir.return_value = []
        applicable = self.node.check_applicable()
        self.assertFalse(applicable)


class TestUpdateInstallDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.node = node.Node()
        self.mock_unpinned = MagicMock()
        setattr(self.node, "update_unpinned_dependencies", self.mock_unpinned)
        self.mock_pinned = MagicMock()
        setattr(self.node, "update_pinned_dependencies", self.mock_pinned)
        self.mock_warn = MagicMock()
        setattr(self.node.util, "warn", self.mock_warn)

    def test_none(self) -> None:
        self.mock_unpinned.return_value = False
        self.mock_pinned.return_value = False
        updated = self.node.update_install_dependencies()
        self.assertFalse(updated)
        self.assertTrue(self.mock_warn.called)

    def test_pinned(self) -> None:
        self.mock_unpinned.return_value = False
        self.mock_pinned.return_value = True
        updated = self.node.update_install_dependencies()
        self.assertTrue(updated)
        self.assertFalse(self.mock_warn.called)

    def test_unpinned(self) -> None:
        self.mock_unpinned.return_value = True
        self.mock_pinned.return_value = False
        updated = self.node.update_install_dependencies()
        self.assertTrue(updated)
        self.assertFalse(self.mock_warn.called)

    def test_all(self) -> None:
        self.mock_unpinned.return_value = True
        self.mock_pinned.return_value = True
        updated = self.node.update_install_dependencies()
        self.assertTrue(updated)
        self.assertFalse(self.mock_warn.called)


class TestUpdateUnpinnedDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.node = node.Node()
        self.mock_execute_shell = MagicMock()
        setattr(self.node.util, "execute_shell", self.mock_execute_shell)
        self.mock_clean = MagicMock()
        setattr(
            self.node.util, "check_repository_cleanliness", self.mock_clean
        )
        self.mock_commit_git = MagicMock()
        setattr(self.node.util, "commit_git", self.mock_commit_git)
        self.mock_push = MagicMock()
        setattr(self.node.util, "push_dependency_update", self.mock_push)
        self.mock_log = MagicMock()
        setattr(self.node.util, "log", self.mock_log)

    def test_install_no_updates(self) -> None:
        updates = self.node.update_unpinned_dependencies()
        self.assertFalse(updates)
        self.assertTrue(self.mock_execute_shell.called)
        self.assertTrue(self.mock_clean.called)
        self.assertFalse(self.mock_commit_git.called)
        self.assertFalse(self.mock_push.called)

    def test_push(self) -> None:
        self.mock_clean.side_effect = RuntimeError()
        updates = self.node.update_unpinned_dependencies()
        self.assertTrue(updates)
        self.assertTrue(self.mock_execute_shell.called)
        self.assertTrue(self.mock_clean.called)
        self.assertTrue(self.mock_commit_git.called)
        self.assertTrue(self.mock_push.called)


class TestUpdatePinnedDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.node = node.Node()
        self.mock_get_outdated = MagicMock()
        setattr(self.node, "get_outdated", self.mock_get_outdated)
        self.mock_update_package = MagicMock()
        setattr(self.node, "update_package", self.mock_update_package)

    def test_update_no_pinned_dependencies(self) -> None:
        self.mock_get_outdated.return_value = []
        updated = self.node.update_pinned_dependencies()
        self.assertFalse(updated)

    def test_update_pinned_dependencies(self) -> None:
        self.mock_get_outdated.return_value = MOCK_NPM_OUTDATED
        self.mock_update_package.return_value = True
        updated = self.node.update_pinned_dependencies()
        self.assertTrue(updated)
        self.assertEqual(len(self.mock_update_package.call_args), 2)
        names = [c[0][0] for c in self.mock_update_package.call_args_list]
        self.assertTrue("dotenv" in names)
        self.assertTrue("varsnap" in names)

    def test_update_unknown_dependencies(self) -> None:
        self.mock_get_outdated.return_value = MOCK_NPM_OUTDATED
        self.mock_update_package.return_value = False
        updated = self.node.update_pinned_dependencies()
        self.assertFalse(updated)


class TestGetOutdated(unittest.TestCase):
    def setUp(self) -> None:
        self.node = node.Node()
        self.mock_execute_shell = MagicMock()
        setattr(self.node.util, "execute_shell", self.mock_execute_shell)

    def test_get_outdated(self) -> None:
        self.mock_execute_shell().stdout = json.dumps(MOCK_NPM_OUTDATED)
        data = self.node.get_outdated()
        self.assertEqual(data, MOCK_NPM_OUTDATED)


class TestUpdatePackage(unittest.TestCase):
    def setUp(self) -> None:
        self.node = node.Node()
        self.mock_log = MagicMock()
        setattr(self.node.util, "log", self.mock_log)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)

    def tearDown(self) -> None:
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def write_package(self, data: Mapping[str, Any]) -> None:
        with open("package.json", "w") as handle:
            handle.write(json.dumps(data))

    def read_package(self) -> Mapping[str, Any]:
        with open("package.json", "r") as handle:
            package_string = handle.read()
        package = cast(Mapping[str, Any], json.loads(package_string))
        return package

    def test_no_updates(self) -> None:
        original_package: Mapping[str, Any] = {
            "dependencies": {},
            "devDependencies": {},
        }
        self.write_package(original_package)
        mock_update = MagicMock()
        setattr(self.node, "update_package_dependencies", mock_update)
        self.node.update_package("varsnap", MOCK_NPM_OUTDATED["varsnap"])
        self.assertFalse(mock_update.called)
        package = self.read_package()
        self.assertEqual(package, original_package)

    def test_prod_updates(self) -> None:
        original_package: Mapping[str, Any] = {
            "dependencies": {"varsnap": "1.0.0"},
            "devDependencies": {},
        }
        self.write_package(original_package)
        self.node.update_package("varsnap", MOCK_NPM_OUTDATED["varsnap"])
        package = self.read_package()
        self.assertNotEqual(package, original_package)
        self.assertEqual(package["dependencies"]["varsnap"], "^1.0.0")

    def test_dev_updates(self) -> None:
        original_package: Mapping[str, Any] = {
            "dependencies": {},
            "devDependencies": {"varsnap": "1.0.0"},
        }
        self.write_package(original_package)
        self.node.update_package("varsnap", MOCK_NPM_OUTDATED["varsnap"])
        package = self.read_package()
        self.assertNotEqual(package, original_package)
        self.assertEqual(package["devDependencies"]["varsnap"], "^1.0.0")


class TestGeneratePackageVersion(unittest.TestCase):
    def test_major(self) -> None:
        self.assertEqual(node.Node.generate_package_version("1.0.0"), "^1.0.0")
        self.assertEqual(node.Node.generate_package_version("1.5.0"), "^1.0.0")
        self.assertEqual(node.Node.generate_package_version("1.0.5"), "^1.0.0")

    def test_minor(self) -> None:
        self.assertEqual(node.Node.generate_package_version("0.1.0"), "^0.1.0")
        self.assertEqual(node.Node.generate_package_version("0.1.5"), "^0.1.0")

    def test_patch(self) -> None:
        self.assertEqual(node.Node.generate_package_version("0.0.1"), "0.0.1")

    def test_not_semver(self) -> None:
        self.assertEqual(node.Node.generate_package_version("asdf"), "asdf")
