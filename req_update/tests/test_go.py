from __future__ import annotations

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from req_update import go


class TestCheckApplicable(unittest.TestCase):
    def setUp(self) -> None:
        self.go = go.Go()
        self.mock_execute_shell = MagicMock()
        setattr(self.go.util, 'execute_shell', self.mock_execute_shell)

    @patch('os.listdir')
    def test_applicable(self, mock_listdir: MagicMock) -> None:
        self.mock_execute_shell.return_value = MagicMock()
        mock_listdir.return_value = ['go.mod', 'go.sum']
        result = self.go.check_applicable()
        self.assertTrue(result)

    @patch('os.listdir')
    def test_no_go(self, mock_listdir: MagicMock) -> None:
        error = subprocess.CalledProcessError(1, 'asdf')
        self.mock_execute_shell.side_effect = error
        mock_listdir.return_value = ['go.mod', 'go.sum']
        result = self.go.check_applicable()
        self.assertFalse(result)

    @patch('os.listdir')
    def test_no_go_mod(self, mock_listdir: MagicMock) -> None:
        self.mock_execute_shell.side_effect = MagicMock()
        mock_listdir.return_value = ['go.sum']
        result = self.go.check_applicable()
        self.assertFalse(result)

    @patch('os.listdir')
    def test_no_go_sum(self, mock_listdir: MagicMock) -> None:
        self.mock_execute_shell.side_effect = MagicMock()
        mock_listdir.return_value = ['go.mod']
        result = self.go.check_applicable()
        self.assertFalse(result)


class TestUpdateInstallDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.go = go.Go()
        self.mock_execute_shell = MagicMock()
        setattr(self.go.util, 'execute_shell', self.mock_execute_shell)
        self.mock_clean = MagicMock()
        setattr(self.go.util, 'check_repository_cleanliness', self.mock_clean)
        self.mock_log = MagicMock()
        setattr(self.go.util, 'log', self.mock_log)
        self.mock_warn = MagicMock()
        setattr(self.go.util, 'warn', self.mock_warn)

    def test_update_clean(self) -> None:
        self.mock_clean.return_value = True
        updated = self.go.update_dependencies()
        self.assertFalse(updated)
        calls = self.mock_execute_shell.call_args_list
        self.assertIn('get', calls[0][0][0])
        self.assertIn('tidy', calls[1][0][0])
        self.assertTrue(self.mock_warn.called)
        self.assertTrue(self.mock_log.called)

    def test_update_changed(self) -> None:
        self.mock_clean.side_effect = RuntimeError()
        updated = self.go.update_dependencies()
        self.assertTrue(updated)
        calls = self.mock_execute_shell.call_args_list
        self.assertIn('get', calls[0][0][0])
        self.assertIn('tidy', calls[1][0][0])
        self.assertFalse(self.mock_warn.called)
        self.assertTrue(self.mock_log.called)
