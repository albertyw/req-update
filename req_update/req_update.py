#!/usr/bin/env python3

from __future__ import annotations
import argparse
import os
import pathlib
import subprocess
import sys
from typing import Set

current_path = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
parent_path = current_path.parent.resolve()
sys.path.insert(0, str(parent_path))

from req_update.go import Go  # NOQA
from req_update.node import Node  # NOQA
from req_update.python import Python  # NOQA
from req_update.util import Util  # NOQA


VERSION = (2, 0, 5)
__version__ = ".".join(map(str, VERSION))


DESCRIPTION = (
    "Update python, go, and node dependencies for your project with git "
    "integration\n\n"
    "https://github.com/albertyw/req-update"
)


def main() -> None:
    ReqUpdate().main()


class ReqUpdate:
    def __init__(self) -> None:
        self.updated_files: Set[str] = set([])
        self.util = Util()
        self.python = Python()
        self.python.util = self.util
        self.go = Go()
        self.go.util = self.util
        self.node = Node()
        self.node.util = self.util

    def main(self) -> bool:
        """
        Update all dependencies
        Return if updates were made
        """
        self.get_args()
        branch_created = False
        self.util.check_repository_cleanliness()
        updates_made = False
        if self.python.check_applicable():
            if not branch_created:
                self.util.create_branch()
                branch_created = True
            python_updates = self.python.update_dependencies()
            updates_made = updates_made or python_updates
        if self.node.check_applicable():
            if not branch_created:
                self.util.create_branch()
                branch_created = True
            node_updates = self.node.update_dependencies()
            updates_made = updates_made or node_updates
        if self.go.check_applicable():
            if not branch_created:
                self.util.create_branch()
                branch_created = True
            go_updates = self.go.update_dependencies()
            updates_made = updates_made or go_updates
        if branch_created and not updates_made:
            self.util.rollback_branch()
        return updates_made

    def get_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description=DESCRIPTION,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        parser.add_argument(
            "-p",
            "--push",
            action="store_true",
            help="Push commits individually to remote origin",
        )
        parser.add_argument(
            "-d",
            "--dryrun",
            action="store_true",
            help="Dry run",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Verbose output",
        )
        parser.add_argument(
            "--version",
            action="version",
            version=__version__,
        )
        args = parser.parse_args()
        self.util.push = args.push
        self.util.verbose = args.verbose
        self.util.dry_run = args.dryrun
        return args


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError:
        pass
