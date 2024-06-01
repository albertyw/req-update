from __future__ import annotations

import re

from req_update.docker import Docker


class Drone(Docker):
    UPDATE_FILE = re.compile(r'^\.drone\.yml$')
    LINE_HEADER = 'image:'
