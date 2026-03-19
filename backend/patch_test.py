import argparse
import difflib
from pathlib import Path
from typing import Iterable, List, Optional


def compute_unified_diff(
    before: str,
    after: str,
    fromfile: str = "before",
    tofile: str = "after",
) -> str:
    """
    Compute a unified diff between two strings.

    This helper can be imported by tests or other code that needs to
    assert how a "patch" changes some text content.
    """
    before_lines: List[str] = before.splitlines(keepends=True)
    after_lines: List[str] = after.splitlines(keepends=True)

    diff_lines: Iterable[str] = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=fromfile,
        tofile=tofile,
    )

    return "".join(diff_lines)


def run_patch_test(path_before: Path, path_after: Path) -> str:
    """
    Read two text files and return their unified diff as a string.

    The diff is empty when the files are identical.
    """
    before_text = path_before.read_text(encoding="utf-8")
    after_text = path_after.read_text(encoding="utf-8")
    return compute_unified_diff(
        before_text,
        after_text,
        fromfile=str(path_before),
        tofile=str(path_after),
    )


def main(argv: Optional[List[str]] = None) -> int:
    """
    Command-line entry point for running a simple "patch test".

    Usage:
        python -m backend.patch_test BEFORE_FILE AFTER_FILE

    Exits with code 0 when the files are identical, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Compute a unified diff between two text files.",
    )
    parser.add_argument(
        "before",
        type=Path,
        help="Path to the 'before' file.",
    )
    parser.add_argument(
        "after",
        type=Path,
        help="Path to the 'after' file.",
    )

    args = parser.parse_args(argv)

    diff = run_patch_test(args.before, args.after)

    if diff:
        print(diff, end="")
        return 1

    print("No differences found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())