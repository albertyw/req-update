from __future__ import annotations
import unittest
from unittest.mock import MagicMock

from req_update import dockercompose, util


class TestAttemptUpdateImage(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.compose = dockercompose.DockerCompose(u)
        self.mock_find_updated_version = MagicMock()
        setattr(self.compose, 'find_updated_version', self.mock_find_updated_version)

    def test_identifies_image(self) -> None:
        self.mock_find_updated_version.return_value = '3.14'
        line = '    image: python:3.10'
        new_line, dependency, version = self.compose.attempt_update_image(line)
        self.assertEqual(new_line, '    image: python:3.14')
        self.assertEqual(dependency, 'python')
        self.assertEqual(version, '3.14')

    def test_identifies_dash_image(self) -> None:
        self.mock_find_updated_version.return_value = '3.14'
        line = '    - image: python:3.10'
        new_line, dependency, version = self.compose.attempt_update_image(line)
        self.assertEqual(new_line, '    - image: python:3.14')
        self.assertEqual(dependency, 'python')
        self.assertEqual(version, '3.14')

    def test_discards_other(self) -> None:
        line = '    ports:'
        new_line, dependency, version = self.compose.attempt_update_image(line)
        self.assertEqual(new_line, line)
        self.assertEqual(dependency, '')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_find_updated_version.called)


class TestUpdateFile(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.compose = dockercompose.DockerCompose(u)

    def test_matches_docker_compose_yml(self) -> None:
        self.assertTrue(self.compose.UPDATE_FILE.match('docker-compose.yml'))

    def test_matches_docker_compose_yaml(self) -> None:
        self.assertTrue(self.compose.UPDATE_FILE.match('docker-compose.yaml'))

    def test_matches_compose_yml(self) -> None:
        self.assertTrue(self.compose.UPDATE_FILE.match('compose.yml'))

    def test_matches_override(self) -> None:
        self.assertTrue(
            self.compose.UPDATE_FILE.match('docker-compose.override.yml'),
        )

    def test_matches_subdir(self) -> None:
        self.assertTrue(
            self.compose.UPDATE_FILE.search('sub/dir/docker-compose.yml'),
        )

    def test_rejects_other(self) -> None:
        self.assertFalse(self.compose.UPDATE_FILE.match('Dockerfile'))
        self.assertFalse(self.compose.UPDATE_FILE.match('.drone.yml'))
        self.assertFalse(self.compose.UPDATE_FILE.match('random.yml'))
