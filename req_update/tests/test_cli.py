import os
import pathlib
import unittest

from req_update import util


class TestCLI(unittest.TestCase):
    def setUp(self) -> None:
        current = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
        parent = current.parent.resolve()
        self.req_update_path = parent / 'req_update.py'
        self.util = util.Util()

    @unittest.skipUnless(os.environ.get('CI'), 'Optimize to run only in CI')
    def test_cli(self) -> None:
        command = ['python3', str(self.req_update_path), '-d']
        self.util.execute_shell(command, readonly=True)

    @unittest.skipUnless(os.environ.get('CI'), 'Optimize to run only in CI')
    def test_shebang(self) -> None:
        command = [str(self.req_update_path), '-d']
        self.util.execute_shell(command, readonly=True)

    @unittest.skipUnless(os.environ.get('CI'), 'Optimize to run only in CI')
    def test_module(self) -> None:
        command = ['python3', '-m', 'req_update.req_update', '-d']
        self.util.execute_shell(command, readonly=True)
