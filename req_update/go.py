from __future__ import annotations
import os
import subprocess

from req_update.util import Updater


class Go(Updater):
    def check_applicable(self) -> bool:
        command = ['which', 'go']
        try:
            self.util.execute_shell(command, True, suppress_output=True)
        except subprocess.CalledProcessError:
            # Cannot find go
            return False
        files = os.listdir('.')
        if 'go.mod' not in files or 'go.sum' not in files:
            # Cannot find go modules files
            return False
        return True

    def update_dependencies(self) -> bool:
        """
        Update dependencies
        Return if updates were made
        """
        command = ['go', 'get', '-u', 'all']
        self.util.log('Updating go packages')
        self.util.execute_shell(command, False)
        command = ['go', 'mod', 'tidy']
        self.util.log('Tidying go packages')
        self.util.execute_shell(command, False)
        try:
            self.util.check_repository_cleanliness()
            self.util.warn('No go updates')
            return False  # repository is clean so nothing to commit or push
        except RuntimeError:
            self.util.commit_git('Update go packages')
            self.util.push_dependency_update()
            return True
