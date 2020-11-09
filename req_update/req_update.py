#!/usr/bin/env python3

from __future__ import annotations
import argparse
from contextlib import contextmanager
import json
import re
import subprocess
from typing import Dict, Iterator, List

VERSION = (1, 2, 0)
__version__ = '.'.join(map(str, VERSION))


DESCRIPTION = (
    'Update python dependencies for your project with git integration\n'
    'https://github.com/albertyw/req-update'
)
BRANCH_NAME = 'dep-update'
COMMIT_MESSAGE = 'Update {package} package to {version}'
PYTHON_PACKAGE_NAME_REGEX = r'([a-zA-Z0-9_]+)'
PYTHON_PACKAGE_OPERATOR_REGEX = r'([<=>]+)'
PYTHON_PACKAGE_VERSION_REGEX = r'([0-9\.]+[ ]+)'
PYTHON_REQUIREMENTS_LINE_REGEX = r'^%s%s%s' % (
    PYTHON_PACKAGE_NAME_REGEX,
    PYTHON_PACKAGE_OPERATOR_REGEX,
    PYTHON_PACKAGE_VERSION_REGEX,
)
REQUIREMENTS_FILES = [
    'requirements.txt',
    'requirements-test.txt',
]


def main() -> None:
    ReqUpdate().main()


class ReqUpdate():
    def __init__(self) -> None:
        self.verbose = False
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
        self.verbose = args.verbose
        self.dry_run = args.dryrun
        return args

    def check_repository_cleanliness(self) -> None:
        """
        Check that the repository is ready for updating dependencies.
        Non-clean repositories will raise a RuntimeError
        """
        # Make sure there are no uncommitted files
        command = ['git', 'status', '--porcelain']
        result = self.execute_shell(command, True)
        if not len(result.stdout) == 0:
            raise RuntimeError('Repository not clean')

        # Make sure pip is recent enough
        command = ['pip', '--version']
        result = self.execute_shell(command, True)
        try:
            pip_version = result.stdout.split(' ')
            pip_major_version = int(pip_version[1].split('.')[0])
        except (ValueError, IndexError):
            raise RuntimeError('Pip version is not parseable')
        if int(pip_major_version) < 9:
            raise RuntimeError('Pip version must be at least v9')

    def create_branch(self) -> None:
        """ Create a new branch for committing dependency updates """
        # Make sure branch does not already exist
        command = ['git', 'branch']
        result = self.execute_shell(command, True)
        output = result.stdout
        branches = [b.strip() for b in output.split('\n')]
        if BRANCH_NAME in branches:
            command = ['git', 'checkout', BRANCH_NAME]
        else:
            command = ['git', 'checkout', '-b', BRANCH_NAME]
        self.execute_shell(command, False)

    def rollback_branch(self) -> None:
        """ Delete the dependency update branch """
        command = ['git', 'checkout', '-']
        self.execute_shell(command, False)
        command = ['git', 'branch', '-d', BRANCH_NAME]
        self.execute_shell(command, False)

    def update_dependencies(self) -> None:
        """ Update and commit a list of dependency updates """
        outdated_list = self.get_pip_outdated()
        clean = True
        for outdated in outdated_list:
            dependency = outdated['name']
            version = outdated['latest_version']
            written = self.write_dependency_update(dependency, version)
            if written:
                self.commit_dependency_update(dependency, version)
                clean = False
        if clean:
            self.log('No updates.  Rolling back')
            self.rollback_branch()

    def get_pip_outdated(self) -> List[Dict[str, str]]:
        """ Get a list of outdated pip packages """
        command = ['pip', 'list', '--outdated', '--format', 'json']
        result = self.execute_shell(command, True)
        outdated: List[Dict[str, str]] = json.loads(result.stdout)
        outdated = sorted(outdated, key=lambda p: p['name'])
        return outdated

    @staticmethod
    @contextmanager
    def edit_requirements(file_name: str) -> Iterator[List[str]]:
        """
        This yields lines from a file, which will be written back into
        the file after yielding
        """
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
        updated = False
        for reqfile in REQUIREMENTS_FILES:
            with ReqUpdate.edit_requirements(reqfile) as lines:
                updated = updated or self.write_dependency_update_lines(
                    dependency, version, lines
                )
        return updated

    def write_dependency_update_lines(
        self, dependency: str, version: str, lines: List[str]
    ) -> bool:
        """
        Given a dependency and some lines, update the lines.  Return a
        boolean for whether the lines have been updated
        """
        for i, line in enumerate(lines):
            match = re.match(PYTHON_REQUIREMENTS_LINE_REGEX, line)
            if not match:
                continue
            old_version = match.group(3)
            if match.group(1) == dependency:
                if old_version[-1] == ' ':
                    spacing = len(old_version) - len(version)
                    version = version + ' ' * spacing
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
        self.execute_shell(command, False)

    def execute_shell(
        self, command: List[str], readonly: bool,
    ) -> subprocess.CompletedProcess[str]:
        """ Helper method to execute commands in a shell and return output """
        if self.verbose:
            self.log(' '.join(command))
        if self.dry_run and not readonly:
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
        """ Helper method for taking care of logging statements """
        print(data)


if __name__ == "__main__":
    main()
