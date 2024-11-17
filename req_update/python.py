from __future__ import annotations
from contextlib import contextmanager
import json
from pathlib import Path
import re
import subprocess
from typing import Iterator

from req_update.util import Updater, Util


PYPROJECT = 'pyproject'
REQUIREMENTS = 'requirements'
PYTHON_PACKAGE_NAME_REGEX = r'(?P<name>[a-zA-Z0-9\-_]+)'
PYTHON_PACKAGE_OPERATOR_REGEX = r'(?P<operator>[<=>]+)'
PYTHON_PACKAGE_VERSION_REGEX = r'(?P<version>(\d+!)?(\d+)(\.\d+)+([\.\-\_])?((a(lpha)?|b(eta)?|c|r(c|ev)?|pre(view)?)\d*)?(\.?(post|dev)\d*)?)'  # noqa
PYTHON_PACKAGE_SPACER_REGEX = r'(?P<spacer>(,?[ ]+\#)?)'
PYPROJECT_OPTIONAL_DEPS_REGEX = re.compile(r'^([a-zA-Z0-9_]+) = \[')
PYTHON_REQUIREMENTS_LINE_REGEX = re.compile('^%s%s%s%s' % (
    PYTHON_PACKAGE_NAME_REGEX,
    PYTHON_PACKAGE_OPERATOR_REGEX,
    PYTHON_PACKAGE_VERSION_REGEX,
    PYTHON_PACKAGE_SPACER_REGEX,
))
PYTHON_PYPROJECT_LINE_REGEX = re.compile('"%s%s%s"%s' % (
    PYTHON_PACKAGE_NAME_REGEX,
    PYTHON_PACKAGE_OPERATOR_REGEX,
    PYTHON_PACKAGE_VERSION_REGEX,
    PYTHON_PACKAGE_SPACER_REGEX,
))
REQUIREMENTS_FILES = [
    Path('requirements.txt'),
    Path('requirements-test.txt'),
]
PYPROJECT_FILES = [
    Path('pyproject.toml'),
]


