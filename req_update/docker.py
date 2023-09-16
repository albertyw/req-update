from __future__ import annotations
import json
import os
from urllib import request

from req_update.util import Updater


# TODO - support .drone.yml files
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
            self.commit_dockerfile(dockerfile_lines, dependency, version)
        if not updates:
            self.util.warn('No dockerfile updates')
        return updates

    def read_dockerfile(self) -> list[str]:
        with open('Dockerfile', 'r') as handle:
            lines = handle.readlines()
        lines = [line.strip('\n') for line in lines]
        return lines

    def attempt_update_image(self, line: str) -> tuple[str, str, str]:
        if not line.strip().startswith('FROM'):
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

    def find_updated_version(self, dependency: str, original_version: str) -> str:
        if original_version == 'latest':
            self.util.warn('Cannot update docker image when using "latest"')
            return ''
        if dependency.count('/') == 1:
            namespace = dependency.split('/')[0]
            dependency_name = dependency.split('/')[1]
        else:
            namespace = 'library'
            dependency_name = dependency
        # Both seem to work:
        # https://registry.hub.docker.com/api/content/v1/repositories/public/library/debian/tags
        # https://hub.docker.com/v2/repositories/library/debian/tags
        url = (
            'https://registry.hub.docker.com/api'
            '/content/v1/repositories/public/%s/%s/tags?page_size=500'
            % (namespace, dependency_name)
        )
        response = request.urlopen(url)
        if int(response.status/100) != 2:
            self.util.warn('Cannot read %s from hub.docker.com' % dependency)
            return ''
        data = json.loads(response.read())
        available_versions = [tag['name'] for tag in data['results']]
        new_version = original_version
        for version in available_versions:
            if self.util.compare_versions(new_version, version):
                new_version = version
        if new_version == original_version:
            return ''
        else:
            return new_version

    def commit_dockerfile(self,
        dockerfile: list[str],
        dependency: str,
        version: str
    ) -> None:
        if not self.util.dry_run:
            with open('Dockerfile', 'w') as handle:
                handle.write('\n'.join(dockerfile))
        self.util.commit_dependency_update(self.language, dependency, version)
