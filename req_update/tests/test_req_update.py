import argparse
import io
import sys
from typing import List
import unittest
from unittest.mock import MagicMock, patch

from req_update import req_update


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()

    def test_main(self) -> None:
        mock_check = MagicMock()
        setattr(self.req_update, 'check_repository_cleanliness', mock_check)
        self.req_update.main()
        self.assertTrue(mock_check.called)


class TestGetArgs(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()

    def get_args_with_argv(self, argv: List[str]) -> argparse.Namespace:
        argv = ['req_update.py'] + argv
        with patch.object(sys, 'argv', argv):
            args = self.req_update.get_args()
        return args

    def test_none(self) -> None:
        args = self.get_args_with_argv([])
        self.assertFalse(args.verbose)

    def test_dryrun(self) -> None:
        self.assertFalse(self.req_update.dry_run)
        args = self.get_args_with_argv(['--dryrun'])
        self.assertTrue(args.dryrun)
        args = self.get_args_with_argv(['-d'])
        self.assertTrue(args.dryrun)
        self.assertTrue(self.req_update.dry_run)

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
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()
        self.mock_execute_shell = MagicMock()
        setattr(self.req_update, 'execute_shell', self.mock_execute_shell)

    def test_clean(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(stdout='')
        self.req_update.check_repository_cleanliness()

    def test_unclean(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(
            stdout=' M req_update/req_update.py'
        )
        with self.assertRaises(RuntimeError):
            self.req_update.check_repository_cleanliness()


class TestCreateBranch(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()
        self.mock_execute_shell = MagicMock()
        setattr(self.req_update, 'execute_shell', self.mock_execute_shell)

    def test_create_branch(self) -> None:
        self.req_update.create_branch()
        self.assertTrue(self.mock_execute_shell.called)


class TestUpdateDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()

    def test_update_dependencies(self) -> None:
        self.req_update.update_dependencies()


class TestGetPipOutdated(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()

    def test_get_pip_outdated(self) -> None:
        self.req_update.get_pip_outdated()


class TestWriteDependencyUpdate(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()

    def test_write_dependency_update(self) -> None:
        self.req_update.write_dependency_update('varsnap', '1.2.3')


class TestCommitDependencyUpdate(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()

    def test_commit_dependency_update(self) -> None:
        self.req_update.commit_dependency_update('varsnap', '1.2.3')


class TestExecuteShell(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()
        self.mock_log = MagicMock()
        setattr(self.req_update, 'log', self.mock_log)

    def test_ls(self) -> None:
        result = self.req_update.execute_shell(['ls'])
        self.assertEqual(result.args, ['ls'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b'')
        self.assertTrue(len(result.stdout) > 0)
        files = result.stdout.decode('utf-8').split('\n')
        self.assertIn('requirements-test.txt', files)
        self.assertFalse(self.mock_log.called)

    def test_execute_shell(self) -> None:
        self.req_update.dry_run = True
        result = self.req_update.execute_shell(['ls'])
        self.assertEqual(result.args, ['ls'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'')
        self.assertEqual(result.stderr, b'')
        self.assertTrue(self.mock_log.called)


class TestLog(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()

    def test_log(self) -> None:
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.req_update.log('asdf')
            self.assertEqual(mock_out.getvalue(), 'asdf\n')
