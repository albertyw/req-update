import unittest

from req_update import req_update


class TestExecuteShell(unittest.TestCase):
    def test_ls(self) -> None:
        result = req_update.execute_shell(['ls'])
        self.assertTrue(len(result.stdout) > 0)
        files = result.stdout.decode('utf-8').split('\n')
        self.assertIn('requirements-test.txt', files)
