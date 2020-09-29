import subprocess


def main():
    pass


def execute_shell(command):
    result = subprocess.run(
        command,
        capture_output=True,
    )
    result.check_returncode()
    return result


if __name__ == '__main__':
    main()
