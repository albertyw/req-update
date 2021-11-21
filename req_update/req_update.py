#!/usr/bin/env python3

from __future__ import annotations
import argparse
from contextlib import contextmanager
import json
import re
import subprocess
from typing import Dict, Iterator, List, Set

from . import util


VERSION = (1, 5, 2)
__version__ = '.'.join(map(str, VERSION))


DESCRIPTION = (
    'Update python dependencies for your project with git integration\n'
    'https://github.com/albertyw/req-update'
)
BRANCH_NAME = 'dep-update'
PYTHON_PACKAGE_NAME_REGEX = r'(?P<name>[a-zA-Z0-9\-_]+)'
PYTHON_PACKAGE_OPERATOR_REGEX = r'(?P<operator>[<=>]+)'
PYTHON_PACKAGE_VERSION_REGEX = r'(?P<version>(\d+!)?(\d+)(\.\d+)+([\.\-\_])?((a(lpha)?|b(eta)?|c|r(c|ev)?|pre(view)?)\d*)?(\.?(post|dev)\d*)?)'  # noqa
PYTHON_PACKAGE_SPACER_REGEX = r'(?P<spacer>[ ]*)'
PYTHON_REQUIREMENTS_LINE_REGEX = r'^%s%s%s%s' % (
    PYTHON_PACKAGE_NAME_REGEX,
    PYTHON_PACKAGE_OPERATOR_REGEX,
    PYTHON_PACKAGE_VERSION_REGEX,
    PYTHON_PACKAGE_SPACER_REGEX,
)
REQUIREMENTS_FILES = [
    'requirements.txt',
    'requirements-test.txt',
]


def main() -> None:
    ReqUpdate().main()


class ReqUpdate():
    def __init__(self) -> None:
        self.install = False
        self.updated_files: Set[str] = set([])
        self.branch_exists = False
        self.util = util.Util()

    def main(self) -> None:
        """ Update all dependencies """
        self.get_args()
        self.check_repository_cleanliness()
        self.create_branch()
        self.update_install_dependencies()

    def update_install_dependencies(self) -> None:
        """ Update dependencies and install updates """
        self.update_dependencies()
        self.install_updates()

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

    def create_branch(self) -> None:
        """ Create a new branch for committing dependency updates """
        # Make sure branch does not already exist
        command = ['git', 'branch', '--list', BRANCH_NAME]
        result = self.util.execute_shell(command, True)
        output = result.stdout
        if output.strip() != '':
            command = ['git', 'checkout', BRANCH_NAME]
            self.branch_exists = True
        else:
            command = ['git', 'checkout', '-b', BRANCH_NAME]
        self.util.execute_shell(command, False)

    def rollback_branch(self) -> None:
        """ Delete the dependency update branch """
        if self.branch_exists:
            return
        command = ['git', 'checkout', '-']
        self.util.execute_shell(command, False)
        command = ['git', 'branch', '-d', BRANCH_NAME]
        self.util.execute_shell(command, False)

    def update_dependencies(self) -> bool:
        """
        Update and commit a list of dependency updates.
        Return if updates were made.
        """
        outdated_list = self.get_pip_outdated()
        clean = True
        for outdated in outdated_list:
            dependency = outdated['name']
            self.util.log('Checking dependency: %s' % dependency)
            version = outdated['latest_version']
            written = self.write_dependency_update(dependency, version)
            if written:
                self.util.commit_dependency_update(dependency, version)
                self.util.push_dependency_update()
                clean = False
        if clean:
            self.util.log('No updates')
            self.rollback_branch()
        return not clean

    def get_pip_outdated(self) -> List[Dict[str, str]]:
        """ Get a list of outdated pip packages """
        command = ['pip', 'list', '--outdated', '--format', 'json']
        result = self.util.execute_shell(command, True)
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
                updated_file = self.write_dependency_update_lines(
                    dependency, version, lines
                )
                if updated_file:
                    self.updated_files.add(reqfile)
                    updated = True
        return updated

    def write_dependency_update_lines(
        self, dependency: str, version: str, lines: List[str]
    ) -> bool:
        """
        Given a dependency and some lines, update the lines.  Return a
        boolean for whether the lines have been updated
        """
        dependency = dependency.replace('_', '-')
        for i, line in enumerate(lines):
            match = re.match(PYTHON_REQUIREMENTS_LINE_REGEX, line)
            if not match:
                continue
            if match.group('name').replace('_', '-') != dependency:
                continue
            old_version = match.group('version')
            old_spacer = match.group('spacer')
            if old_spacer:
                spacing = len(old_version) + len(old_spacer) - len(version)
                spacer = ' ' * spacing
            else:
                spacer = ''
            new_line = re.sub(
                PYTHON_REQUIREMENTS_LINE_REGEX,
                r'\g<1>\g<2>%s%s' % (version, spacer),
                line,
            )
            if line == new_line:
                continue
            self.util.check_major_version_update(
                dependency, old_version, version
            )
            lines[i] = new_line
            return True
        return False

    def install_updates(self) -> None:
        """ Install requirements updates """
        if not self.install:
            return
        for updated_file in self.updated_files:
            command = ['pip', 'install', '-r', updated_file]
            self.util.execute_shell(command, False)
            self.util.log('Installing updated packages in %s' % updated_file)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError:
        pass
