from __future__ import annotations
import copy
import json
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from req_update import python, util


PIP_OUTDATED = [
    {'name': 'varsnap', 'version': '1.0.0', 'latest_version': '1.2.3'},
]


class TestCheckApplicable(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.python = python.Python(u)
        self.mock_execute_shell = MagicMock()
        setattr(self.python.util, 'execute_shell', self.mock_execute_shell)

    def test_applicable(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(stdout='pip 21.3.1')
        files = self.python.get_update_files()
        self.assertTrue(len(files) > 0)
        applicable = self.python.check_applicable()
        self.assertTrue(applicable)

    def test_pip_error(self) -> None:
        error = subprocess.CalledProcessError(1, 'error')
        self.mock_execute_shell.side_effect = error
        applicable = self.python.check_applicable()
        self.assertFalse(applicable)

    def test_pip_version_parse(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(stdout='')
        applicable = self.python.check_applicable()
        self.assertFalse(applicable)

    def test_pip_version(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(stdout='pip 7.0.0')
        applicable = self.python.check_applicable()
        self.assertFalse(applicable)

    @patch('os.listdir')
    def test_requirements_not_exists(self, listdir: MagicMock) -> None:
        self.mock_execute_shell.return_value = MagicMock(stdout='pip 21.3.1')
        listdir.return_value = []
        applicable = self.python.check_applicable()
        self.assertFalse(applicable)


class TestUpdateDependencies(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.python = python.Python(u)
        self.mock_update = MagicMock()
        setattr(self.python, 'update_dependencies_file', self.mock_update)
        self.mock_install = MagicMock()
        setattr(self.python, 'install_updates', self.mock_install)
        self.mock_log = MagicMock()
        setattr(self.python.util, 'log', self.mock_log)

    def test_updates_made(self) -> None:
        self.mock_update.return_value = True
        updates = self.python.update_dependencies()
        self.assertTrue(updates)
        self.assertTrue(self.mock_install.called)

    def test_no_updates_made(self) -> None:
        self.mock_update.return_value = False
        updates = self.python.update_dependencies()
        self.assertFalse(updates)
        self.assertFalse(self.mock_install.called)


class TestUpdateDependenciesFile(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.python = python.Python(u)
        self.mock_execute_shell = MagicMock()
        setattr(self.python.util, 'execute_shell', self.mock_execute_shell)
        self.mock_log = MagicMock()
        setattr(self.python.util, 'log', self.mock_log)

    def test_update_dependencies_file_clean(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(stdout='[]')
        updated = self.python.update_dependencies_file()
        self.assertFalse(updated)

    def test_update_dependencies_file(self) -> None:
        def execute_shell_returns(
            command: list[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if '--outdated' in command:
                return MagicMock(stdout=json.dumps(PIP_OUTDATED))
            raise ValueError()  # pragma: no cover

        self.mock_execute_shell.side_effect = execute_shell_returns
        mock_commit = MagicMock()
        setattr(self.python.util, 'commit_dependency_update', mock_commit)
        updated = self.python.update_dependencies_file()
        self.assertFalse(mock_commit.called)
        self.assertFalse(updated)

    def test_update_dependencies_file_commit(self) -> None:
        def execute_shell_returns(
            command: list[str],
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
        updated = self.python.update_dependencies_file()
        self.assertTrue(mock_write.called)
        self.assertTrue(mock_commit.called)
        self.assertTrue(updated)


class TestGetPipOutdated(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.python = python.Python(u)
        self.mock_execute_shell = MagicMock()
        setattr(self.python.util, 'execute_shell', self.mock_execute_shell)

    def test_get_pip_outdated(self) -> None:
        self.mock_execute_shell.return_value = subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps(PIP_OUTDATED),
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
            [],
            0,
            stdout=json.dumps(outdated),
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
        with python.Python.edit_requirements(Path(filename), False) as lines:
            lines.append('asdf\n')
            lines.append('qwer\n')
        with open(filename, 'r') as handle:
            data = handle.read()
            self.assertEqual(data, 'asdf\nqwer\n')

    def test_edit_requirements_not_found(self) -> None:
        filename = str(random.randint(10**10, 10**11))
        with python.Python.edit_requirements(Path(filename), False):
            pass
        with self.assertRaises(FileNotFoundError):
            open(filename, 'r')


class TestWriteDependencyUpdate(unittest.TestCase):
    def setUp(self) -> None:
        self.tempfile_requirements = tempfile.NamedTemporaryFile()
        self.original_reqfiles = python.REQUIREMENTS_FILES
        python.REQUIREMENTS_FILES = [Path(self.tempfile_requirements.name)]
        self.tempfile_pyproject = tempfile.NamedTemporaryFile()
        self.original_pyprojectfiles = python.PYPROJECT_FILES
        python.PYPROJECT_FILES = [Path(self.tempfile_pyproject.name)]
        u = util.Util()
        self.python = python.Python(u)
        self.python.util.dry_run = False
        self.mock_get_update_files = MagicMock()
        setattr(self.python, 'get_update_files', self.mock_get_update_files)
        self.mock_get_update_files.return_value = \
            python.REQUIREMENTS_FILES + python.PYPROJECT_FILES

    def tearDown(self) -> None:
        self.tempfile_requirements.close()
        self.tempfile_pyproject.close()
        python.REQUIREMENTS_FILES = self.original_reqfiles
        python.PYPROJECT_FILES = self.original_pyprojectfiles

    def test_write_dependency_update_no_comment(self) -> None:
        with open(self.tempfile_requirements.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0')
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write('    "abcd==0.0.1",\n    "varsnap==1.0.0"')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile_requirements.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip('\n'), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip('\n'), 'varsnap==1.2.3')
        with open(self.tempfile_pyproject.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip("\n"), '    "abcd==0.0.1",')
            self.assertEqual(lines[1].strip("\n"), '    "varsnap==1.2.3",')
        self.assertIn(
            Path(self.tempfile_requirements.name),
            self.python.updated_requirements_files,
        )
        self.assertIn(
            Path(self.tempfile_pyproject.name),
            self.python.updated_pyproject_files,
        )

    def test_write_dependency_update(self) -> None:
        with open(self.tempfile_requirements.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0    # qwer')
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write('    "abcd==0.0.1",\n    "varsnap==1.0.0",    # qwer')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile_requirements.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip('\n'), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip('\n'), 'varsnap==1.2.3      # qwer')
        with open(self.tempfile_pyproject.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip("\n"), '    "abcd==0.0.1",')
            self.assertEqual(
                lines[1].strip("\n"),
                '    "varsnap==1.2.3",         # qwer',
            )
        self.assertIn(
            Path(self.tempfile_requirements.name),
            self.python.updated_requirements_files,
        )
        self.assertIn(
            Path(self.tempfile_pyproject.name),
            self.python.updated_pyproject_files,
        )

    def test_write_dependency_update_aligned(self) -> None:
        with open(self.tempfile_requirements.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0    # qwer')
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write('    "abcd==0.0.1",\n    "varsnap==1.0",    # qwer')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile_requirements.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip('\n'), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip('\n'), 'varsnap==1.2.3      # qwer')
        with open(self.tempfile_pyproject.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip("\n"), '    "abcd==0.0.1",')
            self.assertEqual(
                lines[1].strip("\n"),
                '    "varsnap==1.2.3",         # qwer',
            )
        self.assertIn(
            Path(self.tempfile_requirements.name),
            self.python.updated_requirements_files,
        )
        self.assertIn(
            Path(self.tempfile_pyproject.name),
            self.python.updated_pyproject_files,
        )

    def test_write_dependency_update_no_op(self) -> None:
        with open(self.tempfile_requirements.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0    # qwer')
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write('    "abcd==0.0.1",\n    "varsnap==1.0.0",    # qwer')
        updated = self.python.write_dependency_update('varsnap', '1.0.0')
        self.assertFalse(updated)
        with open(self.tempfile_requirements.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip('\n'), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip('\n'), 'varsnap==1.0.0    # qwer')
        with open(self.tempfile_pyproject.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip("\n"), '    "abcd==0.0.1",')
            self.assertEqual(lines[1].strip("\n"), '    "varsnap==1.0.0",    # qwer')
        self.assertNotIn(
            Path(self.tempfile_requirements.name),
            self.python.updated_requirements_files,
        )
        self.assertNotIn(
            Path(self.tempfile_pyproject.name),
            self.python.updated_pyproject_files,
        )

    def test_write_dependency_update_post(self) -> None:
        with open(self.tempfile_requirements.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0.0post0    # qwer')
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write('    "abcd==0.0.1",\n    "varsnap==1.0.0post0",    # qwer')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile_requirements.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip('\n'), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip('\n'), 'varsnap==1.2.3      # qwer')
        with open(self.tempfile_pyproject.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip("\n"), '    "abcd==0.0.1",')
            self.assertEqual(
                lines[1].strip("\n"),
                '    "varsnap==1.2.3",         # qwer',
            )
        self.assertIn(
            Path(self.tempfile_requirements.name),
            self.python.updated_requirements_files,
        )
        self.assertIn(
            Path(self.tempfile_pyproject.name),
            self.python.updated_pyproject_files,
        )

    def test_add_spacing(self) -> None:
        with open(self.tempfile_requirements.name, 'w') as handle:
            handle.write('abcd==0.0.1\nvarsnap==1.0 # qwer')
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write('    "abcd==0.0.1",\n    "varsnap==1.0", # qwer')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile_requirements.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip('\n'), 'abcd==0.0.1')
            self.assertEqual(lines[1].strip('\n'), 'varsnap==1.2.3      # qwer')
        with open(self.tempfile_pyproject.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip("\n"), '    "abcd==0.0.1",')
            self.assertEqual(
                lines[1].strip("\n"),
                '    "varsnap==1.2.3",         # qwer',
            )

    def test_remove_spacing(self) -> None:
        with open(self.tempfile_requirements.name, 'w') as handle:
            handle.write('a==1.0      # qwer')
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write('"a==1.0",      # qwer')
        updated = self.python.write_dependency_update('a', '2.0')
        self.assertTrue(updated)
        with open(self.tempfile_requirements.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip('\n'), 'a==2.0    # qwer')
        with open(self.tempfile_pyproject.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(
                lines[0].strip("\n"),
                '"a==2.0", # qwer',
            )
        self.assertIn(
            Path(self.tempfile_requirements.name),
            self.python.updated_requirements_files,
        )
        self.assertIn(
            Path(self.tempfile_pyproject.name),
            self.python.updated_pyproject_files,
        )

    def test_no_spacing_on_unmatching_lines(self) -> None:
        with open(self.tempfile_requirements.name, 'w') as handle:
            handle.write('varsnap==1.0 # qwer\n# asdf')
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write('    "varsnap==1.0", # qwer\n    # asdf')
        updated = self.python.write_dependency_update('varsnap', '1.2.3')
        self.assertTrue(updated)
        with open(self.tempfile_requirements.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(lines[0].strip('\n'), 'varsnap==1.2.3      # qwer')
            self.assertEqual(lines[1].strip('\n'), '# asdf')
        with open(self.tempfile_pyproject.name, 'r') as handle:
            lines = handle.readlines()
            self.assertEqual(
                lines[0].strip("\n"),
                '    "varsnap==1.2.3",         # qwer',
            )
            self.assertEqual(lines[1].strip("\n"), '    # asdf')
        self.assertIn(
            Path(self.tempfile_requirements.name),
            self.python.updated_requirements_files,
        )
        self.assertIn(
            Path(self.tempfile_pyproject.name),
            self.python.updated_pyproject_files,
        )



class TestInstallUpdates(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.python = python.Python(u)
        self.mock_log = MagicMock()
        setattr(self.python.util, 'log', self.mock_log)
        self.mock_execute_shell = MagicMock()
        setattr(self.python.util, 'execute_shell', self.mock_execute_shell)
        self.tempfile_pyproject = tempfile.NamedTemporaryFile()
        self.original_pyprojectfiles = python.PYPROJECT_FILES
        python.PYPROJECT_FILES = [Path(self.tempfile_pyproject.name)]

    def tearDown(self) -> None:
        self.tempfile_pyproject.close()
        python.PYPROJECT_FILES = self.original_pyprojectfiles

    def test_install_no_updates(self) -> None:
        self.python.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 0)
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 0)

    def test_install_requirements_updates(self) -> None:
        self.python.updated_requirements_files.add(Path('requirements.txt'))
        self.python.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 1)
        log_value = self.mock_log.mock_calls[0][1]
        self.assertIn('requirements.txt', log_value[0])
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 1)
        command = self.mock_execute_shell.mock_calls[0][1]
        self.assertEqual('requirements.txt', command[0][3])

    def test_install_multiple_requirements_updates(self) -> None:
        self.python.updated_requirements_files.add(Path('requirements-test.txt'))
        self.python.updated_requirements_files.add(Path('requirements.txt'))
        self.python.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 2)
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 2)

    def test_install_pyproject_updates(self) -> None:
        pyproject = (
            '[project]\n'
            'dependencies = [\n'
            '    "varsnap==1.0.0",\n'
            ']'
        )
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write(pyproject)
        self.python.updated_pyproject_files.add(Path(self.tempfile_pyproject.name))
        self.python.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 1)
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 1)
        self.assertEqual(self.mock_execute_shell.mock_calls[0][1][0][3], '.')

    def test_install_pyproject_optional_updates(self) -> None:
        pyproject = (
            '[project.optional-dependencies]\n'
            'test = [\n'
            '    "varsnap==1.0.0",\n'
           ']'
       )
        with open(self.tempfile_pyproject.name, 'w') as handle:
            handle.write(pyproject)
        self.python.updated_pyproject_files.add(Path(self.tempfile_pyproject.name))
        self.python.install_updates()
        self.assertEqual(len(self.mock_log.mock_calls), 1)
        self.assertEqual(len(self.mock_execute_shell.mock_calls), 2)
        self.assertEqual(self.mock_execute_shell.mock_calls[0][1][0][3], '.')
        self.assertEqual(self.mock_execute_shell.mock_calls[1][1][0][3], '.[test]')


class TestGetCommentAlignment(unittest.TestCase):
    def test_get_alignment_simple(self) -> None:
        alignment = python.Python.get_comment_alignment([
            'abcd==0.0.1    # qwer',
        ], python.REQUIREMENTS)
        self.assertEqual(alignment, 20)

    def test_get_alignment_long_comment(self) -> None:
        alignment = python.Python.get_comment_alignment([
            'qwer==0.0.1                 # qwer',
        ], python.REQUIREMENTS)
        self.assertEqual(alignment, 20)

    def test_get_alignment_no_inline_comment(self) -> None:
        alignment = python.Python.get_comment_alignment([
            'abcd==0.0.1',
            '# asdf',
        ], python.REQUIREMENTS)
        self.assertEqual(alignment, 0)

    def test_get_alignment_indentation(self) -> None:
        alignment = python.Python.get_comment_alignment([
            '    "abcdefghijk==0.0.1",  # asdf',
        ], python.PYPROJECT)
        self.assertEqual(alignment, 30)

    def test_get_alignment_max(self) -> None:
        alignment = python.Python.get_comment_alignment([
            'a==1.0.0  # asdf',
        ], python.REQUIREMENTS)
        self.assertEqual(alignment, 10)
        alignment = python.Python.get_comment_alignment([
            'a==1.0.0  # asdf',
            'qwer==1.0.0  # qwer',
        ], python.REQUIREMENTS)
        self.assertEqual(alignment, 20)
