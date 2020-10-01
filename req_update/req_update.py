from __future__ import annotations
import subprocess
from typing import List, Tuple


def main() -> None:
    """ Update all dependencies """
    check_repository_cleanliness()
    create_branch()
    update_dependencies()


def check_repository_cleanliness() -> None:
    """ Check that the repository is ready for updating dependencies """
    pass


def create_branch() -> None:
    """ Create a new branch for committing dependency updates """
    pass


def update_dependencies() -> None:
    """ Update and commit a list of dependency updates """
    pass


def get_pip_outdated() -> List[Tuple[str, str]]:
    """ Get a list of outdated pip packages """
    pass


def write_dependency_update(dependency: str, version: str) -> None:
    """ Given a dependency, update it to a given version """
    pass


def commit_dependency_update(dependency: str, version: str) -> None:
    """ Create a commit with a dependency update """
    pass


def execute_shell(command: List[str]) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        command,
        capture_output=True,
    )
    result.check_returncode()
    return result


if __name__ == '__main__':
    main()
