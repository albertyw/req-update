from __future__ import annotations

import re

from req_update.docker import Docker


class GithubWorkflow(Docker):
    UPDATE_FILE = re.compile(r'^\.github/workflows/.+\.yml$')
    LINE_HEADER = 'uses:'
    DEPENDENCY_VERSION_SEPARATOR = '@'
