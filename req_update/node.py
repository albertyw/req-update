from __future__ import annotations
import os
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import util  # NOQA


class Node():
    def __init__(self) -> None:
        self.util = util.Util()

    def check_applicable(self) -> bool:
        command = ['which', 'npm']
        try:
            self.util.execute_shell(
                command, True, suppress_output=True
            )
        except subprocess.CalledProcessError:
            # Cannot find npm
            return False
        files = os.listdir('.')
        if 'package.json' not in files or 'package-lock.json' not in files:
            # Cannot find npm config files
            return False
        return True

    def update_install_dependencies(self) -> bool:
        """
        Update dependencies and install updates
        Return if updates were made
        """
        command = ['npm', 'update']
        self.util.execute_shell(command, False)
        try:
            self.util.check_repository_cleanliness()
            return False  # repository is clean so nothing to commit or push
        except RuntimeError:
            self.util.commit_git('Update npm packages')
            self.util.push_dependency_update()
            return True
