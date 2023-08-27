import datetime
from pathlib import Path
import subprocess
from typing import Any, Dict, List
import unittest
from unittest.mock import MagicMock

from req_update.gitsubmodule import GitSubmodule, Submodule, VersionInfo


MOCK_GITMODULES = """
 fc9ab12365ace68f77cc9ac303bbf239d56601db scripts/git/git-browse (v2.13.4)
 94909552b484d1000d30b6e78a386c911de5bd58 scripts/git/git-reviewers (v0.13.3)
 dc9785bfa7b8e0e0b401ff231fb654aea24491cb scripts/git/req-update (v2.0.5)
"""

MOCK_COMMIT_DATA = """
fc9ab12365ace68f77cc9ac303bbf239d56601db
2022-07-30T15:30:22-07:00
"""
MOCK_COMMIT_TAG = 'v2.13.4'
MOCK_COMMIT_HASH = 'fc9ab12365ace68f77cc9ac303bbf239d56601db'
MOCK_TZINFO = datetime.timezone(-datetime.timedelta(hours=7))
MOCK_COMMIT_DATE = datetime.datetime(2022, 7, 30, 15, 30, 22, 0, MOCK_TZINFO)


class TestCheckApplicable(unittest.TestCase):
    def setUp(self) -> None:
        self.gitsubmodule = GitSubmodule()
        self.mock_execute_shell = MagicMock()
        setattr(
            self.gitsubmodule.util,
            'execute_shell',
            self.mock_execute_shell,
        )

    def test_check_applicable_empty(self) -> None:
        self.mock_execute_shell().stdout = ''
        applicable = self.gitsubmodule.check_applicable()
        self.assertFalse(applicable)

    def test_check_applicable(self) -> None:
        self.mock_execute_shell().stdout = MOCK_GITMODULES
        applicable = self.gitsubmodule.check_applicable()
        self.assertTrue(applicable)

    def test_error(self) -> None:
        error = subprocess.CalledProcessError(1, 'asdf')
        self.mock_execute_shell.side_effect = error
        applicable = self.gitsubmodule.check_applicable()
        self.assertFalse(applicable)


class TestUpdateDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.gitsubmodule = GitSubmodule()
        self.submodule = Submodule(Path('/'))
        self.mock_get_submodule_info = MagicMock()
        setattr(
            self.gitsubmodule,
            'get_submodule_info',
            self.mock_get_submodule_info,
        )
        self.mock_annotate_submodule = MagicMock()
        setattr(
            self.gitsubmodule,
            'annotate_submodule',
            self.mock_annotate_submodule,
        )
        self.mock_update_submodule = MagicMock()
        setattr(
            self.gitsubmodule, 'update_submodule', self.mock_update_submodule
        )
        self.mock_check_cleanliness = MagicMock()
        setattr(
            self.gitsubmodule.util,
            'check_repository_cleanliness',
            self.mock_check_cleanliness,
        )
        self.mock_commit = MagicMock()
        setattr(
            self.gitsubmodule.util,
            'commit_dependency_update',
            self.mock_commit,
        )
        self.mock_push = MagicMock()
        setattr(
            self.gitsubmodule.util, 'push_dependency_update', self.mock_push
        )
        self.mock_log = MagicMock()
        setattr(self.gitsubmodule.util, 'log', self.mock_log)

    def test_no_submodule(self) -> None:
        self.mock_get_submodule_info.return_value = []
        updates = self.gitsubmodule.update_dependencies()
        self.assertFalse(self.mock_annotate_submodule.called)
        self.assertFalse(self.mock_commit.called)
        self.assertFalse(self.mock_push.called)
        self.assertFalse(updates)

    def test_no_version(self) -> None:
        self.mock_get_submodule_info.return_value = [self.submodule]
        self.mock_update_submodule.return_value = ''
        updates = self.gitsubmodule.update_dependencies()
        self.assertFalse(self.mock_commit.called)
        self.assertFalse(self.mock_push.called)
        self.assertFalse(updates)

    def test_clean(self) -> None:
        self.mock_get_submodule_info.return_value = [self.submodule]
        self.mock_update_submodule.return_value = 'v1.2.3'
        updates = self.gitsubmodule.update_dependencies()
        self.assertFalse(self.mock_commit.called)
        self.assertFalse(self.mock_push.called)
        self.assertFalse(updates)

    def test_updates(self) -> None:
        self.mock_get_submodule_info.return_value = [self.submodule]
        self.mock_update_submodule.return_value = 'v1.2.3'
        self.mock_check_cleanliness.side_effect = RuntimeError('asdf')
        updates = self.gitsubmodule.update_dependencies()
        self.assertTrue(self.mock_commit.called)
        self.assertTrue(self.mock_push.called)
        self.assertTrue(updates)


