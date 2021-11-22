from __future__ import annotations
import argparse
import io
import subprocess
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
        self.mock_execute_shell = MagicMock()
        setattr(self.req_update.util, 'execute_shell', self.mock_execute_shell)

    def test_main(self) -> None:
        mock_get_args = MagicMock()
        setattr(self.req_update, 'get_args', mock_get_args)
        mock_check = MagicMock()
        setattr(self.req_update, 'check_repository_cleanliness', mock_check)
        mock_applicable = MagicMock()
        setattr(self.req_update.python, 'check_applicable', mock_applicable)
        setattr(
            self.req_update.python, 'update_install_dependencies', MagicMock()
        )
        self.req_update.main()
        self.assertTrue(mock_get_args.called)
        self.assertTrue(mock_check.called)
        self.assertTrue(mock_applicable.called)


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


class TestCheckRepositoryCleanliness(unittest.TestCase):
    def setUp(self) -> None:
        self.req_update = req_update.ReqUpdate()
        self.mock_execute_shell = MagicMock()
        setattr(self.req_update.util, 'execute_shell', self.mock_execute_shell)

    def test_clean(self) -> None:
        def execute_shell_returns(
            command: List[str],
            readonly: bool,
        ) -> subprocess.CompletedProcess[bytes]:
            if 'pip' in command:
                return MagicMock(stdout='pip 20.2.4')
            return MagicMock(stdout='')
        self.mock_execute_shell.side_effect = execute_shell_returns
        self.req_update.check_repository_cleanliness()

    def test_unclean(self) -> None:
        self.mock_execute_shell.return_value = MagicMock(
            stdout=' M req_update/req_update.py'
        )
        with self.assertRaises(RuntimeError):
            self.req_update.check_repository_cleanliness()
