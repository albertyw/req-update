from __future__ import annotations

import json
import re

from req_update.docker import Docker
from req_update.util import HTTPError


GITHUB_API_HEADERS = {
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
}


class GithubWorkflow(Docker):
    UPDATE_FILE = re.compile(r'^\.github/workflows/.+\.yml$')
    LINE_HEADER = 'uses:'
    DEPENDENCY_VERSION_SEPARATOR = '@'

    def find_updated_version(self, dependency: str, original_version: str) -> str:
        url = 'https://api.github.com/repos/%s/git/refs/tags' % dependency
        self.util.debug('Checking github tags for %s' % dependency)
        try:
            tags = self.util.cached_request(url, GITHUB_API_HEADERS)
        except (HTTPError, json.JSONDecodeError) as e:
            self.util.warn(
                'Cannot read %s from api.github.com: %s' % (dependency, str(e)),
            )
            return ''

        available_versions = [tag['ref'].removeprefix('refs/tags/') for tag in tags]
        most_recent = original_version
        for version in available_versions:
            if self.util.compare_versions(most_recent, version):
                most_recent = version
        if most_recent != original_version:
            self.util.debug(
                'Found update for %s from %s to %s' %
                    (dependency, original_version, most_recent),
            )
            return str(most_recent)
        else:
            self.util.debug(
                'No updates found for %s at %s' % (dependency, original_version),
            )
            return ''
