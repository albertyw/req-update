from __future__ import annotations
import argparse
from contextlib import contextmanager
import json
import re
import subprocess
from typing import Dict, Iterator, List

VERSION = (1, 0, 0)
__version__ = '.'.join(map(str, VERSION))


DESCRIPTION = (
    'Update python dependencies for your project with git integration\n'
    'https://github.com/albertyw/req-update'
)
BRANCH_NAME = 'dep-update'
COMMIT_MESSAGE = 'Update {package} package to {version}'
PYTHON_PACKAGE_NAME_REGEX = r'([a-zA-Z0-9_]+)'
PYTHON_PACKAGE_OPERATOR_REGEX = r'([<=>]+)'
PYTHON_PACKAGE_VERSION_REGEX = r'([0-9\.]+)'
PYTHON_REQUIREMENTS_LINE_REGEX = r'%s%s%s' % (
    PYTHON_PACKAGE_NAME_REGEX,
    PYTHON_PACKAGE_OPERATOR_REGEX,
    PYTHON_PACKAGE_VERSION_REGEX,
)
REQUIREMENTS_FILES = [
    'requirements.txt',
    'requirements-test.txt',
]


class ReqUpdate():
    def __init__(self) -> None:
        self.dry_run = True

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
        # Make sure there are no uncommitted files
        command = ['git', 'status', '--porcelain']
        result = self.execute_shell(command)
        if not len(result.stdout) == 0:
            raise RuntimeError('Repository not clean')

        # Make sure branch does not already exist
        command = ['git', 'branch']
        result = self.execute_shell(command)
        output = result.stdout
        branches = [b.strip() for b in output.split('\n')]
        if BRANCH_NAME in branches:
            raise RuntimeError('Branch "%s" already exists' % BRANCH_NAME)

    def create_branch(self) -> None:
        """ Create a new branch for committing dependency updates """
        command = ['git', 'checkout', '-b', BRANCH_NAME]
        self.execute_shell(command)

    def update_dependencies(self) -> None:
        """ Update and commit a list of dependency updates """
        outdated_list = self.get_pip_outdated()
        for outdated in outdated_list:
            dependency = outdated['name']
            version = outdated['latest_version']
            written = self.write_dependency_update(dependency, version)
            if written:
                self.commit_dependency_update(dependency, version)

    def get_pip_outdated(self) -> List[Dict[str, str]]:
        """ Get a list of outdated pip packages """
        command = ['pip', 'list', '--outdated', '--format', 'json']
        result = self.execute_shell(command)
        outdated: List[Dict[str, str]] = json.loads(result.stdout)
        return outdated

    @staticmethod
    @contextmanager
    def edit_requirements(file_name: str) -> Iterator[List[str]]:
        lines: List[str] = []
        try:
            with open(file_name, 'r') as handle:
                lines = handle.readlines()
        except FileNotFoundError:
            pass
        yield lines
        if not lines:
            return
        with open(file_name, 'w') as handle:
            handle.write(''.join(lines))

    def write_dependency_update(self, dependency: str, version: str) -> bool:
        """ Given a dependency, update it to a given version """
        for reqfile in REQUIREMENTS_FILES:
            with ReqUpdate.edit_requirements(reqfile) as lines:
                for i, line in enumerate(lines):
                    match = re.match(PYTHON_REQUIREMENTS_LINE_REGEX, line)
                    if not match:
                        continue
                    if match.group(1) == dependency:
                        line = re.sub(
                            PYTHON_REQUIREMENTS_LINE_REGEX,
                            r'\g<1>\g<2>%s' % version,
                            line,
                        )
                        lines[i] = line
                        return True
        return False

    def commit_dependency_update(self, dependency: str, version: str) -> None:
        """ Create a commit with a dependency update """
        commit_message = COMMIT_MESSAGE.format(
            package=dependency,
            version=version,
        )
        self.log(commit_message)
        command = ['git', 'commit', '-am', commit_message]
        self.execute_shell(command)

    def execute_shell(
        self, command: List[str]
    ) -> subprocess.CompletedProcess[str]:
        if self.dry_run:
            self.log(' '.join(command))
            return subprocess.CompletedProcess(
                command, 0, stdout='', stderr=''
            )
        result = subprocess.run(
            command,
            capture_output=True,
            encoding='utf-8',
        )
        result.check_returncode()
        return result

    def log(self, data: str) -> None:
        print(data)


if __name__ == "__main__":
    ReqUpdate().main()
