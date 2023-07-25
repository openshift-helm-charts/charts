# -*- coding: utf-8 -*-
"""Sets the cwd within the context.

Reference: https://dev.to/teckert/changing-directory-with-a-python-context-manager-2bj8
"""

import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SetDirectory(object):
    """
    Args:
        path (Path): The path to the cwd
    """
    path: Path
    origin: Path = Path().absolute()

    def __enter__(self):
        os.chdir(self.path)
    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.origin)
