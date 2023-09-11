from __future__ import annotations
import os
from pathlib import Path
import re
import subprocess
from typing import Optional, Union


BRANCH_NAME = 'dep-update'
COMMIT_MESSAGE = 'Update {language} {package} package to {version}'
SubprocessOutput = Union[
    subprocess.CalledProcessError,
    subprocess.CompletedProcess,
]


class Updater:
    def __init__(self) -> None:
        self.util = Util()

    def check_applicable(self) -> bool:
        """
        Return if this updater is applicable for the current repository
        """
        return False

    def update_dependencies(self) -> bool:
        """
        Update dependencies
        Return if updates were made
        """
        return False


class Util:
    def __init__(self) -> None:
        self.push = False
        self.verbose = False
        self.dry_run = True
        self.branch_exists = False
        self.language = ''

    def check_repository_cleanliness(self) -> None:
        """
        Check that the repository is ready for updating dependencies.
        Non-clean repositories will raise a RuntimeError
        """
        # Make sure there are no uncommitted files
        if self.dry_run:
            return
        command = ['git', 'status', '--porcelain']
        try:
            result = self.execute_shell(command, True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError('Must run within a git repository') from error
        lines = result.stdout.split('\n')
        # Do not count untracked files when checking for repository cleanliness
        lines = [line for line in lines if line and line[:2] != '??']
        if lines:
            raise RuntimeError('Repository not clean')

    def commit_git(self, commit_message: str) -> None:
        """Create a git commit of all changed files"""
        self.log(commit_message)
        command = ['git', 'commit', '-am', commit_message]
        self.execute_shell(command, False)

    def commit_dependency_update(self, dependency: str, version: str) -> None:
        """Create a commit with a dependency update"""
        commit_message = COMMIT_MESSAGE.format(
            language=self.language,
            package=dependency,
            version=version,
        )
        self.commit_git(commit_message)

    def create_branch(self) -> None:
        """Create a new branch for committing dependency updates"""
        # Make sure branch does not already exist
        command = ['git', 'branch', '--list', BRANCH_NAME]
        result = self.execute_shell(command, True)
        output = result.stdout
        if output.strip() != '':
            command = ['git', 'checkout', BRANCH_NAME]
            self.branch_exists = True
        else:
            command = ['git', 'checkout', '-b', BRANCH_NAME]
        self.execute_shell(command, False)

    def rollback_branch(self) -> None:
        """Delete the dependency update branch"""
        if self.branch_exists:
            return
        command = ['git', 'checkout', '-']
        self.execute_shell(command, False)
        command = ['git', 'branch', '-d', BRANCH_NAME]
        self.execute_shell(command, False)

    def reset_changes(self) -> None:
        """Reset any noncommitted changes to the branch"""
        command = ['git', 'checkout', '.']
        self.execute_shell(command, False)

    def push_dependency_update(self) -> None:
        """Git push any commits to remote"""
        if not self.push:
            return
        self.log('Pushing commit to git remote')
        command = ['git', 'push', '-u', 'origin']
        self.execute_shell(command, False)

    def compare_versions(self, current: str, proposed: str) -> bool:
        """
        Take the current version and a proposed new version and return a bool
        for whether the new version is a valid upgrade.  The new version is a
        valid upgrade if the version structure matches and the version numbers
        are greater.
        """
        structure_regex = r"[0-9]+"
        current_structure = re.sub(structure_regex, "", current)
        proposed_structure = re.sub(structure_regex, "", proposed)
        if current_structure != proposed_structure:
            return False
        num_regex = r"(\.|^)([0-9]+)(?![a-zA-Z])"
        current_nums = [found[1] for found in re.findall(num_regex, current)]
        proposed_nums = [found[1] for found in re.findall(num_regex, proposed)]
        for compares in zip(current_nums, proposed_nums):
            if int(compares[0]) < int(compares[1]):
                return True
        return False

    def check_major_version_update(
        self, dependency: str, old_version: str, new_version: str
    ) -> Optional[bool]:
        """
        Try to parse versions as semver and compare major version numbers.
        Log a warning if the major version numbers are different.
        Returns True if there is a major version bump
        Returns False if there is not a major version bump
        Returns None if versions are not semver
        """
        old_version_parsed = old_version.lstrip('^~ ').split('.')
        new_version_parsed = new_version.lstrip('^~ ').split('.')
        if len(old_version_parsed) != 3 or len(new_version_parsed) != 3:
            return None
        try:
            old_version_major = int(old_version_parsed[0])
        except ValueError:
            return None
        try:
            new_version_major = int(new_version_parsed[0])
        except ValueError:
            return None
        if old_version_major == new_version_major:
            return False
        self.warn(
            'Warning: Major version change on %s: %s updated to %s'
            % (dependency, old_version, new_version)
        )
        return True

    def execute_shell(
        self,
        command: list[str],
        readonly: bool,
        cwd: Optional[Path] = None,
        suppress_output: bool = False,
        ignore_exit_code: bool = False,
    ) -> SubprocessOutput:
        """Helper method to execute commands in a shell and return output"""
        if self.verbose:
            self.log(' '.join(command))
        if self.dry_run and not readonly:
            return subprocess.CompletedProcess(
                command, 0, stdout='', stderr=''
            )
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                check=True,
                encoding='utf-8',
            )
        except subprocess.CalledProcessError as error:
            if ignore_exit_code:
                return error
            if not suppress_output:
                self.log(error.stdout)
                self.warn(error.stderr)
            raise
        return result

    @staticmethod
    def is_no_color() -> bool:
        """Return if output should have no color: https://no-color.org/"""
        return 'NO_COLOR' in os.environ

    def warn(self, data: str) -> None:
        """Helper method for warn-level logs"""
        if not Util.is_no_color():
            data = f'\033[93m{data}\033[0m'
        return self.log(data)

    def log(self, data: str) -> None:
        """Helper method for taking care of logging statements"""
        print(data)
