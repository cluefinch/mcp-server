"""Validate Developer Certificate of Origin sign-offs for a commit range."""

import re
import subprocess
import sys

_SIGNOFF = re.compile(
    r"^Signed-off-by:\s*(.+?)\s*<([^<>]+)>\s*$", re.IGNORECASE | re.MULTILINE
)


def has_matching_signoff(message: str, author_name: str, author_email: str) -> bool:
    """Return whether a commit message contains the author's DCO sign-off."""
    expected_name = " ".join(author_name.split()).casefold()
    expected_email = author_email.strip().casefold()
    return any(
        " ".join(name.split()).casefold() == expected_name
        and email.strip().casefold() == expected_email
        for name, email in _SIGNOFF.findall(message)
    )


def _commit_metadata(commit: str) -> tuple[str, str, str]:
    output = subprocess.run(
        ["git", "show", "-s", "--format=%an%x00%ae%x00%B", commit],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    name, email, message = output.split("\0", 2)
    return name, email, message


def validate_range(base: str, head: str) -> list[str]:
    """Return commit SHAs in ``base..head`` that lack a matching sign-off."""
    commits = subprocess.run(
        ["git", "rev-list", "--reverse", f"{base}..{head}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    failures: list[str] = []
    for commit in commits:
        name, email, message = _commit_metadata(commit)
        if not has_matching_signoff(message, name, email):
            failures.append(commit)
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check_dco.py <base-sha> <head-sha>", file=sys.stderr)
        return 2
    failures = validate_range(sys.argv[1], sys.argv[2])
    if failures:
        print(
            "DCO sign-off missing or does not match the commit author:", file=sys.stderr
        )
        for commit in failures:
            print(f"  {commit}", file=sys.stderr)
        print(
            "Use `git commit -s` (and rebase/amend affected commits).", file=sys.stderr
        )
        return 1
    print("PASS: all commits in the pull request have matching DCO sign-offs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
