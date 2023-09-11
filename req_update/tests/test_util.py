from __future__ import annotations
import io
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from req_update import util


class TestUpdater(unittest.TestCase):
    def test(self) -> None:
        updater = util.Updater()
        self.assertTrue(updater.util)
        self.assertFalse(updater.check_applicable())
        self.assertFalse(updater.update_dependencies())


class TestCheckRepositoryCleanliness(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_log = MagicMock()
        self.util = util.Util()
        self.util.dry_run = False
        self.mock_execute_shell = MagicMock()
        setattr(self.util, 'execute_shell', self.mock_execute_shell)
        setattr(self.util, 'log', self.mock_log)

    def test_dry_run(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(
            stdout=' M util/util.py'
        )
        self.util.dry_run = True
        self.util.check_repository_cleanliness()

    def test_clean(self) -> None:
        self.mock_execute_shell.return_error = MagicMock(stdout='')
        self.util.check_repository_cleanliness()

    def test_git_error(self) -> None:
        error = subprocess.CalledProcessError(1, 'git')
        self.mock_execute_shell.side_effect = error
        with self.assertRaises(RuntimeError):
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
            command: list[str],
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
            command: list[str],
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


class TestResetChanges(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.mock_execute_shell = MagicMock()
        setattr(self.util, 'execute_shell', self.mock_execute_shell)

    def test_reset_changes(self) -> None:
        self.util.reset_changes()
        checkout = self.mock_execute_shell.mock_calls[0]
        self.assertIn('checkout', checkout[1][0])
        self.assertIn('.', checkout[1][0])


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


class TestCompareVersions(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()

    def test_ints(self) -> None:
        self.assertFalse(self.util.compare_versions('a10', 'a12'))
        self.assertFalse(self.util.compare_versions('10a', '12a'))

    def test_regex(self) -> None:
        tests: dict[str, list[str]] = {
            '12': ['11', '10', '9', '1'],
            '3.11': ['3.10', '3.9', '3.0'],
            '1.21': ['1.19', '1.2'],
            '18-slim': ['16-slim', '15-slim'],
            '3.11-slim-bookworm': ['3.10-slim-bookworm', '3.9-slim-bookworm'],
        }
        for newest, olders in tests.items():
            for older in olders:
                self.assertTrue(
                    self.util.compare_versions(older, newest),
                    '%s->%s' % (older, newest),
                )
                self.assertFalse(
                    self.util.compare_versions(newest, older),
                    '%s->%s' % (newest, older),
                )
                self.assertFalse(self.util.compare_versions(newest, newest), newest)

    def test_not_upgradable(self) -> None:
        tests: list[tuple[str, str]] = [
            ('18', '18.14'),
            ('18', '18.14.2'),
            ('18-alpine', '19-debian'),
            ('3.11-slim-bookworm', 'alpine3.18'),
        ]
        for older, newer in tests:
            self.assertFalse(
                self.util.compare_versions(older, newer),
                '%s->%s' % (older, newer),
            )


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

    def test_semver_range(self) -> None:
        result = self.util.check_major_version_update(
            'sinon', '~13.0.0', '~14.0.0'
        )
        self.assertTrue(result)
        result = self.util.check_major_version_update(
            'sinon', '^13.0.0', '^14.0.0'
        )
        self.assertTrue(result)
        result = self.util.check_major_version_update(
            'sinon', '^13.0.0', '^13.1.0'
        )
        self.assertFalse(result)


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

    def test_ignore_exit_code(self) -> None:
        command = ['ls', '/asdf']
        with self.assertRaises(subprocess.CalledProcessError):
            self.util.execute_shell(command, True)
        result = self.util.execute_shell(command, True, ignore_exit_code=True)
        self.assertIn('ls', result.stderr)

    def test_execute_shell(self) -> None:
        command = ['ls']
        path = Path('/')
        result = self.util.execute_shell(command, True, cwd=path)
        self.assertIn('etc', result.stdout)
        self.assertIn('home', result.stdout)
        self.assertIn('var', result.stdout)


class TestWarn(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.original_env = os.getenv('NO_COLOR', None)

    def tearDown(self) -> None:
        if self.original_env is not None:
            os.environ['NO_COLOR'] = self.original_env  # pragma: no cover
        elif 'NO_COLOR' in os.environ:
            del os.environ['NO_COLOR']

    def test_warn(self) -> None:
        if 'NO_COLOR' in os.environ:
            del os.environ['NO_COLOR']  # pragma: no cover
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.util.warn('asdf')
            self.assertIn('asdf', mock_out.getvalue())
            self.assertNotEqual(mock_out.getvalue(), 'asdf\n')

    def test_warn_no_color(self) -> None:
        os.environ['NO_COLOR'] = 'true'
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.util.warn('asdf')
            self.assertEqual(mock_out.getvalue(), 'asdf\n')


class TestLog(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()

    def test_log(self) -> None:
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.util.log('asdf')
            self.assertEqual(mock_out.getvalue(), 'asdf\n')
