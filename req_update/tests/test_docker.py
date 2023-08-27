from __future__ import annotations
import os
import tempfile
import unittest
from unittest.mock import MagicMock

from req_update import docker


class BaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.docker = docker.Docker()
        self.lines = ['FROM debian:10', 'RUN echo']
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.tempdir.name)
        with open('Dockerfile', 'w') as handle:
            handle.write('\n'.join(self.lines))
        self.mock_warn = MagicMock()
        setattr(self.docker.util, 'warn', self.mock_warn)

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        os.chdir(self.original_cwd)


class TestCheckApplicable(BaseTest):
    def test_check(self) -> None:
        self.assertTrue(self.docker.check_applicable())
        os.chdir('/')
        self.assertFalse(self.docker.check_applicable())


class TestUpdateDependencies(BaseTest):
    def test_update(self) -> None:
        self.docker.update_dependencies()


class TestReadDockerfile(BaseTest):
    def test_read(self) -> None:
        lines = self.docker.read_dockerfile()
        self.assertEqual(self.lines, lines)


class TestAttemptUpdateImage(BaseTest):
    def test_attempt(self) -> None:
        self.docker.attempt_update_image('')


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
        self.docker.commit_dockerfile(lines, 'debian', '12')
        with open('Dockerfile', 'r') as handle:
            data = handle.read()
            self.assertEqual(data, 'asdf\nqwer')
        self.assertEqual(self.docker.read_dockerfile(), lines)
        self.assertTrue(self.mock_commit_dependency_update.called)
