from __future__ import annotations

from req_update.docker import Docker


class Drone(Docker):
    UPDATE_FILE = '.drone.yml'
    LINE_HEADER = 'image:'
