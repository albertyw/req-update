from __future__ import annotations
import os

from req_update.util import Updater


class Docker(Updater):
    def check_applicable(self) -> bool:
        return 'Dockerfile' in os.listdir('.')

    def update_dependencies(self) -> bool:
        """
        Update dependencies
        Return if updates were made
        """
        dockerfile_lines = self.read_dockerfile()
        updates = False
        for i in range(len(dockerfile_lines)):
            line = dockerfile_lines[i]
            new_line = self.attempt_update_image(line)
            if new_line == line:
                continue
            updates = True
            dockerfile_lines[i] = line
            self.util.log('Updating dockerfile %s to %s' % (line, new_line))
            self.commit_dockerfile(dockerfile_lines)
        if not updates:
            self.util.warn('No dockerfile updates')
        return updates

    def read_dockerfile(self) -> list[str]:
        return []

    def attempt_update_image(self, line: str) -> str:
        return line

    def commit_dockerfile(self, dockerfile: list[str]) -> None:
        return
