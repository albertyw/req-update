from __future__ import annotations
from contextlib import contextmanager
import json
import os
import re
import subprocess
from typing import Iterator

from req_update.util import Updater, Util


PYTHON_PACKAGE_NAME_REGEX = r'(?P<name>[a-zA-Z0-9\-_]+)'
PYTHON_PACKAGE_OPERATOR_REGEX = r'(?P<operator>[<=>]+)'
PYTHON_PACKAGE_VERSION_REGEX = r'(?P<version>(\d+!)?(\d+)(\.\d+)+([\.\-\_])?((a(lpha)?|b(eta)?|c|r(c|ev)?|pre(view)?)\d*)?(\.?(post|dev)\d*)?)'  # noqa
PYTHON_PACKAGE_SPACER_REGEX = r'(?P<spacer>([ ]+\#)?)'
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


class Python(Updater):
    def __init__(self, util: Util) -> None:
        self.updated_files: set[str] = set([])
        super().__init__(util)

    def check_applicable(self) -> bool:
        # Make sure pip is recent enough
        command = ['pip', '--version']
        try:
            result = self.util.execute_shell(
                command, True, suppress_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Cannot find pip
            return False
        try:
            pip_version = result.stdout.split(' ')
            pip_major_version = int(pip_version[1].split('.')[0])
        except (ValueError, IndexError):
            # Pip version is not parseable
            return False
        if int(pip_major_version) < 9:
            # Pip version must be at least v9
            return False

        # Make sure there's at least one requirements files
        for f in REQUIREMENTS_FILES:
            if f in os.listdir('.'):
                break
        else:
            return False
        return True

    def update_dependencies(self) -> bool:
        """
        Update dependencies
        Return if updates were made.
        """
        updates_made = self.update_dependencies_file()
        if updates_made:
            self.install_updates()
        else:
            self.util.warn('No python updates')
        return updates_made

    def update_dependencies_file(self) -> bool:
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
                self.util.commit_dependency_update(self.language, dependency, version)
                self.util.push_dependency_update()
                clean = False
        return not clean

    def get_pip_outdated(self) -> list[dict[str, str]]:
        """Get a list of outdated pip packages"""
        command = ['pip', 'list', '--outdated', '--format', 'json']
        result = self.util.execute_shell(command, True)
        outdated: list[dict[str, str]] = json.loads(result.stdout)
        outdated = sorted(outdated, key=lambda p: p['name'])
        return outdated

    @staticmethod
    @contextmanager
    def edit_requirements(file_name: str, dry_run: bool) -> Iterator[list[str]]:
        """
        This yields lines from a file, which will be written back into
        the file after yielding
        """
        lines: list[str] = []
        try:
            with open(file_name, 'r') as handle:
                lines = handle.readlines()
        except FileNotFoundError:
            pass
        yield lines
        if dry_run or not lines:
            return
        with open(file_name, 'w') as handle:
            handle.write(''.join(lines))

    def write_dependency_update(self, dependency: str, version: str) -> bool:
        """Given a dependency, update it to a given version"""
        updated = False
        for reqfile in REQUIREMENTS_FILES:
            with Python.edit_requirements(reqfile, self.util.dry_run) as lines:
                updated_file = self.write_dependency_update_lines(
                    dependency, version, lines
                )
                if updated_file:
                    self.updated_files.add(reqfile)
                    updated = True
        return updated

    def write_dependency_update_lines(
        self, dependency: str, version: str, lines: list[str]
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
            dependency_file = match.group('name').replace('_', '-').lower()
            dependency_update = dependency.lower()
            if dependency_file != dependency_update:
                continue
            old_version = match.group('version')
            old_spacer = match.group('spacer')
            if old_spacer:
                spacing = len(old_version) + len(old_spacer) - len(version)
                if spacing <= 1:
                    spacing = 10 - len(version) % 10 + 1
                spacer = ' ' * (spacing - 1) + '#'
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
        """Install requirements updates"""
        for updated_file in self.updated_files:
            command = ['pip', 'install', '-r', updated_file]
            self.util.execute_shell(command, False)
            self.util.log('Installing updated packages in %s' % updated_file)
