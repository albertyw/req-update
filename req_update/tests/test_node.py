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
        self.mock_commit_git = MagicMock()
        setattr(self.node.util, 'commit_git', self.mock_commit_git)

    def test_install(self) -> None:
        self.node.update_install_dependencies()
        self.assertTrue(self.mock_execute_shell.called)
        self.assertTrue(self.mock_commit_git.called)
