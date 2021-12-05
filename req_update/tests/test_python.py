from __future__ import annotations
import copy
import json
import random
import subprocess
import tempfile
from typing import List
import unittest
from unittest.mock import MagicMock

from req_update import python


PIP_OUTDATED = [
    {"name": "varsnap", "version": "1.0.0", "latest_version": "1.2.3"}
]


class TestCheckApplicable(unittest.TestCase):
    def setUp(self) -> None:
        self.python = python.Python()
        self.mock_execute_shell = MagicMock()
        setattr(self.python.util, 'execute_shell', self.mock_execute_shell)

    def test_pip_version_parse(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
            suppress_output: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if 'pip' in command:
                return MagicMock(stdout='')
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        applicable = self.python.check_applicable()
        self.assertFalse(applicable)

    def test_pip_version(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
            suppress_output: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if 'pip' in command:
                return MagicMock(stdout='pip 7.0.0')
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        applicable = self.python.check_applicable()
        self.assertFalse(applicable)


class TestUpdateInstallDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.python = python.Python()
        self.mock_update = MagicMock()
        setattr(self.python, 'update_dependencies', self.mock_update)
        self.mock_install = MagicMock()
        setattr(self.python, 'install_updates', self.mock_install)
        self.mock_log = MagicMock()
        setattr(self.python.util, 'log', self.mock_log)

    def test_updates_made(self) -> None:
        self.mock_update.return_value = True
        updates = self.python.update_install_dependencies()
        self.assertTrue(updates)
        self.assertTrue(self.mock_install.called)

    def test_no_updates_made(self) -> None:
        self.mock_update.return_value = False
        updates = self.python.update_install_dependencies()
        self.assertFalse(updates)
        self.assertFalse(self.mock_install.called)


class TestUpdateDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.python = python.Python()
        self.mock_execute_shell = MagicMock()
        setattr(self.python.util, 'execute_shell', self.mock_execute_shell)
        self.mock_log = MagicMock()
        setattr(self.python.util, 'log', self.mock_log)

    def test_update_dependencies_clean(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(stdout='[]')
        updated = self.python.update_dependencies()
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
        setattr(self.python.util, 'commit_dependency_update', mock_commit)
        updated = self.python.update_dependencies()
        self.assertFalse(mock_commit.called)
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
        setattr(self.python, 'write_dependency_update', mock_write)
        mock_commit = MagicMock()
        setattr(self.python.util, 'commit_dependency_update', mock_commit)
        updated = self.python.update_dependencies()
        self.assertTrue(mock_write.called)
        self.assertTrue(mock_commit.called)
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
        setattr(self.python, 'write_dependency_update', mock_write)
        mock_commit = MagicMock()
        setattr(self.python.util, 'commit_dependency_update', mock_commit)
        mock_push = MagicMock()
        setattr(self.python.util, 'push_dependency_update', mock_push)
        updated = self.python.update_dependencies()
        self.assertTrue(mock_write.called)
        self.assertTrue(mock_commit.called)
        self.assertTrue(mock_push.called)
        self.assertTrue(updated)


class TestGetPipOutdated(unittest.TestCase):
    def setUp(self) -> None:
        self.python = python.Python()
        self.mock_execute_shell = MagicMock()
        setattr(self.python.util, 'execute_shell', self.mock_execute_shell)

    def test_get_pip_outdated(self) -> None:
        self.mock_execute_shell.return_value = subprocess.CompletedProcess(
            [], 0, stdout=json.dumps(PIP_OUTDATED),
        )
        data = self.python.get_pip_outdated()
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
        data = self.python.get_pip_outdated()
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
        with python.Python.edit_requirements(filename) as lines:
            lines.append('asdf\n')
            lines.append('qwer\n')
        with open(filename, 'r') as handle:
            data = handle.read()
            self.assertEqual(data, 'asdf\nqwer\n')

    def test_edit_requirements_not_found(self) -> None:
        filename = str(random.randint(10**10, 10**11))
        with python.Python.edit_requirements(filename):
            pass
        with self.assertRaises(FileNotFoundError):
            open(filename, 'r')


class TestWriteDependencyUpdate(unittest.TestCase):
    def setUp(self) -> None:
        self.tempfile = tempfile.NamedTemporaryFile()
        self.original_reqfiles = python.REQUIREMENTS_FILES
        python.REQUIREMENTS_FILES = [self.tempfile.name]
        self.python = python.Python()

    def tearDown(self) -> None:
        self.tempfile.close()
        python.REQUIREMENTS_FILES = self.original_reqfiles

    def test_write_dependency_update_no_comment(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.2.3')
        self.assertIn(self.tempfile.name, self.python.updated_files)

    def test_write_dependency_update(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0    # qwer')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.2.3    # qwer')
        self.assertIn(self.tempfile.name, self.python.updated_files)

    def test_write_dependency_update_aligned(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0    # qwer')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.2.3  # qwer')
        self.assertIn(self.tempfile.name, self.python.updated_files)

    def test_write_dependency_update_no_op(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0    # qwer')
        updated = self.python.write_dependency_update('varsnap', '1.0.0')
        self.assertFalse(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.0.0    # qwer')
        self.assertNotIn(self.tempfile.name, self.python.updated_files)

    def test_write_dependency_update_post(self) -> None:
        with open(self.tempfile.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0post0    # qwer')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip(), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip(), 'varsnap==1.2.3         # qwer')
        self.assertIn(self.tempfile.name, self.python.updated_files)


class TestInstallUpdates(unittest.TestCase):
    def setUp(self) -> None:
        self.python = python.Python()
        self.mock_log = MagicMock()
        setattr(self.python.util, 'log', self.mock_log)
        self.mock_execute_shell = MagicMock()
        setattr(self.python.util, 'execute_shell', self.mock_execute_shell)

    def test_install_updates_noop(self) -> None:
        self.python.updated_files.add('requirements.txt')
        self.python.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 0)
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 0)

    def test_install_updates(self) -> None:
        self.python.install = True
        self.python.updated_files.add('requirements.txt')
        self.python.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 1)
        log_value = self.mock_log.mock_calls[0][1]
        self.assertIn('requirements.txt', log_value[0])
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 1)
        command = self.mock_execute_shell.mock_calls[0][1]
        self.assertEqual('requirements.txt', command[0][3])

    def test_install_multiple_updates(self) -> None:
        self.python.install = True
        self.python.updated_files.add('requirements-test.txt')
        self.python.updated_files.add('requirements.txt')
        self.python.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 2)
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 2)
