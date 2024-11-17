from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Optional, Union
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BRANCH_NAME = 'dep-update'
COMMIT_MESSAGE = 'Update {language} {package} package to {version}'
SubprocessOutput = Union[
    subprocess.CalledProcessError,
    subprocess.CompletedProcess[str],
]


class Updater:
    def __init__(self, util: Util) -> None:
        self.util = util

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

    @property
    def language(self) -> str:
        """
        Return the name of the language being updated
        """
        return type(self).__name__


class Util:
    def __init__(self) -> None:
        self.push = False
        self.verbose = False
        self.ignore_cleanliness = True
        self.dry_run = True
        self.branch_exists = False
        self.request_cache: dict[str, Any] = {}

    def check_repository_cleanliness(self) -> bool:
        """
        Check that the repository is ready for updating dependencies.
        Returns a bool for if a repository is clean.
        Raises a runtimeError if not being run within a git repository.
        """
        # Make sure there are no uncommitted files
        if self.dry_run:
            return True
        command = ['git', 'status', '--porcelain']
        try:
            result = self.execute_shell(command, True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError('Must run within a git repository') from error
        lines = result.stdout.split('\n')
        # Do not count untracked files when checking for repository cleanliness
        lines = [line for line in lines if line and line[:2] != '??']
        return len(lines) == 0

    def commit_git(self, commit_message: str) -> None:
        """Create a git commit of all changed files"""
        self.info(commit_message)
        command = ['git', 'commit', '-am', commit_message]
        self.execute_shell(command, False)
        self.push_dependency_update()

    def commit_dependency_update(
        self, language: str, dependency: str, version: str,
    ) -> None:
        """Create a commit with a dependency update"""
        commit_message = COMMIT_MESSAGE.format(
            language=language,
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
        self.info('Pushing commit to git remote')
        command = ['git', 'push', '-u', 'origin']
        self.execute_shell(command, False)

    def compare_versions(self, current: str, proposed: str) -> bool:
        """
        Take the current version and a proposed new version and return a bool
        for whether the new version is a valid upgrade.  The new version is a
        valid upgrade if the version structure matches and the version numbers
        are greater.
        """
        structure_regex = re.compile(r"[0-9]+")
        current_structure = structure_regex.sub("", current)
        proposed_structure = structure_regex.sub("", proposed)
        if current_structure != proposed_structure:
            return False
        num_regex = re.compile(r"\d+")
        current_nums = num_regex.findall(current)
        proposed_nums = num_regex.findall(proposed)
        for compares in zip(current_nums, proposed_nums):
            if int(compares[0]) < int(compares[1]):
                return True
            if int(compares[0]) > int(compares[1]):
                return False
        return False

    def check_major_version_update(
        self, dependency: str, old_version: str, new_version: str,
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
            % (dependency, old_version, new_version),
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
        self.debug(' '.join(command))
        if self.dry_run and not readonly:
            return subprocess.CompletedProcess(
                command, 0, stdout='', stderr='',
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
                self.info(error.stdout)
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
            data = f'\033[93m{data}\033[0m'  # color text yellow
        return self._log(data)

    def info(self, data: str) -> None:
        """Helper method for debug-level logs"""
        return self._log(data)

    def debug(self, data: str) -> None:
        """Helper method for debug-level logs"""
        if not self.verbose:
            return
        if not Util.is_no_color():
            data = f'\033[37m{data}\033[0m'  # color text gray
        return self._log(data)

    def _log(self, data: str) -> None:
        """Helper method for taking care of logging statements"""
        print(data)

    def cached_request(self, url: str, headers: dict[str, str]) -> Any:
        """
        Makes an HTTP request given a URL and headers, returns the json-parsed result
        Caches the results based on URL
        """
        if url in self.request_cache:
            return self.request_cache[url]
        request = Request(url)
        for key, value in headers.items():
            request.add_header(key, value)
        self.debug('Checking %s' % url)
        response = urlopen(request)
        if int(response.status/100) != 2:
            raise HTTPError(
                url,
                response.status,
                'Error status',
                response.getheaders(),
                None,
                )
        result = json.loads(response.read())
        self.request_cache[url] = result
        return result
