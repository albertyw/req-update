from __future__ import annotations
import argparse
import io
import sys
from typing import List
import unittest
from unittest.mock import MagicMock, patch

from req_update import req_update


PIP_OUTDATED = [
    {"name": "varsnap", "version": "1.0.0", "latest_version": "1.2.3"}
]


class TestMain(unittest.TestCase):
    def test_main(self) -> None:
        with patch('req_update.req_update.ReqUpdate') as mock_req_update:
            req_update.main()
            self.assertTrue(mock_req_update().main.called)


class TestReqUpdateMain(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()
        self.mock_get_args = MagicMock()
        setattr(self.req_update, 'get_args', self.mock_get_args)
        self.mock_check = MagicMock()
        setattr(
            self.req_update.util, 'check_repository_cleanliness',
            self.mock_check
        )
        self.mock_create_branch = MagicMock()
        setattr(self.req_update.util, 'create_branch', self.mock_create_branch)
        self.mock_python_applicable = MagicMock()
        setattr(
            self.req_update.python, 'check_applicable',
            self.mock_python_applicable
        )
        self.mock_python_update = MagicMock()
        setattr(
            self.req_update.python, 'update_install_dependencies',
            self.mock_python_update,
        )
        self.mock_node_applicable = MagicMock()
        setattr(
            self.req_update.node, 'check_applicable',
            self.mock_node_applicable
        )
        self.mock_node_update = MagicMock()
        setattr(
            self.req_update.node, 'update_install_dependencies',
            self.mock_node_update,
        )
        self.mock_rollback = MagicMock()
        setattr(self.req_update.util, 'rollback_branch', self.mock_rollback)

    def test_main_no_applicable(self) -> None:
        self.mock_python_applicable.return_value = False
        self.mock_node_applicable.return_value = False
        updated = self.req_update.main()
        self.assertFalse(updated)
        self.assertTrue(self.mock_get_args.called)
        self.assertTrue(self.mock_check.called)
        self.assertTrue(self.mock_python_applicable.called)
        self.assertFalse(self.mock_python_update.called)
        self.assertTrue(self.mock_node_applicable.called)
        self.assertFalse(self.mock_node_update.called)
        self.assertFalse(self.mock_create_branch.called)
        self.assertFalse(self.mock_rollback.called)

    def test_main_python_applicable_no_update(self) -> None:
        self.mock_python_applicable.return_value = True
        self.mock_python_update.return_value = False
        self.mock_node_applicable.return_value = False
        updated = self.req_update.main()
        self.assertFalse(updated)
        self.assertTrue(self.mock_get_args.called)
        self.assertTrue(self.mock_check.called)
        self.assertTrue(self.mock_python_applicable.called)
        self.assertTrue(self.mock_python_update.called)
        self.assertTrue(self.mock_node_applicable.called)
        self.assertFalse(self.mock_node_update.called)
        self.assertTrue(self.mock_create_branch.called)
        self.assertTrue(self.mock_rollback.called)

    def test_main_python_applicable_update(self) -> None:
        self.mock_python_applicable.return_value = True
        self.mock_python_update.return_value = True
        self.mock_node_applicable.return_value = False
        updated = self.req_update.main()
        self.assertTrue(updated)
        self.assertTrue(self.mock_get_args.called)
        self.assertTrue(self.mock_check.called)
        self.assertTrue(self.mock_python_applicable.called)
        self.assertTrue(self.mock_python_update.called)
        self.assertTrue(self.mock_node_applicable.called)
        self.assertFalse(self.mock_node_update.called)
        self.assertTrue(self.mock_create_branch.called)
        self.assertFalse(self.mock_rollback.called)

    def test_main_node_applicable_no_update(self) -> None:
        self.mock_python_applicable.return_value = False
        self.mock_node_applicable.return_value = True
        self.mock_node_update.return_value = False
        updated = self.req_update.main()
        self.assertFalse(updated)
        self.assertTrue(self.mock_get_args.called)
        self.assertTrue(self.mock_check.called)
        self.assertTrue(self.mock_python_applicable.called)
        self.assertFalse(self.mock_python_update.called)
        self.assertTrue(self.mock_node_applicable.called)
        self.assertTrue(self.mock_node_update.called)
        self.assertTrue(self.mock_create_branch.called)
        self.assertTrue(self.mock_rollback.called)

    def test_main_node_applicable_update(self) -> None:
        self.mock_python_applicable.return_value = False
        self.mock_node_applicable.return_value = True
        self.mock_node_update.return_value = True
        updated = self.req_update.main()
        self.assertTrue(updated)
        self.assertTrue(self.mock_get_args.called)
        self.assertTrue(self.mock_check.called)
        self.assertTrue(self.mock_python_applicable.called)
        self.assertFalse(self.mock_python_update.called)
        self.assertTrue(self.mock_node_applicable.called)
        self.assertTrue(self.mock_node_update.called)
        self.assertTrue(self.mock_create_branch.called)
        self.assertFalse(self.mock_rollback.called)

    def test_main_all_applicable_no_update(self) -> None:
        self.mock_python_applicable.return_value = True
        self.mock_python_update.return_value = False
        self.mock_node_applicable.return_value = True
        self.mock_node_update.return_value = False
        updated = self.req_update.main()
        self.assertFalse(updated)
        self.assertTrue(self.mock_get_args.called)
        self.assertTrue(self.mock_check.called)
        self.assertTrue(self.mock_python_applicable.called)
        self.assertTrue(self.mock_python_update.called)
        self.assertTrue(self.mock_node_applicable.called)
        self.assertTrue(self.mock_node_update.called)
        self.assertTrue(self.mock_create_branch.called)
        self.assertTrue(self.mock_rollback.called)

    def test_main_all_applicable_python_update(self) -> None:
        self.mock_python_applicable.return_value = True
        self.mock_python_update.return_value = True
        self.mock_node_applicable.return_value = True
        self.mock_node_update.return_value = False
        updated = self.req_update.main()
        self.assertTrue(updated)
        self.assertTrue(self.mock_get_args.called)
        self.assertTrue(self.mock_check.called)
        self.assertTrue(self.mock_python_applicable.called)
        self.assertTrue(self.mock_python_update.called)
        self.assertTrue(self.mock_node_applicable.called)
        self.assertTrue(self.mock_node_update.called)
        self.assertTrue(self.mock_create_branch.called)
        self.assertFalse(self.mock_rollback.called)

    def test_main_all_applicable_node_update(self) -> None:
        self.mock_python_applicable.return_value = True
        self.mock_python_update.return_value = False
        self.mock_node_applicable.return_value = True
        self.mock_node_update.return_value = True
        updated = self.req_update.main()
        self.assertTrue(updated)
        self.assertTrue(self.mock_get_args.called)
        self.assertTrue(self.mock_check.called)
        self.assertTrue(self.mock_python_applicable.called)
        self.assertTrue(self.mock_python_update.called)
        self.assertTrue(self.mock_node_applicable.called)
        self.assertTrue(self.mock_node_update.called)
        self.assertTrue(self.mock_create_branch.called)
        self.assertFalse(self.mock_rollback.called)


class TestGetArgs(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()

    def get_args_with_argv(self, argv: List[str]) -> argparse.Namespace:
        argv = ['req_update.py'] + argv
        with patch.object(sys, 'argv', argv):
            args = self.req_update.get_args()
        return args

    def test_none(self) -> None:
        args = self.get_args_with_argv([])
        self.assertFalse(args.verbose)

    def test_push(self) -> None:
        self.assertFalse(self.req_update.util.push)
        args = self.get_args_with_argv([])
        self.assertFalse(args.push)
        args = self.get_args_with_argv(['--push'])
        self.assertTrue(args.push)
        args = self.get_args_with_argv(['-p'])
        self.assertTrue(args.push)
        self.assertTrue(self.req_update.util.push)

    def test_install(self) -> None:
        self.assertFalse(self.req_update.install)
        args = self.get_args_with_argv([])
        self.assertFalse(args.install)
        args = self.get_args_with_argv(['--install'])
        self.assertTrue(args.install)
        args = self.get_args_with_argv(['-i'])
        self.assertTrue(args.install)
        self.assertTrue(self.req_update.install)

    def test_dryrun(self) -> None:
        self.assertTrue(self.req_update.util.dry_run)
        args = self.get_args_with_argv([])
        self.assertFalse(args.dryrun)
        args = self.get_args_with_argv(['--dryrun'])
        self.assertTrue(args.dryrun)
        args = self.get_args_with_argv(['-d'])
        self.assertTrue(args.dryrun)
        self.assertTrue(self.req_update.util.dry_run)

    def test_verbose(self) -> None:
        args = self.get_args_with_argv(['--verbose'])
        self.assertTrue(args.verbose)
        args = self.get_args_with_argv(['-v'])
        self.assertTrue(args.verbose)

    def test_version(self) -> None:
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            with self.assertRaises(SystemExit):
                self.get_args_with_argv(['--version'])
            self.assertTrue(len(mock_out.getvalue()) > 0)
