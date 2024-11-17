from __future__ import annotations

import json
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from req_update.docker import Docker


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
        request = Request(url)
        for key, value in GITHUB_API_HEADERS.items():
            request.add_header(key, value)
        self.util.debug('Checking github tags for %s' % dependency)
        try:
            response = urlopen(request)
        except HTTPError:
            self.util.warn('Cannot read %s from api.github.com' % dependency)
            return ''
        if not response or int(response.status/100) != 2:
            self.util.warn('Cannot read %s from api.github.com' % dependency)
            return ''
        try:
            tags = json.loads(response.read())
        except json.JSONDecodeError:
            self.util.warn('Cannot read %s from api.github.com' % dependency)
            return ''
        try:
            tag = tags[-1]['ref'].removeprefix('refs/tags/')
        except (IndexError, KeyError):
            return ''
        if self.util.compare_versions(original_version, tag):
            self.util.debug(
                'Found update for %s from %s to %s' %
                    (dependency, original_version, tag),
            )
            return str(tag)
        else:
            self.util.debug(
                'No updates found for %s at %s' % (dependency, original_version),
            )
            return ''
