import argparse
import io
import sys
from typing import List
import unittest
from unittest.mock import MagicMock, Mock, patch

from req_update import req_update


class TestMain(unittest.TestCase):
    @patch('req_update.req_update.check_repository_cleanliness')
    def test_main(self, mock_check: Mock) -> None:
        req_update.main()
        self.assertTrue(mock_check.called)


class TestGetArgs(unittest.TestCase):
    def get_args_with_argv(self, argv: List[str]) -> argparse.Namespace:
        argv = ['req_update.py'] + argv
        with patch.object(sys, 'argv', argv):
            args = req_update.get_args()
        return args

    def test_none(self) -> None:
        args = self.get_args_with_argv([])
        self.assertFalse(args.verbose)

    def test_verbose(self) -> None:
        args = self.get_args_with_argv(['--verbose'])
        self.assertTrue(args.verbose)
        args = self.get_args_with_argv(['-v'])
        self.assertTrue(args.verbose)

    def test_version(self) -> None:
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            with self.assertRaises(SystemExit):
                self.get_args_with_argv(['--version'])
            self.assertTrue(len(mock_out.getvalue()) > 0)


class TestCheckRepositoryCleanliness(unittest.TestCase):
    @patch('req_update.req_update.execute_shell')
    def test_clean(self, mock_execute_shell: Mock) -> None:
        mock_execute_shell.return_value = MagicMock(stdout='')
        req_update.check_repository_cleanliness()

    @patch('req_update.req_update.execute_shell')
    def test_unclean(self, mock_execute_shell: Mock) -> None:
        mock_execute_shell.return_value = MagicMock(
            stdout=' M req_update/req_update.py'
        )
        with self.assertRaises(RuntimeError):
            req_update.check_repository_cleanliness()


class TestCreateBranch(unittest.TestCase):
    def test_create_branch(self) -> None:
        req_update.create_branch()


class TestUpdateDependencies(unittest.TestCase):
    def test_update_dependencies(self) -> None:
        req_update.update_dependencies()


class TestGetPipOutdated(unittest.TestCase):
    def test_get_pip_outdated(self) -> None:
        req_update.get_pip_outdated()


class TestWriteDependencyUpdate(unittest.TestCase):
    def test_write_dependency_update(self) -> None:
        req_update.write_dependency_update('varsnap', '1.2.3')


class TestCommitDependencyUpdate(unittest.TestCase):
    def test_commit_dependency_update(self) -> None:
        req_update.commit_dependency_update('varsnap', '1.2.3')


class TestExecuteShell(unittest.TestCase):
    def test_ls(self) -> None:
        result = req_update.execute_shell(['ls'])
        self.assertTrue(len(result.stdout) > 0)
        files = result.stdout.decode('utf-8').split('\n')
        self.assertIn('requirements-test.txt', files)
