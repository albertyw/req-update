from __future__ import annotations
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import util  # NOQA


class Go:
    def __init__(self) -> None:
        self.util = util.Util()

    def check_applicable(self) -> bool:
        raise NotImplementedError()

    def update_install_dependencies(self) -> bool:
        """
        Update dependencies and install updates
        Return if updates were made
        """
        raise NotImplementedError()
