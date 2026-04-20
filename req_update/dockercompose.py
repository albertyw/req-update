from __future__ import annotations

import re

from req_update.docker import Docker


class DockerCompose(Docker):
    UPDATE_FILE = re.compile(
        r'(^|/)(docker-)?compose(\.[^/]+)?\.ya?ml$',
    )
    LINE_HEADERS = ['image:', '- image:']
