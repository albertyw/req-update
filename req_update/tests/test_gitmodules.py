import subprocess
import unittest
from unittest.mock import MagicMock

from req_update.gitsubmodule import GitSubmodule


MOCK_GITMODULES = """
 fc9ab12365ace68f77cc9ac303bbf239d56601db scripts/git/git-browse (v2.13.4)
 94909552b484d1000d30b6e78a386c911de5bd58 scripts/git/git-reviewers (v0.13.3)
 dc9785bfa7b8e0e0b401ff231fb654aea24491cb scripts/git/req-update (v2.0.5)
"""


class TestCheckApplicable(unittest.TestCase):
    def setUp(self) -> None:
        self.gitsubmodule = GitSubmodule()
        self.mock_execute_shell = MagicMock()
        setattr(
            self.gitsubmodule.util,
            "execute_shell",
            self.mock_execute_shell,
        )

    def test_check_applicable_empty(self) -> None:
        self.mock_execute_shell().stdout = ""
        applicable = self.gitsubmodule.check_applicable()
        self.assertFalse(applicable)

    def test_check_applicable(self) -> None:
        self.mock_execute_shell().stdout = MOCK_GITMODULES
        applicable = self.gitsubmodule.check_applicable()
        self.assertTrue(applicable)

    def test_error(self) -> None:
        error = subprocess.CalledProcessError(1, "asdf")
        self.mock_execute_shell.side_effect = error
        applicable = self.gitsubmodule.check_applicable()
        self.assertFalse(applicable)
