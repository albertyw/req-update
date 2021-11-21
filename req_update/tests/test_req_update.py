from __future__ import annotations
import argparse
import copy
import io
import json
import random
import subprocess
import sys
import tempfile
from typing import List
import unittest
from unittest.mock import MagicMock, patch

from req_update import req_update


PIP_OUTDATED = [
    {"name": "varsnap", "version": "1.0.0", "latest_version": "1.2.3"}
]


class TestMain(unittest.TestCase):
    def test_main(self) -> None:
        with patch('req_update.req_update.ReqUpdate') as mock_req_update:
            req_update.main()
            self.assertTrue(mock_req_update().main.called)


class TestReqUpdateMain(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()
        self.mock_execute_shell = MagicMock()
        setattr(self.req_update.util, 'execute_shell', self.mock_execute_shell)

    def test_main(self) -> None:
        mock_get_args = MagicMock()
        setattr(self.req_update, 'get_args', mock_get_args)
        mock_check = MagicMock()
        setattr(self.req_update, 'check_repository_cleanliness', mock_check)
        setattr(self.req_update, 'update_dependencies', MagicMock())
        self.req_update.main()
        self.assertTrue(mock_get_args.called)
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

    def test_push(self) -> None:
        self.assertFalse(self.req_update.util.push)
        args = self.get_args_with_argv([])
        self.assertFalse(args.push)
        args = self.get_args_with_argv(['--push'])
        self.assertTrue(args.push)
        args = self.get_args_with_argv(['-p'])
        self.assertTrue(args.push)
        self.assertTrue(self.req_update.util.push)

    def test_install(self) -> None:
        self.assertFalse(self.req_update.install)
        args = self.get_args_with_argv([])
        self.assertFalse(args.install)
        args = self.get_args_with_argv(['--install'])
        self.assertTrue(args.install)
        args = self.get_args_with_argv(['-i'])
        self.assertTrue(args.install)
        self.assertTrue(self.req_update.install)

    def test_dryrun(self) -> None:
        self.assertTrue(self.req_update.util.dry_run)
        args = self.get_args_with_argv([])
        self.assertFalse(args.dryrun)
        args = self.get_args_with_argv(['--dryrun'])
        self.assertTrue(args.dryrun)
        args = self.get_args_with_argv(['-d'])
        self.assertTrue(args.dryrun)
        self.assertTrue(self.req_update.util.dry_run)

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
        setattr(self.req_update.util, 'execute_shell', self.mock_execute_shell)

    def test_clean(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if 'pip' in command:
                return MagicMock(stdout='pip 20.2.4')
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        self.req_update.check_repository_cleanliness()

    def test_unclean(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(
            stdout=' M req_update/req_update.py'
        )
        with self.assertRaises(RuntimeError):
            self.req_update.check_repository_cleanliness()

    def test_pip_version_parse(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if 'pip' in command:
                return MagicMock(stdout='')
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        with self.assertRaises(RuntimeError):
            self.req_update.check_repository_cleanliness()

    def test_pip_version(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if 'pip' in command:
                return MagicMock(stdout='pip 7.0.0')
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        with self.assertRaises(RuntimeError):
            self.req_update.check_repository_cleanliness()


class TestUpdateDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()
        self.mock_execute_shell = MagicMock()
        setattr(self.req_update.util, 'execute_shell', self.mock_execute_shell)
        self.mock_rollback_branch = MagicMock()
        setattr(
            self.req_update.util, 'rollback_branch', self.mock_rollback_branch
        )
        self.mock_log = MagicMock()
        setattr(self.req_update.util, 'log', self.mock_log)

    def test_update_dependencies_clean(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(stdout='[]')
        updated = self.req_update.update_dependencies()
        self.assertTrue(self.mock_log.called)
        self.assertFalse(updated)

    def test_update_dependencies(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if '--outdated' in command:
                return MagicMock(stdout=json.dumps(PIP_OUTDATED))
            raise ValueError()  # pragma: no cover
        self.mock_execute_shell.side_effect = execute_shell_returns
        mock_commit = MagicMock()
        setattr(self.req_update.util, 'commit_dependency_update', mock_commit)
        updated = self.req_update.update_dependencies()
        self.assertFalse(mock_commit.called)
        self.assertTrue(self.mock_log.called)
        self.assertTrue(self.mock_rollback_branch.called)
        self.assertFalse(updated)

    def test_update_dependencies_commit(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if '--outdated' in command:
                return MagicMock(stdout=json.dumps(PIP_OUTDATED))
            raise ValueError()  # pragma: no cover
        self.mock_execute_shell.side_effect = execute_shell_returns
        mock_write = MagicMock(return_value=True)
        setattr(self.req_update, 'write_dependency_update', mock_write)
        mock_commit = MagicMock()
        setattr(self.req_update.util, 'commit_dependency_update', mock_commit)
        updated = self.req_update.update_dependencies()
        self.assertTrue(mock_write.called)
        self.assertTrue(mock_commit.called)
        self.assertFalse(self.mock_rollback_branch.called)
        self.assertTrue(updated)

    def test_update_dependencies_push(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if '--outdated' in command:
                return MagicMock(stdout=json.dumps(PIP_OUTDATED))
            raise ValueError()  # pragma: no cover
        self.mock_execute_shell.side_effect = execute_shell_returns
        mock_write = MagicMock(return_value=True)
        setattr(self.req_update, 'write_dependency_update', mock_write)
        mock_commit = MagicMock()
        setattr(self.req_update.util, 'commit_dependency_update', mock_commit)
        mock_push = MagicMock()
        setattr(self.req_update.util, 'push_dependency_update', mock_push)
        updated = self.req_update.update_dependencies()
        self.assertTrue(mock_write.called)
        self.assertTrue(mock_commit.called)
        self.assertTrue(mock_push.called)
        self.assertFalse(self.mock_rollback_branch.called)
        self.assertTrue(updated)


class TestGetPipOutdated(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()
        self.mock_execute_shell = MagicMock()
        setattr(self.req_update.util, 'execute_shell', self.mock_execute_shell)

    def test_get_pip_outdated(self) -> None:
        self.mock_execute_shell.return_value = subprocess.CompletedProcess(
            [], 0, stdout=json.dumps(PIP_OUTDATED),
        )
        data = self.req_update.get_pip_outdated()
        self.assertEqual(data, PIP_OUTDATED)

    def test_sorts_packages(self) -> None:
        outdated = [
            copy.deepcopy(PIP_OUTDATED[0]),
            copy.deepcopy(PIP_OUTDATED[0]),
        ]
        outdated[1]['name'] = 'abcd'
        self.mock_execute_shell.return_value = subprocess.CompletedProcess(
            [], 0, stdout=json.dumps(outdated),
        )
        data = self.req_update.get_pip_outdated()
        self.assertEqual(data[0]['name'], 'abcd')
        self.assertEqual(data[1]['name'], 'varsnap')
        self.assertNotEqual(data, outdated)


class TestEditRequirements(unittest.TestCase):
    def setUp(self) -> None:
        self.tempfile = tempfile.NamedTemporaryFile()

    def tearDown(self) -> None:
        self.tempfile.close()

    def test_edit_requirements(self) -> None:
        filename = self.tempfile.name
        with req_update.ReqUpdate.edit_requirements(filename) as lines:
            lines.append('asdf\n')
            lines.append('qwer\n')
        with open(filename, 'r') as handle:
            data = handle.read()
            self.assertEqual(data, 'asdf\nqwer\n')

    def test_edit_requirements_not_found(self) -> None:
        filename = str(random.randint(10**10, 10**11))
        with req_update.ReqUpdate.edit_requirements(filename):
            pass
        with self.assertRaises(FileNotFoundError):
            open(filename, 'r')


class TestWriteDependencyUpdate(unittest.TestCase):
    def setUp(self) -> None:
        self.tempfile = tempfile.NamedTemporaryFile()
        self.original_reqfiles = req_update.REQUIREMENTS_FILES
        req_update.REQUIREMENTS_FILES = [self.tempfile.name]
        self.req_update = req_update.ReqUpdate()

    def tearDown(self) -> None:
        self.tempfile.close()
        req_update.REQUIREMENTS_FILES = self.original_reqfiles

    def test_write_dependency_update_no_comment(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0')
        updated = self.req_update.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.2.3')
        self.assertIn(self.tempfile.name, self.req_update.updated_files)

    def test_write_dependency_update(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0    # qwer')
        updated = self.req_update.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.2.3    # qwer')
        self.assertIn(self.tempfile.name, self.req_update.updated_files)

    def test_write_dependency_update_aligned(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0    # qwer')
        updated = self.req_update.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.2.3  # qwer')
        self.assertIn(self.tempfile.name, self.req_update.updated_files)

    def test_write_dependency_update_no_op(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0    # qwer')
        updated = self.req_update.write_dependency_update('varsnap', '1.0.0')
        self.assertFalse(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.0.0    # qwer')
        self.assertNotIn(self.tempfile.name, self.req_update.updated_files)

    def test_write_dependency_update_post(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0post0    # qwer')
        updated = self.req_update.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.2.3         # qwer')
        self.assertIn(self.tempfile.name, self.req_update.updated_files)


class TestInstallUpdates(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()
        self.mock_log = MagicMock()
        setattr(self.req_update.util, 'log', self.mock_log)
        self.mock_execute_shell = MagicMock()
        setattr(self.req_update.util, 'execute_shell', self.mock_execute_shell)

    def test_install_updates_noop(self) -> None:
        self.req_update.updated_files.add('requirements.txt')
        self.req_update.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 0)
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 0)

    def test_install_updates(self) -> None:
        self.req_update.install = True
        self.req_update.updated_files.add('requirements.txt')
        self.req_update.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 1)
        log_value = self.mock_log.mock_calls[0][1]
        self.assertIn('requirements.txt', log_value[0])
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 1)
        command = self.mock_execute_shell.mock_calls[0][1]
        self.assertEqual('requirements.txt', command[0][3])

    def test_install_multiple_updates(self) -> None:
        self.req_update.install = True
        self.req_update.updated_files.add('requirements-test.txt')
        self.req_update.updated_files.add('requirements.txt')
        self.req_update.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 2)
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 2)
