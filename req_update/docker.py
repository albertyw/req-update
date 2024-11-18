from __future__ import annotations
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError

from req_update.util import Updater, Util


class Docker(Updater):
    UPDATE_FILE = re.compile(r'Dockerfile$')
    LINE_HEADER = 'FROM'
    DEPENDENCY_VERSION_SEPARATOR = ':'

    def __init__(self, util: Util) -> None:
        super().__init__(util)
        # Cache of known versions for each dependency
        # This is required because hub.docker.com's APIs are limited to 100 items
        self.known_versions: dict[str, set[str]] = {}

    def check_applicable(self) -> bool:
        return len(self.get_update_files()) > 0

    def get_update_files(self) -> list[Path]:
        command = ['git', 'ls-files']
        try:
            shell = self.util.execute_shell(command, True)
        except subprocess.CalledProcessError:
            return []
        files = [Path(f) for f in shell.stdout.split('\n')]
        files = [f for f in files if self.UPDATE_FILE.match(str(f))]
        return files

    def update_dependencies(self) -> bool:
        """
        Update dependencies
        Return if updates were made
        """
        update_files = self.get_update_files()
        updates = False
        for f in update_files:
            update = self.update_dependencies_file(f)
            if update:
                updates = True
        return updates

    def update_dependencies_file(self, update_file: Path) -> bool:
        dockerfile_lines = self.read_update_file(update_file)
        updates = False
        for i in range(len(dockerfile_lines)):
            line = dockerfile_lines[i]
            new_line, dependency, version = self.attempt_update_image(line)
            if not dependency or not version:
                continue
            updates = True
            dockerfile_lines[i] = new_line
            self.commit_dockerfile(update_file, dockerfile_lines, dependency, version)
        return updates

    def read_update_file(self, update_file: Path) -> list[str]:
        with open(update_file, 'r') as handle:
            lines = handle.readlines()
        lines = [line.strip('\n') for line in lines]
        return lines

    def attempt_update_image(self, line: str) -> tuple[str, str, str]:
        if not line.strip().startswith(self.LINE_HEADER):
            return line, '', ''
        base_image = line.split()[1]
        if base_image.count(self.DEPENDENCY_VERSION_SEPARATOR) != 1:
            return line, base_image, ''
        dependency = base_image.split(self.DEPENDENCY_VERSION_SEPARATOR)[0]
        version = base_image.split(self.DEPENDENCY_VERSION_SEPARATOR)[1]
        new_version = self.find_updated_version(dependency, version)
        if new_version:
            line = line.replace(
                self.DEPENDENCY_VERSION_SEPARATOR + version,
                self.DEPENDENCY_VERSION_SEPARATOR + new_version,
            )
        return line, dependency, new_version

    def find_updated_version(self, dependency: str, original_version: str) -> str:
        if original_version == 'latest':
            self.util.warn('Cannot update docker image when using "latest"')
            return ''
        known_versions = self.known_versions.get(dependency, set())
        known_versions.add(original_version)
        self.known_versions[dependency] = known_versions
        if dependency.count('/') == 1:
            namespace = dependency.split('/')[0]
            dependency_name = dependency.split('/')[1]
        else:
            namespace = 'library'
            dependency_name = dependency
        # Both seem to work:
        # https://registry.hub.docker.com/api/content/v1/repositories/public/library/debian/tags
        # https://hub.docker.com/v2/repositories/library/debian/tags
        # Documentation: https://docs.docker.com/reference/api/hub/latest/#tag/repositories/paths/
        url = (
            'https://hub.docker.com/'
            'v2/repositories/%s/%s/tags?page_size=100'
            % (namespace, dependency_name)
        )
        try:
            data = self.util.cached_request(url, {})
        except HTTPError:
            self.util.warn('Cannot read %s from hub.docker.com' % dependency)
            return ''
        try:
            available_versions = [tag['name'] for tag in data['results']]
        except (IndexError, KeyError):
            self.util.warn('Cannot read %s from hub.docker.com' % dependency)
            return ''
        new_version = original_version
        for version in available_versions + list(known_versions):
            if self.util.compare_versions(new_version, version):
                new_version = version
        if new_version == original_version:
            self.util.debug(
                'No updates found for %s at %s' %
                    (dependency, original_version),
            )
            return ''
        else:
            self.util.debug(
                'Found update for %s from %s to %s' %
                    (dependency, original_version, new_version),
            )
            return new_version

    def commit_dockerfile(self,
        update_file: Path,
        dockerfile: list[str],
        dependency: str,
        version: str,
    ) -> None:
        if not self.util.dry_run:
            with open(update_file, 'w') as handle:
                handle.write('\n'.join(dockerfile))
        self.util.commit_dependency_update(self.language, dependency, version)
