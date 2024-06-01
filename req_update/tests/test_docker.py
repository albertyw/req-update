from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from unittest.mock import MagicMock

from req_update import docker, util


class BaseTest(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.docker = docker.Docker(u)
        self.docker.util.dry_run = False
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.tempdir.name)
        self.docker.util.execute_shell(['git', 'init'], False)

        self.lines = ['FROM debian:10', 'RUN echo']
        self.update_file = self.add_update_file('Dockerfile', '\n'.join(self.lines))

        self.mock_urlopen = MagicMock()
        self.original_urlopen = docker.request.urlopen  # type:ignore
        setattr(docker.request, 'urlopen', self.mock_urlopen)  # type:ignore
        self.mock_commit = MagicMock()
        setattr(self.docker.util, 'commit_dependency_update', self.mock_commit)

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        os.chdir(self.original_cwd)
        setattr(docker.request, 'urlopen', self.original_urlopen)  # type:ignore

    def add_update_file(self, relative_path: str, contents: str) -> Path:
        absolute_path = Path(os.getcwd()) / relative_path
        absolute_path.touch()
        with open(absolute_path, 'w') as handle:
            handle.write(contents)
        self.docker.util.execute_shell(['git', 'add', '.'], False)
        return absolute_path


class TestCheckApplicable(BaseTest):
    def setUp(self) -> None:
        super().setUp()
        self.mock_log = MagicMock()
        setattr(self.docker.util, 'log', self.mock_log)
        self.mock_warn = MagicMock()
        setattr(self.docker.util, 'warn', self.mock_warn)

    def test_check(self) -> None:
        command = ['git', 'rm', '--force', str(self.update_file)]
        self.docker.util.execute_shell(command, False)
        self.assertFalse(self.docker.check_applicable())
        self.add_update_file('Dockerfile', '')
        self.assertTrue(self.docker.check_applicable())
        os.chdir('/')
        self.assertFalse(self.docker.check_applicable())


class TestUpdateDependencies(BaseTest):
    def test_update(self) -> None:
        self.mock_urlopen().status = 200
        self.mock_urlopen().read.return_value = json.dumps(
            {'results': [{'name': '12'}]},
        )
        self.docker.update_dependencies()
        lines = self.docker.read_update_file(self.update_file)
        self.assertEqual(lines, ['FROM debian:12', 'RUN echo'])
        self.assertEqual(len(self.mock_commit.call_args_list), 1)
        self.assertEqual(
            self.mock_commit.call_args_list[0][0],
            ('Docker', 'debian', '12'),
        )

    def test_no_update(self) -> None:
        self.mock_urlopen().status = 200
        self.mock_urlopen().read.return_value = json.dumps(
            {'results': [{'name': '10'}]},
        )
        self.docker.update_dependencies()
        lines = self.docker.read_update_file(self.update_file)
        self.assertEqual(lines, ['FROM debian:10', 'RUN echo'])

    def test_multiple_update(self) -> None:
        with open(self.update_file, 'w') as handle:
            handle.write('FROM debian:10\nFROM debian:11')
        self.mock_urlopen().status = 200
        self.mock_urlopen().read.return_value = json.dumps(
            {'results': [{'name': '12'}]},
        )
        self.docker.update_dependencies()
        lines = self.docker.read_update_file(self.update_file)
        self.assertEqual(lines, ['FROM debian:12', 'FROM debian:12'])
        self.assertEqual(len(self.mock_commit.call_args_list), 2)
        self.assertEqual(
            self.mock_commit.call_args_list[0][0],
            ('Docker', 'debian', '12'),
        )
        self.assertEqual(
            self.mock_commit.call_args_list[1][0],
            ('Docker', 'debian', '12'),
        )


class TestReadDockerfile(BaseTest):
    def test_read(self) -> None:
        lines = self.docker.read_update_file(self.update_file)
        self.assertEqual(self.lines, lines)


class TestAttemptUpdateImage(BaseTest):
    def setUp(self) -> None:
        super().setUp()
        self.test_line = 'FROM debian:10  # comment'
        self.mock_find_updated_version = MagicMock()
        setattr(self.docker, 'find_updated_version', self.mock_find_updated_version)

    def test_discards_other(self) -> None:
        new_line, dependency, version = self.docker.attempt_update_image('RUN echo')
        self.assertEqual(new_line, 'RUN echo')
        self.assertEqual(dependency, '')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_find_updated_version.called)

    def test_identifies_image(self) -> None:
        new_line, dependency, version = self.docker.attempt_update_image('FROM debian')
        self.assertEqual(new_line, 'FROM debian')
        self.assertEqual(dependency, 'debian')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_find_updated_version.called)

    def test_identifies_version(self) -> None:
        self.mock_find_updated_version.return_value = '12'
        new_line, dependency, version = self.docker.attempt_update_image(self.test_line)
        self.assertEqual(new_line, 'FROM debian:12  # comment')
        self.assertEqual(dependency, 'debian')
        self.assertTrue(self.mock_find_updated_version.called)
        self.assertEqual(version, '12')


class TestFindUpdatedVersion(BaseTest):
    def setUp(self) -> None:
        super().setUp()
        self.mock_warn = MagicMock()
        setattr(self.docker.util, 'warn', self.mock_warn)

    def test_updates(self) -> None:
        self.mock_urlopen().status = 200
        self.mock_urlopen().read.return_value = json.dumps(
            {'results': [{'name': '12'}]},
        )
        version = self.docker.find_updated_version('debian', '10')
        self.assertEqual(version, '12')
        self.assertIn('library/debian', self.mock_urlopen.call_args[0][0])
        self.assertTrue(self.mock_urlopen().read.called)

    def test_warns_on_error(self) -> None:
        self.mock_urlopen().status = 404
        version = self.docker.find_updated_version('debian', '10')
        self.assertEqual(version, '')
        self.assertIn('library/debian', self.mock_urlopen.call_args[0][0])
        self.assertFalse(self.mock_urlopen().read.called)
        self.assertTrue(self.mock_warn.called)

    def test_warns_on_exception(self) -> None:
        self.mock_urlopen.side_effect = HTTPError('url', 404, 'msg', None, None) # type:ignore
        version = self.docker.find_updated_version('debian', '10')
        self.assertEqual(version, '')
        self.assertIn('library/debian', self.mock_urlopen.call_args[0][0])
        self.assertTrue(self.mock_warn.called)

    def test_namespaced_library(self) -> None:
        self.mock_urlopen().status = 404
        version = self.docker.find_updated_version('albertyw/ssh-client', '10')
        self.assertEqual(version, '')
        self.assertIn('albertyw/ssh-client', self.mock_urlopen.call_args[0][0])
        self.assertFalse(self.mock_urlopen().read.called)
        self.assertTrue(self.mock_warn.called)

    def test_skips_latest(self) -> None:
        version = self.docker.find_updated_version('debian', 'latest')
        self.assertEqual(version, '')


class TestCommitDockerfile(BaseTest):
    def setUp(self) -> None:
        super().setUp()
        self.mock_commit_dependency_update = MagicMock()
        setattr(
            self.docker.util,
            'commit_dependency_update',
            self.mock_commit_dependency_update,
        )

    def test_commit(self) -> None:
        lines = ['asdf', 'qwer']
        self.docker.commit_dockerfile(self.update_file, lines, 'debian', '12')
        with open(self.update_file, 'r') as handle:
            data = handle.read()
            self.assertEqual(data, 'asdf\nqwer')
        self.assertEqual(self.docker.read_update_file(self.update_file), lines)
        self.assertTrue(self.mock_commit_dependency_update.called)
