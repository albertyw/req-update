from __future__ import annotations

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from req_update import go


class TestCheckApplicable(unittest.TestCase):
    def setUp(self) -> None:
        self.go = go.Go()
        self.mock_execute_shell = MagicMock()
        setattr(self.go.util, "execute_shell", self.mock_execute_shell)

    @patch("os.listdir")
    def test_applicable(self, mock_listdir: MagicMock) -> None:
        self.mock_execute_shell.return_value = MagicMock()
        mock_listdir.return_value = ["go.mod", "go.sum"]
        result = self.go.check_applicable()
        self.assertTrue(result)

    @patch("os.listdir")
    def test_no_go(self, mock_listdir: MagicMock) -> None:
        error = subprocess.CalledProcessError(1, "asdf")
        self.mock_execute_shell.side_effect = error
        mock_listdir.return_value = ["go.mod", "go.sum"]
        result = self.go.check_applicable()
        self.assertFalse(result)

    @patch("os.listdir")
    def test_no_go_mod(self, mock_listdir: MagicMock) -> None:
        self.mock_execute_shell.side_effect = MagicMock()
        mock_listdir.return_value = ["go.sum"]
        result = self.go.check_applicable()
        self.assertFalse(result)

    @patch("os.listdir")
    def test_no_go_sum(self, mock_listdir: MagicMock) -> None:
        self.mock_execute_shell.side_effect = MagicMock()
        mock_listdir.return_value = ["go.mod"]
        result = self.go.check_applicable()
        self.assertFalse(result)


class TestUpdateInstallDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.go = go.Go()

    def test(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.go.update_install_dependencies()
