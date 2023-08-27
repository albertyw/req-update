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
            new_line, dependency, version = self.attempt_update_image(line)
            if not dependency or not version:
                continue
            updates = True
            dockerfile_lines[i] = new_line
            self.util.log('Updating dockerfile %s to %s' % (dependency, version))
            self.commit_dockerfile(dockerfile_lines, dependency, version)
        if not updates:
            self.util.warn('No dockerfile updates')
        return updates

    def read_dockerfile(self) -> list[str]:
        with open('Dockerfile', 'r') as handle:
            lines = handle.readlines()
        lines = [line.strip() for line in lines]
        return lines

    def attempt_update_image(self, line: str) -> tuple[str, str, str]:
        if not line.startswith('FROM'):
            return line, '', ''
        base_image = line.split()[1]
        if base_image.count(':') != 1:
            return line, base_image, ''
        dependency = base_image.split(':')[0]
        version = base_image.split(':')[1]
        return line, dependency, version

    def commit_dockerfile(self,
        dockerfile: list[str],
        dependency: str,
        version: str
    ) -> None:
        with open('Dockerfile', 'w') as handle:
            handle.write('\n'.join(dockerfile))
        self.util.commit_dependency_update(dependency, version)
