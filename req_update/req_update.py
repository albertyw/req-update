from __future__ import annotations
import argparse
import json
import subprocess
from typing import Dict, List

VERSION = (0, 0, 1)
__version__ = '.'.join(map(str, VERSION))


DESCRIPTION = (
    'Update python dependencies for your project with git integration\n'
    'https://github.com/albertyw/req-update'
)
BRANCH_NAME = 'dep-update'


class ReqUpdate():
    def __init__(self) -> None:
        self.dry_run = False

    def main(self) -> None:
        """ Update all dependencies """
        self.get_args()
        self.check_repository_cleanliness()
        self.create_branch()
        self.update_dependencies()

    def get_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description=DESCRIPTION)
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
        self.dry_run = args.dryrun
        return args

    def check_repository_cleanliness(self) -> None:
        """ Check that the repository is ready for updating dependencies """
        command = ['git', 'status', '--porcelain']
        result = self.execute_shell(command)
        if not len(result.stdout) == 0:
            raise RuntimeError('Repository not clean')

    def create_branch(self) -> None:
        """ Create a new branch for committing dependency updates """
        command = ['git', 'checkout', '-b', BRANCH_NAME]
        self.execute_shell(command)

    def update_dependencies(self) -> None:
        """ Update and commit a list of dependency updates """
        pass

    def get_pip_outdated(self) -> List[Dict[str, str]]:
        """ Get a list of outdated pip packages """
        command = ['pip', 'list', '--outdated', '--format', 'json']
        result = self.execute_shell(command)
        outdated: List[Dict[str, str]] = json.loads(result.stdout)
        return outdated

    def write_dependency_update(self, dependency: str, version: str) -> None:
        """ Given a dependency, update it to a given version """
        pass

    def commit_dependency_update(self, dependency: str, version: str) -> None:
        """ Create a commit with a dependency update """
        pass

    def execute_shell(
        self, command: List[str]
    ) -> subprocess.CompletedProcess[bytes]:
        if self.dry_run:
            self.log(' '.join(command))
            return subprocess.CompletedProcess(
                command, 0, stdout=b'', stderr=b''
            )
        result = subprocess.run(
            command,
            capture_output=True,
        )
        result.check_returncode()
        return result

    def log(self, data: str) -> None:
        print(data)


if __name__ == "__main__":
    ReqUpdate().main()
