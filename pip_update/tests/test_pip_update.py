import unittest

from pip_update import pip_update


class TestExecuteShell(unittest.TestCase):
    def test_ls(self) -> None:
        result = pip_update.execute_shell(['ls'])
        self.assertTrue(len(result.stdout) > 0)
        files = result.stdout.decode('utf-8').split('\n')
        self.assertIn('requirements-test.txt', files)
