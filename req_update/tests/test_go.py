from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from req_update import go


class TestCheckApplicable(unittest.TestCase):
    def setUp(self) -> None:
        self.go = go.Go()
        self.mock_execute_shell = MagicMock()
        setattr(self.go.util, "execute_shell", self.mock_execute_shell)

    def test(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.go.check_applicable()


class TestUpdateInstallDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.go = go.Go()

    def test(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.go.update_install_dependencies()
