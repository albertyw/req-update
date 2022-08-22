import datetime
from pathlib import Path
import subprocess
from typing import NamedTuple, Optional

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


# TODO: After python 3.7 support is dropped, switch this to a TypedDict
class Submodule:
    def __init__(self, path: Path) -> None:
        self.path: Path = path
        self.remote_tag: Optional[VersionInfo] = None
        self.remote_commit: Optional[VersionInfo] = None


# TODO: After python 3.7 support is dropped, switch this to a TypedDict
class VersionInfo(NamedTuple):
    version_name: str
    version_date: datetime.datetime
