from __future__ import annotations

import datetime
from pathlib import Path
import subprocess
from typing import List, NamedTuple, Optional

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

    def update_dependencies(self) -> bool:
        # Get a list of submodules and their versions
        submodules = self.get_submodule_info()  # NOQA
        # Get submodule remote info
        # Checkout submodule to a remote version
        # Commit submodule update
        return False

    def get_submodule_info(self) -> List[Submodule]:
        command = ["git", "submodule"]
        result = self.util.execute_shell(command, True)
        submodules: List[Submodule] = []
        for line in result.stdout.split("\n"):
            if not line:
                continue
            location = Path(line.strip().split(" ")[1])
            submodule = Submodule(path=location)
            submodules.append(submodule)
        return submodules


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
