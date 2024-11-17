from __future__ import annotations
import json
import os
import re
import subprocess
from typing import TYPE_CHECKING, cast

from req_update.util import Updater


# Copied and simplified from
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
SEMVER = re.compile(r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$')  # NOQA


class Node(Updater):
    def check_applicable(self) -> bool:
        command = ['which', 'npm']
        try:
            self.util.execute_shell(command, True, suppress_output=True)
        except subprocess.CalledProcessError:
            # Cannot find npm
            return False
        files = os.listdir('.')
        if 'package.json' not in files or 'package-lock.json' not in files:
            # Cannot find npm config files
            return False
        return True

    def update_dependencies(self) -> bool:
        """
        Update dependencies
        Return if updates were made
        """
        updated_unpinned = self.update_unpinned_dependencies()
        updated_pinned = self.update_pinned_dependencies()
        updated = updated_unpinned or updated_pinned
        return updated

    def update_unpinned_dependencies(self) -> bool:
        command = ['npm', 'update']
        self.util.info('Updating npm packages')
        self.util.execute_shell(command, False)
        clean = self.util.check_repository_cleanliness()
        if not clean:
            self.util.commit_git('Update npm packages')
            return True
        return False

    def update_pinned_dependencies(self) -> bool:
        packages = self.get_outdated()
        if not packages:
            return False
        any_updated = False
        for package_name, package in packages.items():
            updated = self.update_package(package_name, package)
            if updated:
                any_updated = True
        return any_updated

    def get_outdated(self) -> dict[str, dict[str, str]]:
        command = ['npm', 'outdated', '--json']
        result = self.util.execute_shell(command, True, ignore_exit_code=True)
        packages = json.loads(result.stdout)
        if TYPE_CHECKING:
            return cast(dict[str, dict[str, str]], packages)
        return packages

    def update_package(
        self, package_name: str, package: dict[str, str],
    ) -> bool:
        self.util.info('Updating dependency: %s' % package_name)
        with open('package.json', 'r') as handle:
            package_json_string = handle.read()
        package_json = json.loads(package_json_string)
        if package_name in package_json.get('dependencies', {}):
            old_version = package_json['dependencies'][package_name]
            package_json['dependencies'] = self.update_package_dependencies(
                package_json['dependencies'],
                package_name,
                package,
            )
            new_version = package_json['dependencies'][package_name]
        elif package_name in package_json.get('devDependencies', {}):
            old_version = package_json['devDependencies'][package_name]
            package_json['devDependencies'] = self.update_package_dependencies(
                package_json['devDependencies'],
                package_name,
                package,
            )
            new_version = package_json['devDependencies'][package_name]
        else:
            return False
        package_json_string = json.dumps(package_json, indent=2)
        package_json_string += '\n'  # Add the traditional EOF newline
        if not self.util.dry_run:
            with open('package.json', 'w') as handle:
                handle.write(package_json_string)
        success = self.install_dependencies()
        if not success:
            self.util.warn(
                'Dependency conflict; rolling back: %s' % package_name,
            )
            self.util.reset_changes()
            return False
        self.util.check_major_version_update(
            package_name, old_version, new_version,
        )
        self.util.commit_dependency_update(self.language, package_name, new_version)
        return True

    def update_package_dependencies(
        self,
        dependencies: dict[str, str],
        package_name: str,
        package: dict[str, str],
    ) -> dict[str, str]:
        new_version = package['latest']
        new_version = Node.generate_package_version(new_version)
        dependencies[package_name] = new_version
        return dependencies

    @staticmethod
    def generate_package_version(version: str) -> str:
        """
        Given a version, generate a version specifier that allows updates
        within the most recent non-zero version for semver versions
        """
        match = SEMVER.match(version)
        if not match:
            return version
        versions = match.groupdict()
        if versions['major'] != '0':
            return '^%s.0.0' % versions['major']
        if versions['minor'] != '0':
            return '^0.%s.0' % versions['minor']
        if versions['patch'] != '0':
            return version
        raise ValueError('Cannot compute version')  # pragma: no cover

    def install_dependencies(self) -> bool:
        command = ['npm', 'install']
        try:
            result = self.util.execute_shell(
                command,
                False,
                suppress_output=True,
            )
            if 'Could not resolve dependency' in result.stderr:
                return False
        except subprocess.CalledProcessError as error:
            if 'Could not resolve dependency' in error.stderr:
                return False
            self.util.info(error.stdout)
            self.util.warn(error.stderr)
            raise
        return True
