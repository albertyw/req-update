from __future__ import annotations
import io
import subprocess
from typing import List
import unittest
from unittest.mock import MagicMock, patch

from req_update import util


class TestCheckRepositoryCleanliness(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.mock_execute_shell = MagicMock()
        setattr(self.util, 'execute_shell', self.mock_execute_shell)

    def test_clean(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if 'pip' in command:
                return MagicMock(stdout='pip 20.2.4')
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        self.util.check_repository_cleanliness()

    def test_unclean(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(
            stdout=' M util/util.py'
        )
        with self.assertRaises(RuntimeError):
            self.util.check_repository_cleanliness()


class TestCommitGit(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.mock_log = MagicMock()
        setattr(self.util, 'log', self.mock_log)
        self.mock_execute_shell = MagicMock()
        setattr(self.util, 'execute_shell', self.mock_execute_shell)

    def test_commit_git(self) -> None:
        self.util.commit_git('commit message')
        self.assertTrue(self.mock_log.called)
        log_value = self.mock_log.mock_calls[0][1]
        self.assertIn('commit message', log_value[0])
        self.assertTrue(self.mock_execute_shell.called)
        command = self.mock_execute_shell.mock_calls[0][1]
        self.assertIn('commit message', command[0][3])


class TestCommitDependencyUpdate(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.mock_commit_git = MagicMock()
        setattr(self.util, 'commit_git', self.mock_commit_git)

    def test_commit_dependency_update(self) -> None:
        self.util.commit_dependency_update('varsnap', '1.2.3')
        self.assertTrue(self.mock_commit_git.called)
        commit_message = self.mock_commit_git.mock_calls[0][1]
        self.assertIn('varsnap', commit_message[0])
        self.assertIn('1.2.3', commit_message[0])


class TestCreateBranch(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.mock_execute_shell = MagicMock()
        setattr(self.util, 'execute_shell', self.mock_execute_shell)

    def test_create_branch(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        self.util.create_branch()
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 2)
        branch_call = self.mock_execute_shell.mock_calls[0]
        self.assertEqual(branch_call[1][0][1], 'branch')
        create_call = self.mock_execute_shell.mock_calls[1]
        self.assertIn('-b', create_call[1][0])
        self.assertFalse(self.util.branch_exists)

    def test_create_branch_exists(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if 'branch' in command:
                return MagicMock(stdout='dep-update')
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        self.util.create_branch()
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 2)
        branch_call = self.mock_execute_shell.mock_calls[0]
        self.assertEqual(branch_call[1][0][1], 'branch')
        create_call = self.mock_execute_shell.mock_calls[1]
        self.assertNotIn('-b', create_call[1][0])
        self.assertTrue(self.util.branch_exists)


class TestRollbackBranch(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.mock_execute_shell = MagicMock()
        setattr(self.util, 'execute_shell', self.mock_execute_shell)

    def test_rollback(self) -> None:
        self.util.rollback_branch()
        checkout = self.mock_execute_shell.mock_calls[0]
        self.assertIn('checkout', checkout[1][0])
        delete = self.mock_execute_shell.mock_calls[1]
        self.assertIn('branch', delete[1][0])
        self.assertIn('-d', delete[1][0])

    def test_does_not_rollback_already_exists(self) -> None:
        self.util.branch_exists = True
        self.util.rollback_branch()
        self.assertFalse(self.mock_execute_shell.called)


class TestPushDependencyUpdate(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.mock_log = MagicMock()
        setattr(self.util, 'log', self.mock_log)
        self.mock_execute_shell = MagicMock()
        setattr(self.util, 'execute_shell', self.mock_execute_shell)

    def test_push_dependency_update_false(self) -> None:
        self.util.push_dependency_update()
        self.assertFalse(self.mock_log.called)
        self.assertFalse(self.mock_execute_shell.called)

    def test_push_dependency_update(self) -> None:
        self.util.push = True
        self.util.push_dependency_update()
        self.assertTrue(self.mock_log.called)
        log_value = self.mock_log.mock_calls[0][1]
        self.assertIn('Push', log_value[0])
        self.assertTrue(self.mock_execute_shell.called)
        command = self.mock_execute_shell.mock_calls[0][1]
        self.assertIn('push', command[0])


class TestCheckMajorVersionUpdate(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.mock_log = MagicMock()
        setattr(self.util, 'log', self.mock_log)

    def test_check_non_major_update(self) -> None:
        result = self.util.check_major_version_update(
            'varsnap', '1.0.0', '1.2.3'
        )
        self.assertFalse(result)
        self.assertFalse(self.mock_log.called)
        result = self.util.check_major_version_update(
            'varsnap', '1.0.0', '1.0.3'
        )
        self.assertFalse(result)
        self.assertFalse(self.mock_log.called)

    def test_check_major_update(self) -> None:
        result = self.util.check_major_version_update(
            'varsnap', '1.0.0', '2.0.0'
        )
        self.assertTrue(result)
        self.assertTrue(self.mock_log.called)
        log_value = self.mock_log.call_args[0][0]
        self.assertIn('varsnap', log_value)
        self.assertIn('1.0.0', log_value)
        self.assertIn('2.0.0', log_value)

    def test_semver_not_three_part(self) -> None:
        result = self.util.check_major_version_update(
            'varsnap', 'asdf', '2.0.0'
        )
        self.assertEqual(result, None)
        self.assertFalse(self.mock_log.called)
        result = self.util.check_major_version_update(
            'varsnap', '1.0', '2.0.0'
        )
        self.assertEqual(result, None)
        self.assertFalse(self.mock_log.called)
        result = self.util.check_major_version_update(
            'varsnap', '1.0.0', '2.0'
        )
        self.assertEqual(result, None)
        self.assertFalse(self.mock_log.called)

    def test_semver_not_integer(self) -> None:
        result = self.util.check_major_version_update(
            'varsnap', 'a.0.0', '2.0.0'
        )
        self.assertEqual(result, None)
        self.assertFalse(self.mock_log.called)
        result = self.util.check_major_version_update(
            'varsnap', '1.0.0', 'a.0.0'
        )
        self.assertEqual(result, None)
        self.assertFalse(self.mock_log.called)


class TestExecuteShell(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.util.dry_run = False
        self.mock_log = MagicMock()
        setattr(self.util, 'log', self.mock_log)

    def test_ls(self) -> None:
        result = self.util.execute_shell(['ls'], True)
        self.assertEqual(result.args, ['ls'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, '')
        self.assertTrue(len(result.stdout) > 0)
        files = result.stdout.split('\n')
        self.assertIn('requirements-test.txt', files)
        self.assertFalse(self.mock_log.called)

    def test_dry_run(self) -> None:
        self.util.dry_run = True
        result = self.util.execute_shell(['ls'], False)
        self.assertEqual(result.args, ['ls'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr, '')
        self.assertFalse(self.mock_log.called)

    def test_dry_run_read_only(self) -> None:
        self.util.dry_run = True
        result = self.util.execute_shell(['ls'], True)
        self.assertTrue(len(result.stdout) > 0)

    def test_verbose(self) -> None:
        self.util.verbose = True
        self.util.execute_shell(['ls'], True)
        self.assertTrue(self.mock_log.called)

    def test_error(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError):
            self.util.execute_shell(['ls', 'asdf'], True)
        self.assertTrue(self.mock_log.called)
        self.assertIn('cannot access', self.mock_log.call_args[0][0])

    def test_suppress_output(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError):
            self.util.execute_shell(['ls', 'asdf'], True, suppress_output=True)
        self.assertFalse(self.mock_log.called)


class TestLog(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()

    def test_log(self) -> None:
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.util.log('asdf')
            self.assertEqual(mock_out.getvalue(), 'asdf\n')