class TestGetSubmoduleInfo(unittest.TestCase):
    def setUp(self) -> None:
        self.gitsubmodule = GitSubmodule()
        self.mock_execute_shell = MagicMock()
        setattr(
            self.gitsubmodule.util,
            'execute_shell',
            self.mock_execute_shell,
        )

    def test_get_submodule_info(self) -> None:
        self.mock_execute_shell().stdout = MOCK_GITMODULES
        submodules = self.gitsubmodule.get_submodule_info()
        self.assertEqual(len(submodules), 3)
        for submodule in submodules:
            self.assertIn('scripts/git', str(submodule.path))


class TestAnnotateSubmodule(unittest.TestCase):
    def setUp(self) -> None:
        self.gitsubmodule = GitSubmodule()
        self.mock_execute_shell = MagicMock()
        setattr(
            self.gitsubmodule.util,
            'execute_shell',
            self.mock_execute_shell,
        )
        self.submodule = Submodule(Path('./git-browse'))

    def test_get_info(self) -> None:
        def execute_shell_returns(
            *args: List[Any], **kwargs: Dict[str, Any]
        ) -> MagicMock:
            stdout = None
            if args[0] == ['git', 'fetch', '-tp']:
                stdout = ''
            if args[0] == [
                'git',
                'show',
                'origin',
                '--date=iso-strict',
                '--quiet',
                '--format=%H%n%cd',
            ]:
                stdout = MOCK_COMMIT_DATA
            if args[0] == [
                'git',
                'show',
                'v2.13.4',
                '--date=iso-strict',
                '--quiet',
                '--format=%H%n%cd',
            ]:
                stdout = MOCK_COMMIT_DATA
            if args[0] == ['git', 'tag']:
                stdout = 'v1\nv2.13.4'
            self.assertNotEqual(stdout, None, args[0])
            result = MagicMock()
            result.stdout = stdout
            return result

        self.mock_execute_shell.side_effect = execute_shell_returns
        out = self.gitsubmodule.annotate_submodule(self.submodule)
        self.assertEqual(out, self.submodule)
        version_info = self.submodule.remote_commit
        self.assertNotEqual(version_info, None)
        assert version_info
        self.assertEqual(version_info.version_name, MOCK_COMMIT_HASH)
        self.assertEqual(version_info.version_date, MOCK_COMMIT_DATE)
        version_info = self.submodule.remote_tag
        self.assertNotEqual(version_info, None)
        assert version_info
        self.assertEqual(version_info.version_name, MOCK_COMMIT_TAG)
        self.assertEqual(version_info.version_date, MOCK_COMMIT_DATE)

    def test_info_no_tag(self) -> None:
        def execute_shell_returns(
            *args: List[Any], **kwargs: Dict[str, Any]
        ) -> MagicMock:
            stdout = None
            if args[0] == ['git', 'fetch', '-tp']:
                stdout = ''
            if args[0] == [
                'git',
                'show',
                'origin',
                '--date=iso-strict',
                '--quiet',
                '--format=%H%n%cd',
            ]:
                stdout = MOCK_COMMIT_DATA
            if args[0] == ['git', 'tag']:
                stdout = ''
            self.assertNotEqual(stdout, None, args[0])
            result = MagicMock()
            result.stdout = stdout
            return result

        self.mock_execute_shell.side_effect = execute_shell_returns
        out = self.gitsubmodule.annotate_submodule(self.submodule)
        self.assertEqual(out, self.submodule)
        version_info = self.submodule.remote_commit
        self.assertNotEqual(version_info, None)
        assert version_info
        self.assertEqual(version_info.version_name, MOCK_COMMIT_HASH)
        self.assertEqual(version_info.version_date, MOCK_COMMIT_DATE)
        version_info = self.submodule.remote_tag
        self.assertEqual(version_info, None)


