import unittest
from unittest.mock import MagicMock, patch

from req_update import req_update


class TestCheckRepositoryCleanliness(unittest.TestCase):
    @patch('req_update.req_update.execute_shell')
    def test_clean(self, mock_execute_shell) -> None:
        mock_execute_shell.return_value = MagicMock(stdout='')
        req_update.check_repository_cleanliness()

    @patch('req_update.req_update.execute_shell')
    def test_unclean(self, mock_execute_shell) -> None:
        mock_execute_shell.return_value = MagicMock(
            stdout=' M req_update/req_update.py'
        )
        with self.assertRaises(RuntimeError):
            req_update.check_repository_cleanliness()


class TestExecuteShell(unittest.TestCase):
    def test_ls(self) -> None:
        result = req_update.execute_shell(['ls'])
        self.assertTrue(len(result.stdout) > 0)
        files = result.stdout.decode('utf-8').split('\n')
        self.assertIn('requirements-test.txt', files)
