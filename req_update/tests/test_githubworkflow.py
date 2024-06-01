from __future__ import annotations
import json
import unittest
from urllib.error import HTTPError
from unittest.mock import MagicMock

from req_update import githubworkflow, util


class TestFindUpdatedVersion(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.githubworkflow = githubworkflow.GithubWorkflow(u)

        self.mock_urlopen = MagicMock()
        self.original_urlopen = githubworkflow.urlopen  # type: ignore
        setattr(githubworkflow, 'urlopen', self.mock_urlopen)

        self.mock_warn = MagicMock()
        setattr(self.githubworkflow.util, 'warn', self.mock_warn)

    def tearDown(self) -> None:
        setattr(githubworkflow, 'urlopen', self.original_urlopen)

    def test_find_updated_version(self) -> None:
        self.mock_urlopen().status = 200
        self.mock_urlopen().read.return_value = json.dumps(
            [{"ref": "refs/tags/2"}],
        )
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '2')
        self.assertIn('albertyw/git-browse', self.mock_urlopen.call_args[0][0].full_url)
        self.assertTrue(self.mock_urlopen().read.called)
        self.assertFalse(self.mock_warn.called)

    def test_http_error(self) -> None:
        self.mock_urlopen.side_effect = HTTPError('url', 404, 'not found', None, None)  # type: ignore
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '')
        self.assertTrue(self.mock_warn.called)

    def test_request_error(self) -> None:
        self.mock_urlopen().status = 404
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '')
        self.assertTrue(self.mock_warn.called)

    def test_malformed_response(self) -> None:
        self.mock_urlopen().status = 200
        self.mock_urlopen().read.return_value = 'malformed json'
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '')
        self.assertTrue(self.mock_warn.called)

    def test_no_tags(self) -> None:
        self.mock_urlopen().status = 200
        self.mock_urlopen().read.return_value = json.dumps([])
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_warn.called)

    def test_equal_version(self) -> None:
        self.mock_urlopen().status = 200
        self.mock_urlopen().read.return_value = json.dumps(
            [{"ref": "refs/tags/1"}],
        )
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_warn.called)

    def test_old_version(self) -> None:
        self.mock_urlopen().status = 200
        self.mock_urlopen().read.return_value = json.dumps(
            [{"ref": "refs/tags/1"}],
        )
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '2')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_warn.called)
