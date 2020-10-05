from __future__ import annotations
import argparse
import subprocess
from typing import List, Tuple

VERSION = (0, 0, 1)
__version__ = '.'.join(map(str, VERSION))


DESCRIPTION = (
    'Update python dependencies for your project with git integration\n'
    'https://github.com/albertyw/req-update'
)


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
        return args

    def check_repository_cleanliness(self) -> None:
        """ Check that the repository is ready for updating dependencies """
        command = ['git', 'status', '--porcelain']
        result = self.execute_shell(command)
        if not len(result.stdout) == 0:
            raise RuntimeError('Repository not clean')

    def create_branch(self) -> None:
        """ Create a new branch for committing dependency updates """
        pass

    def update_dependencies(self) -> None:
        """ Update and commit a list of dependency updates """
        pass

    def get_pip_outdated(self) -> List[Tuple[str, str]]:
        """ Get a list of outdated pip packages """
        pass

    def write_dependency_update(self, dependency: str, version: str) -> None:
        """ Given a dependency, update it to a given version """
        pass

    def commit_dependency_update(self, dependency: str, version: str) -> None:
        """ Create a commit with a dependency update """
        pass

    def execute_shell(
        self, command: List[str]
    ) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(
            command,
            capture_output=True,
        )
        result.check_returncode()
        return result


if __name__ == "__main__":
    ReqUpdate().main()
