from __future__ import annotations
import os
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import util  # NOQA


class Go:
    def __init__(self) -> None:
        self.util = util.Util()

    def check_applicable(self) -> bool:
        command = ["which", "go"]
        try:
            self.util.execute_shell(command, True, suppress_output=True)
        except subprocess.CalledProcessError:
            # Cannot find go
            return False
        files = os.listdir(".")
        if "go.mod" not in files or "go.sum" not in files:
            # Cannot find go modules files
            return False
        return True

    def update_install_dependencies(self) -> bool:
        """
        Update dependencies and install updates
        Return if updates were made
        """
        raise NotImplementedError()
