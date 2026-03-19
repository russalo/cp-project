"""
Simple scaffold for the `check_unfold` backend check.

This module can be run as a script or imported and its `run_check` function
called programmatically. At the moment it only implements a no-op check, but
it is structured so that real validation logic can be added without changing
the public interface.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, List, Optional


def run_check(argv: Optional[Iterable[str]] = None) -> int:
    """
    Entry point for the `check_unfold` verification.

    Parameters
    ----------
    argv:
        Optional iterable of command-line arguments (excluding the program
        name). If omitted or ``None``, arguments are taken from
        :data:`sys.argv`.

    Returns
    -------
    int
        Process exit code: ``0`` for success, non-zero for failure.
    """

    parser = argparse.ArgumentParser(
        prog="check_unfold",
        description=(
            "Run the 'check_unfold' backend validation. "
            "Currently this is a no-op scaffold; real checks should be "
            "implemented here."
        ),
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Reserved for future use to enable strict unfold checks.",
    )

    # Convert argv to a list so argparse can consume it; default to sys.argv[1:].
    args: argparse.Namespace
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(list(argv))

    # Placeholder for actual check logic.
    # TODO: implement real checks and return a non-zero exit code on failure.
    _ = args  # avoid 'unused variable' warnings for now

    return 0


if __name__ == "__main__":
    raise SystemExit(run_check())