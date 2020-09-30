import subprocess
from typing import List


def main() -> None:
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
