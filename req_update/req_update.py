#!/usr/bin/env python3

from __future__ import annotations
import argparse
import os
import subprocess
import sys
from typing import Set

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import python  # NOQA
import util  # NOQA


VERSION = (1, 5, 3)
__version__ = '.'.join(map(str, VERSION))


DESCRIPTION = (
    'Update python dependencies for your project with git integration\n'
    'https://github.com/albertyw/req-update'
)


def main() -> None:
    ReqUpdate().main()


class ReqUpdate():
    def __init__(self) -> None:
        self.install = False
        self.updated_files: Set[str] = set([])
        self.util = util.Util()
        self.python = python.Python()
        self.python.util = self.util

    def main(self) -> None:
        """ Update all dependencies """
        self.get_args()
        self.check_repository_cleanliness()
        self.util.create_branch()
        self.python.update_install_dependencies()

    def get_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser.add_argument(
            '-p',
            '--push',
            action='store_true',
            help='Push commits individually to remote origin',
        )
        parser.add_argument(
            '-i',
            '--install',
            action='store_true',
            help='Install updates',
        )
        parser.add_argument(
            '-d',
            '--dryrun',
            action='store_true',
            help='Dry run',
        )
        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='Verbose output',
        )
        parser.add_argument(
            '--version',
            action='version',
            version=__version__,
        )
        args = parser.parse_args()
        self.install = args.install
        self.util.push = args.push
        self.util.verbose = args.verbose
        self.util.dry_run = args.dryrun
        return args

    def check_repository_cleanliness(self) -> None:
        """
        Check that the repository is ready for updating dependencies.
        Non-clean repositories will raise a RuntimeError
        """
        # Make sure there are no uncommitted files
        command = ['git', 'status', '--porcelain']
        result = self.util.execute_shell(command, True)
        lines = result.stdout.split("\n")
        # Do not count untracked files when checking for repository cleanliness
        lines = [line for line in lines if line and line[:2] != '??']
        if lines:
            raise RuntimeError('Repository not clean')

        # Make sure pip is recent enough
        command = ['pip', '--version']
        result = self.util.execute_shell(command, True)
        try:
            pip_version = result.stdout.split(' ')
            pip_major_version = int(pip_version[1].split('.')[0])
        except (ValueError, IndexError):
            raise RuntimeError('Pip version is not parseable')
        if int(pip_major_version) < 9:
            raise RuntimeError('Pip version must be at least v9')


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError:
        pass
