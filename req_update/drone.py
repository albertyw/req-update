from __future__ import annotations
import os

from req_update.docker import Docker


class Drone(Docker):
    def check_applicable(self) -> bool:
        return '.drone.yml' in os.listdir('.')

    def update_dependencies(self) -> bool:
        """
        Update dependencies
        Return if updates were made
        """
        drone_lines = self.read_drone()
        updates = False
        for i in range(len(drone_lines)):
            line = drone_lines[i]
            new_line, dependency, version = self.attempt_update_image(line)
            if not dependency or not version:
                continue
            updates = True
            drone_lines[i] = new_line
            self.commit_drone(drone_lines, dependency, version)
        if not updates:
            self.util.warn('No %s updates' % self.language)
        return updates

    def read_drone(self) -> list[str]:
        with open('.drone.yml', 'r') as handle:
            lines = handle.readlines()
        lines = [line.strip('\n') for line in lines]
        return lines

    def attempt_update_image(self, line: str) -> tuple[str, str, str]:
        if not line.strip().startswith('image:'):
            return line, '', ''
        base_image = line.split()[1]
        if base_image.count(':') != 1:
            return line, base_image, ''
        dependency = base_image.split(':')[0]
        version = base_image.split(':')[1]
        new_version = self.find_updated_version(dependency, version)
        if new_version:
            line = line.replace(':' + version, ':' + new_version)
        return line, dependency, new_version

    def commit_drone(self,
        drone_lines: list[str],
        dependency: str,
        version: str
    ) -> None:
        if not self.util.dry_run:
            with open('.drone.yml', 'w') as handle:
                handle.write('\n'.join(drone_lines))
        self.util.commit_dependency_update(self.language, dependency, version)
