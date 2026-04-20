from __future__ import annotations

import re

from req_update.docker import Docker


class Drone(Docker):
    UPDATE_FILE = re.compile(r'^\.drone\.ya?ml$')
    LINE_HEADERS = ['image:']
