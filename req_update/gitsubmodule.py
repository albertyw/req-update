from __future__ import annotations

import datetime
from pathlib import Path
import re
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
        submodules = self.get_submodule_info()
        for submodule in submodules:
            # Get submodule remote info
            submodule = self.annotate_submodule(submodule)
            # Checkout submodule to a remote version
            self.update_submodule(submodule)
            # Commit submodule update
        return False

    # TODO: Make this a method on Submodule
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

    def annotate_submodule(self, submodule: Submodule) -> Submodule:
        command = ["git", "fetch"]
        self.util.execute_shell(command, True, cwd=submodule.path)
        submodule.remote_commit = self.get_remote_commit(submodule)
        submodule.remote_tag = self.get_remote_tag(submodule)
        return submodule

    def get_remote_commit(self, submodule: Submodule) -> VersionInfo:
        command = [
            "git",
            "show",
            "origin",
            "--date=iso-strict",
            "--quiet",
            "--format=%H%n%d%n%cd",
        ]
        result = self.util.execute_shell(command, True, cwd=submodule.path)
        return GitSubmodule.get_version_info(result.stdout)

    def get_remote_tag(self, submodule: Submodule) -> Optional[VersionInfo]:
        command = ["git", "tag"]
        result = self.util.execute_shell(command, True, cwd=submodule.path)
        if not result.stdout.strip():
            return None
        tag = result.stdout.strip().split("\n")[-1]
        command = [
            "git",
            "show",
            tag,
            "--date=iso-strict",
            "--quiet",
            "--format=%H%n%d%n%cd",
        ]
        result = self.util.execute_shell(command, True, cwd=submodule.path)
        return GitSubmodule.get_version_info(result.stdout)

    @staticmethod
    def get_version_info(commit: str) -> VersionInfo:
        lines = commit.strip().split("\n")
        commit_search = re.search(r"tag: ([v0-9\.]+)", lines[1])
        if commit_search:
            version_name = commit_search.group(1)
        else:
            version_name = lines[0]
        version_date_raw = lines[2]
        version_date = datetime.datetime.fromisoformat(version_date_raw)
        version_info = VersionInfo(
            version_name=version_name,
            version_date=version_date,
        )
        return version_info

    def update_submodule(self, submodule: Submodule) -> Optional[str]:
        if not submodule.remote_tag and not submodule.remote_commit:
            return None
        version = ""
        if submodule.remote_tag and submodule.remote_commit:
            if (
                submodule.remote_tag.version_date + datetime.timedelta(days=30)
                > submodule.remote_commit.version_date
            ):
                version = submodule.remote_tag.version_name
            else:
                version = submodule.remote_commit.version_name
        elif submodule.remote_commit:
            version = submodule.remote_commit.version_name
        elif submodule.remote_tag:
            version = submodule.remote_tag.version_name
        command = ["git", "checkout", version]
        self.util.execute_shell(command, False, cwd=submodule.path)
        return version


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
