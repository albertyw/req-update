from __future__ import annotations
import subprocess
from typing import List, Optional


COMMIT_MESSAGE = 'Update {package} package to {version}'


class Util():
    def __init__(self) -> None:
        self.push = False
        self.verbose = False
        self.dry_run = True

    def commit_dependency_update(self, dependency: str, version: str) -> None:
        """ Create a commit with a dependency update """
        commit_message = COMMIT_MESSAGE.format(
            package=dependency,
            version=version,
        )
        self.log(commit_message)
        command = ['git', 'commit', '-am', commit_message]
        self.execute_shell(command, False)

    def push_dependency_update(self) -> None:
        """ Git push any commits to remote """
        if not self.push:
            return
        self.log("Pushing commit to git remote")
        command = ['git', 'push', '-u', 'origin']
        self.execute_shell(command, False)

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
        old_version_parsed = old_version.split('.')
        new_version_parsed = new_version.split('.')
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
        self.log(
            'Warning: Major version change on %s: %s updated to %s'
            % (dependency, old_version, new_version)
        )
        return True

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
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=True,
                encoding='utf-8',
            )
        except subprocess.CalledProcessError as error:
            self.log(error.stdout)
            self.log(error.stderr)
            raise
        return result

    def log(self, data: str) -> None:
        """ Helper method for taking care of logging statements """
        print(data)
