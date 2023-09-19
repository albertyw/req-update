from __future__ import annotations

from req_update.docker import Docker


class Drone(Docker):
    UPDATE_FILE = '.drone.yml'
    LINE_HEADER = 'image:'

    def update_dependencies(self) -> bool:
        """
        Update dependencies
        Return if updates were made
        """
        drone_lines = self.read_update_file()
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

    def commit_drone(self,
        drone_lines: list[str],
        dependency: str,
        version: str
    ) -> None:
        if not self.util.dry_run:
            with open(self.UPDATE_FILE, 'w') as handle:
                handle.write('\n'.join(drone_lines))
        self.util.commit_dependency_update(self.language, dependency, version)