class TestGetRemoteTag(unittest.TestCase):
    def setUp(self) -> None:
        self.gitsubmodule = GitSubmodule()
        self.mock_execute_shell = MagicMock()
        setattr(
            self.gitsubmodule.util,
            'execute_shell',
            self.mock_execute_shell,
        )
        self.submodule = Submodule(Path('./git-browse'))
        self.original_get_version_info = GitSubmodule.get_version_info
        self.mock_get_version_info = MagicMock()
        setattr(
            GitSubmodule,
            'get_version_info',
            self.mock_get_version_info,
        )

    def tearDown(self) -> None:
        setattr(
            GitSubmodule,
            'get_version_info',
            self.original_get_version_info,
        )

    def test_one_tag(self) -> None:
        self.mock_execute_shell().stdout = 'v1'
        self.gitsubmodule.get_remote_tag(self.submodule)
        self.assertEqual(self.mock_get_version_info.call_args[0][0], 'v1')

    def test_sorted_tags(self) -> None:
        self.mock_execute_shell().stdout = 'a\nb'
        self.gitsubmodule.get_remote_tag(self.submodule)
        self.assertEqual(self.mock_get_version_info.call_args[0][1], 'b')

    def test_semver_tags(self) -> None:
        self.mock_execute_shell().stdout = '1.15.0\n1.5.0'
        self.gitsubmodule.get_remote_tag(self.submodule)
        self.assertEqual(self.mock_get_version_info.call_args[0][1], '1.15.0')

    def test_semver_v_tags(self) -> None:
        self.mock_execute_shell().stdout = 'v1.15.0\nv1.5.0'
        self.gitsubmodule.get_remote_tag(self.submodule)
        self.assertEqual(self.mock_get_version_info.call_args[0][1], 'v1.15.0')


class TestVersionInfo(unittest.TestCase):
    def test_find_tag(self) -> None:
        info = GitSubmodule.get_version_info(MOCK_COMMIT_DATA, MOCK_COMMIT_TAG)
        self.assertEqual(info.version_name, 'v2.13.4')
        self.assertEqual(info.version_date, MOCK_COMMIT_DATE)

    def test_find_commit(self) -> None:
        info = GitSubmodule.get_version_info(MOCK_COMMIT_DATA, '')
        self.assertEqual(
            info.version_name, 'fc9ab12365ace68f77cc9ac303bbf239d56601db'
        )
        self.assertEqual(info.version_date, MOCK_COMMIT_DATE)


class TestUpdateSubmodule(unittest.TestCase):
    def setUp(self) -> None:
        self.gitsubmodule = GitSubmodule()
        self.mock_execute_shell = MagicMock()
        setattr(
            self.gitsubmodule.util,
            'execute_shell',
            self.mock_execute_shell,
        )
        self.submodule = Submodule(Path('./git-browse'))
        now = datetime.datetime.now()
        old = now - datetime.timedelta(days=60)
        self.new_tag_version = VersionInfo(
            version_name='new_tag', version_date=now
        )
        self.old_tag_version = VersionInfo(
            version_name='old_tag', version_date=old
        )
        self.commit_version = VersionInfo(
            version_name='commit', version_date=now
        )

    def test_update_submodule_none(self) -> None:
        version = self.gitsubmodule.update_submodule(self.submodule)
        self.assertEqual(version, None)

    def test_update_submodule_new_tag(self) -> None:
        self.submodule.remote_tag = self.new_tag_version
        self.submodule.remote_commit = self.commit_version
        version = self.gitsubmodule.update_submodule(self.submodule)
        self.assertEqual(version, 'new_tag')

    def test_update_submodule_old_tag(self) -> None:
        self.submodule.remote_tag = self.old_tag_version
        self.submodule.remote_commit = self.commit_version
        version = self.gitsubmodule.update_submodule(self.submodule)
        self.assertEqual(version, 'commit')

    def test_update_submodule_commit(self) -> None:
        self.submodule.remote_commit = self.commit_version
        version = self.gitsubmodule.update_submodule(self.submodule)
        self.assertEqual(version, 'commit')

    def test_update_submodule_tag(self) -> None:
        self.submodule.remote_tag = self.new_tag_version
        version = self.gitsubmodule.update_submodule(self.submodule)
        self.assertEqual(version, 'new_tag')
