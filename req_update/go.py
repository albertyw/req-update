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
        self.util.info('Updating go packages')
        self.util.execute_shell(command, False)
        command = ['go', 'mod', 'tidy']
        self.util.info('Tidying go packages')
        self.util.execute_shell(command, False)
        clean = self.util.check_repository_cleanliness()
        if not clean:
            self.util.commit_git('Update go packages')
        return not clean
