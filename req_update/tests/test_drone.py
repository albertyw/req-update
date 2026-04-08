from __future__ import annotations
import unittest
from unittest.mock import MagicMock

from req_update import drone, util


class TestAttemptUpdateImage(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.drone = drone.Drone(u)
        self.mock_find_updated_version = MagicMock()
        setattr(self.drone, 'find_updated_version', self.mock_find_updated_version)

    def test_identifies_image(self) -> None:
        self.mock_find_updated_version.return_value = '3.14'
        line = '    image: python:3.10'
        new_line, dependency, version = self.drone.attempt_update_image(line)
        self.assertEqual(new_line, '    image: python:3.14')
        self.assertEqual(dependency, 'python')
        self.assertEqual(version, '3.14')

    def test_discards_other(self) -> None:
        line = '    commands:'
        new_line, dependency, version = self.drone.attempt_update_image(line)
        self.assertEqual(new_line, line)
        self.assertEqual(dependency, '')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_find_updated_version.called)
