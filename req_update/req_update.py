#!/usr/bin/env python3

from __future__ import annotations
import argparse
import os
import pathlib
import subprocess
import sys

current_path = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
parent_path = current_path.parent.resolve()
sys.path.insert(0, str(parent_path))

from req_update.docker import Docker  # NOQA
from req_update.drone import Drone  # NOQA
from req_update.githubworkflow import GithubWorkflow  # NOQA
from req_update.gitsubmodule import GitSubmodule  # NOQA
from req_update.go import Go  # NOQA
from req_update.node import Node  # NOQA
from req_update.python import Python  # NOQA
from req_update.util import Updater, Util  # NOQA


VERSION = (2, 7, 4)
__version__ = '.'.join(map(str, VERSION))


DESCRIPTION = (
    'Update python, go, node, and git submodule dependencies for your '
    'project with git integration\n\n'
    'https://github.com/albertyw/req-update'
)
UPDATERS: list[type[Updater]] = [
    Docker,
    Drone,
    GithubWorkflow,
    GitSubmodule,
    Go,
    Node,
    Python,
]


def main() -> None:
    ReqUpdate().main()


class ReqUpdate:
    def __init__(self) -> None:
        self.updated_files: set[str] = set([])
        self.util = Util()
        self.language: str = ''
        self.updaters: list[Updater] = []
        for updater in UPDATERS:
            u = updater(self.util)
            self.updaters.append(u)

    def main(self) -> bool:
        """
        Update all dependencies
        Return if updates were made
        """
        self.get_args()
        branch_created = False
        if not self.util.ignore_cleanliness:
            clean = self.util.check_repository_cleanliness()
            if not clean:
                raise RuntimeError('Repository is not clean')
        updates_made = False
        for updater in self.updaters:
            if self.language:
                if self.language != updater.language.lower():
                    continue
            if not updater.check_applicable():
                if self.language:
                    warn = (
                        'Selected language %s but language not applicable'
                        % self.language
                    )
                    self.util.warn(warn)
                continue
            if not branch_created:
                self.util.create_branch()
                branch_created = True
            updates = updater.update_dependencies()
            if not updates:
                self.util.warn('No %s updates' % updater.language)
            updates_made = updates_made or updates
        if branch_created and not updates_made:
            self.util.rollback_branch()
        return updates_made

    def get_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description=DESCRIPTION,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        language_help = 'Language/package manager to update.  Options are: '
        language_help += ', '.join(ReqUpdate.updater_names())
        parser.add_argument(
            '-l',
            '--language',
            type=str,
            help=language_help,
        )
        parser.add_argument(
            '-p',
            '--push',
            action='store_true',
            help='Push commits individually to remote origin',
        )
        parser.add_argument(
            '-i',
            '--ignore-cleanliness',
            action='store_true',
            help='Ignore checking if the repository is clean',
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
        self.language = args.language
        self.util.push = args.push
        self.util.verbose = args.verbose
        self.util.ignore_cleanliness = args.ignore_cleanliness
        self.util.dry_run = args.dryrun
        return args

    @staticmethod
    def updater_names() -> list[str]:
        return [u.__name__.lower() for u in UPDATERS]


if __name__ == '__main__':  # pragma: no cover
    try:
        main()
    except subprocess.CalledProcessError:
        pass