class Python(Updater):
    def __init__(self, util: Util) -> None:
        self.updated_requirements_files: set[Path] = set([])
        self.updated_pyproject_files: set[Path] = set([])
        super().__init__(util)

    def get_update_files(self, file_type: str='') -> list[Path]:
        command = ['git', 'ls-files']
        try:
            shell = self.util.execute_shell(command, True)
        except subprocess.CalledProcessError:
            return []
        files = [Path(f) for f in shell.stdout.split('\n')]
        requirements_files = [f for f in files if Path(f.name) in REQUIREMENTS_FILES]
        pyproject_files = [f for f in files if Path(f.name) in PYPROJECT_FILES]
        if file_type == REQUIREMENTS:
            return requirements_files
        if file_type == PYPROJECT:
            return pyproject_files
        return requirements_files + pyproject_files

    def check_applicable(self) -> bool:
        # Make sure pip is recent enough
        command = ['pip', '--version']
        try:
            result = self.util.execute_shell(
                command, True, suppress_output=True,
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
        if not self.get_update_files():
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
            self.util.info('Checking dependency: %s' % dependency)
            version = outdated['latest_version']
            written = self.write_dependency_update(dependency, version)
            if written:
                self.util.commit_dependency_update(self.language, dependency, version)
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
    def edit_requirements(file_name: Path, dry_run: bool) -> Iterator[list[str]]:
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
        for reqfile in self.get_update_files(file_type=REQUIREMENTS):
            with Python.edit_requirements(reqfile, self.util.dry_run) as lines:
                updated_file = self.write_dependency_update_lines(
                    dependency, version, lines, REQUIREMENTS,
                )
                if updated_file:
                    self.updated_requirements_files.add(reqfile)
                    updated = True
        for pyproject in self.get_update_files(file_type=PYPROJECT):
            with Python.edit_requirements(pyproject, self.util.dry_run) as lines:
                updated_file = self.write_dependency_update_lines(
                    dependency, version, lines, PYPROJECT,
                )
                if updated_file:
                    self.updated_pyproject_files.add(pyproject)
                    updated = True
        return updated

    def write_dependency_update_lines(
        self, dependency: str, version: str, lines: list[str], file_type: str,
    ) -> bool:
        """
        Given a dependency and some lines, update the lines.  Return a
        boolean for whether the lines have been updated
        """
        if file_type == REQUIREMENTS:
            line_regex = PYTHON_REQUIREMENTS_LINE_REGEX
        elif file_type == PYPROJECT:
            line_regex = PYTHON_PYPROJECT_LINE_REGEX
        dependency = dependency.replace('_', '-')
        updated = False
        for i, line in enumerate(lines):
            match = line_regex.match(line.strip())
            if not match:
                continue
            dependency_file = match.group('name').replace('_', '-').lower()
            dependency_update = dependency.lower()
            if dependency_file != dependency_update:
                continue
            old_version = match.group('version')
            old_spacer = match.group('spacer')
            if file_type == PYPROJECT:
                old_spacer = ',' + old_spacer[1:]
            if file_type == REQUIREMENTS:
                new_line = line_regex.sub(
                    r'\g<1>\g<2>%s%s' % (version, old_spacer),
                    line,
                )
            elif file_type == PYPROJECT:
                new_line = line_regex.sub(
                    r'"\g<1>\g<2>%s"%s' % (version, old_spacer),
                    line,
                )
            if line == new_line:
                continue
            self.util.check_major_version_update(
                dependency, old_version, version,
            )
            lines[i] = new_line
            updated = True
        if not updated:
            return updated
        # Vertically align comments
        comment_alignment = Python.get_comment_alignment(lines, file_type)
        for i, line in enumerate(lines):
            if '#' not in line:
                continue
            if line_regex.search(line) is None:
                continue
            new_line = line
            while new_line.find('#') != comment_alignment:
                if new_line.find('#') < comment_alignment:
                    new_line = new_line.replace('#', ' #')
                else:
                    new_line = new_line.replace(' #', '#')
            lines[i] = new_line
        return updated

    def install_updates(self) -> None:
        """Install requirements updates"""
        for updated_file in self.updated_requirements_files:
            command = ['pip', 'install', '-r', str(updated_file)]
            self.util.execute_shell(command, False)
            self.util.info('Installing updated packages in %s' % updated_file)
        for updated_file in self.updated_pyproject_files:
            command = ['pip', 'install', '-e', '.']
            self.util.execute_shell(command, False)

            # Install optional dependencies
            with open(updated_file, 'r') as handle:
                lines = handle.readlines()
            optional_dependencies = False
            for line in lines:
                if line.strip() == '[project.optional-dependencies]':
                    optional_dependencies = True
                    continue
                if not optional_dependencies:
                    continue
                if line[0] == '[':
                    break
                match = PYPROJECT_OPTIONAL_DEPS_REGEX.match(line)
                if not match:
                    continue
                optional = match.group(1)
                command = ['pip', 'install', '-e', '.[%s]' % optional]
                self.util.execute_shell(command, False)
            self.util.info('Installing updated packages in %s' % updated_file)

    @staticmethod
    def get_comment_alignment(lines: list[str], file_type: str) -> int:
        max_length = 0
        for line in lines:
            if '#' not in line:
                continue
            length = 1 # One whitespace before comments
            if file_type == REQUIREMENTS:
                match = PYTHON_REQUIREMENTS_LINE_REGEX.search(line)
            elif file_type == PYPROJECT:
                match = PYTHON_PYPROJECT_LINE_REGEX.search(line)
                length += 3 # Account for additional quotes and comma
            if not match:
                continue
            length += match.start() # Account for indentation
            length += len(match.group(1) + match.group(2) + match.group(3))
            if length > max_length:
                max_length = length
        alignment = max_length
        if alignment % 10 != 0:
            alignment += 10 - alignment % 10
        return alignment
