"""JSON-only command-line parsing helpers."""

from __future__ import annotations

import argparse
from typing import NoReturn


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise ValueError(message)
