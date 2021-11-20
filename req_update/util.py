from __future__ import annotations
import subprocess
from typing import List


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
