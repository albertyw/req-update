import subprocess

from req_update.util import Updater


class GitSubmodule(Updater):
    def check_applicable(self) -> bool:
        command = ["git", "submodule"]
        try:
            result = self.util.execute_shell(
                command,
                True,
                suppress_output=True,
            )
        except subprocess.CalledProcessError:
            return False
        return len(result.stdout) > 0
