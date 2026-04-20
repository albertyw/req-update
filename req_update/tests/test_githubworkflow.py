from __future__ import annotations
import unittest
from unittest.mock import MagicMock

from req_update import githubworkflow, util


class TestUpdateFile(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.githubworkflow = githubworkflow.GithubWorkflow(u)

    def test_matches_yml(self) -> None:
        self.assertTrue(
            self.githubworkflow.UPDATE_FILE.match('.github/workflows/ci.yml'),
        )

    def test_matches_yaml(self) -> None:
        self.assertTrue(
            self.githubworkflow.UPDATE_FILE.match('.github/workflows/ci.yaml'),
        )

    def test_rejects_other(self) -> None:
        self.assertFalse(self.githubworkflow.UPDATE_FILE.match('Dockerfile'))


class TestAttemptUpdateImage(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.githubworkflow = githubworkflow.GithubWorkflow(u)
        self.mock_find_updated_version = MagicMock()
        setattr(
            self.githubworkflow,
            'find_updated_version',
            self.mock_find_updated_version,
        )

    def test_inline_uses(self) -> None:
        self.mock_find_updated_version.return_value = 'v5'
        line = '      - uses: actions/checkout@v4'
        new_line, dependency, version = self.githubworkflow.attempt_update_image(line)
        self.assertEqual(new_line, '      - uses: actions/checkout@v5')
        self.assertEqual(dependency, 'actions/checkout')
        self.assertEqual(version, 'v5')

    def test_nested_uses(self) -> None:
        self.mock_find_updated_version.return_value = 'v5'
        line = '        uses: actions/checkout@v4'
        new_line, dependency, version = self.githubworkflow.attempt_update_image(line)
        self.assertEqual(new_line, '        uses: actions/checkout@v5')
        self.assertEqual(dependency, 'actions/checkout')
        self.assertEqual(version, 'v5')

    def test_discards_other(self) -> None:
        line = '      - run: pnpm install'
        new_line, dependency, version = self.githubworkflow.attempt_update_image(line)
        self.assertEqual(new_line, line)
        self.assertEqual(dependency, '')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_find_updated_version.called)


class TestFindUpdatedVersion(unittest.TestCase):
    def setUp(self) -> None:
        u = util.Util()
        self.githubworkflow = githubworkflow.GithubWorkflow(u)

        self.mock_request = MagicMock()
        setattr(u, 'cached_request', self.mock_request)

        self.mock_warn = MagicMock()
        setattr(self.githubworkflow.util, 'warn', self.mock_warn)

    def test_find_updated_version(self) -> None:
        self.mock_request.return_value = [{"ref": "refs/tags/2"}]
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '2')
        self.assertIn('albertyw/git-browse', self.mock_request.call_args[0][0])
        self.assertFalse(self.mock_warn.called)

    def test_http_error(self) -> None:
        http_error = util.HTTPError('url', 404, 'not found', None, None)
        self.mock_request.side_effect = http_error
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '')
        self.assertTrue(self.mock_warn.called)

    def test_malformed_response(self) -> None:
        self.mock_request.return_value = 'malformed json'
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '')
        self.assertTrue(self.mock_warn.called)

    def test_equal_version(self) -> None:
        self.mock_request.return_value = [{"ref": "refs/tags/1"}]
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '1')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_warn.called)

    def test_old_version(self) -> None:
        self.mock_request.return_value = [{"ref": "refs/tags/1"}]
        version = self.githubworkflow.find_updated_version('albertyw/git-browse', '2')
        self.assertEqual(version, '')
        self.assertFalse(self.mock_warn.called)
