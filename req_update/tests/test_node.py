from __future__ import annotations
import subprocess
from typing import List
import unittest
from unittest.mock import MagicMock, patch

from req_update import node


class TestCheckApplicable(unittest.TestCase):
    def setUp(self) -> None:
        self.node = node.Node()
        self.mock_execute_shell = MagicMock()
        setattr(self.node.util, 'execute_shell', self.mock_execute_shell)

    @patch('os.listdir')
    def test_applicable(self, mock_listdir: MagicMock) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
            suppress_output: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        mock_listdir.return_value = ['package.json', 'package-lock.json']
        applicable = self.node.check_applicable()
        self.assertTrue(applicable)

    def test_no_npm(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
            suppress_output: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            raise subprocess.CalledProcessError(1, 'asdf')
        self.mock_execute_shell.side_effect = execute_shell_returns
        applicable = self.node.check_applicable()
        self.assertFalse(applicable)

    @patch('os.listdir')
    def test_no_package(self, mock_listdir: MagicMock) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
            suppress_output: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        mock_listdir.return_value = []
        applicable = self.node.check_applicable()
        self.assertFalse(applicable)


class TestUpdateInstallDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.node = node.Node()
        self.mock_execute_shell = MagicMock()
        setattr(self.node.util, 'execute_shell', self.mock_execute_shell)
        self.mock_clean = MagicMock()
        setattr(
            self.node.util, 'check_repository_cleanliness', self.mock_clean
        )
        self.mock_commit_git = MagicMock()
        setattr(self.node.util, 'commit_git', self.mock_commit_git)
        self.mock_push = MagicMock()
        setattr(self.node.util, 'push_dependency_update', self.mock_push)

    def test_install_no_updates(self) -> None:
        updates = self.node.update_install_dependencies()
        self.assertFalse(updates)
        self.assertTrue(self.mock_execute_shell.called)
        self.assertTrue(self.mock_clean.called)
        self.assertFalse(self.mock_commit_git.called)
        self.assertFalse(self.mock_push.called)

    def test_push(self) -> None:
        self.mock_clean.side_effect = RuntimeError()
        updates = self.node.update_install_dependencies()
        self.assertTrue(updates)
        self.assertTrue(self.mock_execute_shell.called)
        self.assertTrue(self.mock_clean.called)
        self.assertTrue(self.mock_commit_git.called)
        self.assertTrue(self.mock_push.called)
