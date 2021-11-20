from __future__ import annotations
import io
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from req_update import util


class TestCommitDependencyUpdate(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()
        self.mock_log = MagicMock()
        setattr(self.util, 'log', self.mock_log)
        self.mock_execute_shell = MagicMock()
        setattr(self.util, 'execute_shell', self.mock_execute_shell)

    def test_commit_dependency_update(self) -> None:
        self.util.commit_dependency_update('varsnap', '1.2.3')
        self.assertTrue(self.mock_log.called)
        log_value = self.mock_log.mock_calls[0][1]
        self.assertIn('varsnap', log_value[0])
        self.assertIn('1.2.3', log_value[0])
        self.assertTrue(self.mock_execute_shell.called)
        command = self.mock_execute_shell.mock_calls[0][1]
        self.assertIn('varsnap', command[0][3])
        self.assertIn('1.2.3', command[0][3])


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


class TestLog(unittest.TestCase):
    def setUp(self) -> None:
        self.util = util.Util()

    def test_log(self) -> None:
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.util.log('asdf')
            self.assertEqual(mock_out.getvalue(), 'asdf\n')
