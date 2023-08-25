from __future__ import annotations
import unittest

from req_update import docker


class TestCheckApplicable(unittest.TestCase):
    def test_check(self) -> None:
        self.assertFalse(docker.Docker().check_applicable())
