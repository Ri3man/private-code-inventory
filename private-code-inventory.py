#!/usr/bin/env python3
"""Create a local, aggregate Git inventory without exporting code or identities.

Requires Python 3.9+ and Git. Uses only the standard library. No network API,
repository upload, package installation or source-file execution is performed.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

SCHEMA_VERSION = "1.0.0"
DATE_SAMPLE_LIMIT = 100_000
FILE_TYPES = {
    ".py": "Python", ".pyi": "Python", ".js": "JavaScript",
    ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
    ".kt": "Kotlin", ".kts": "Kotlin", ".swift": "Swift",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".c": "C", ".h": "C/C++ headers", ".cc": "C++", ".cpp": "C++",
    ".hpp": "C++", ".cs": "C#", ".vb": "Visual Basic",
    ".cob": "COBOL", ".cbl": "COBOL", ".cpy": "COBOL copybooks",
    ".f": "Fortran", ".f90": "Fortran", ".f95": "Fortran",
    ".erl": "Erlang", ".hrl": "Erlang", ".ex": "Elixir",
    ".exs": "Elixir", ".scala": "Scala", ".sc": "Scala",
    ".r": "R", ".sql": "SQL", ".sh": "Shell", ".ps1": "PowerShell",
    ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".scss": "CSS",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".xml": "XML", ".md": "Documentation", ".rst": "Documentation",
    ".txt": "Text", ".ipynb": "Notebook", ".vue": "Vue", ".svelte": "Svelte",
}


class InventoryError(Exception):
    """A deliberately path-free error suitable for the command-line output."""


def git(path: Path, *args: str, allow_missing: bool = False) -> bytes:
    # Do not let inherited Git-specific variables redirect the target repository
    # or add configuration. Preserve ordinary process settings such as PATH.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    # Avoid credential prompts, lazy remote object fetches, optional writes and
    # user-wide configuration. These are metadata-only Git plumbing operations.
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_NO_LAZY_FETCH": "1",
                "GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat",
                "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    command = ["git", "--no-pager", "--no-replace-objects",
               "-c", "core.fsmonitor=false", "-c", "protocol.allow=never",
               "-C", str(path), *args]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=env,
                                timeout=60, check=False)
    except FileNotFoundError as exc:
        raise InventoryError("Git is not installed or is not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise InventoryError("A metadata command timed out; no report was completed.") from exc
    if result.returncode:
        if allow_missing:
            return b""
        # Git's stderr can contain private paths. Do not copy it into the report.
        raise InventoryError("Git could not read the local repository metadata. Check the repository and permissions.")
    return result.stdout


def utc_date(timestamp: int) -> str:
    try:
        return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return "outside supported date range"


def inspect_repository(path: Path) -> dict:
    if not path.is_dir():
        raise InventoryError("Choose an existing local repository directory.")
    path = path.resolve()
    bare = git(path, "rev-parse", "--is-bare-repository").strip() == b"true"
    root = git(path, "rev-parse", "--absolute-git-dir" if bare else "--show-toplevel")
    # Remove Git's one line terminator, not whitespace that may be part of a path.
    root_path = Path(os.fsdecode(root[:-1] if root.endswith(b"\n") else root)).resolve()
    if root_path != path:
        raise InventoryError("Select the repository root directory, not a subdirectory.")
    shallow = git(path, "rev-parse", "--is-shallow-repository").strip() == b"true"
    count_bytes = git(path, "rev-list", "--all", "--count").strip()
    count = int(count_bytes or b"0")
    timestamps = git(path, "log", "--all", "--no-show-signature", "--no-notes",
                     f"--max-count={DATE_SAMPLE_LIMIT}", "--format=%ct") if count else b""
    dates = [int(t) for t in timestamps.splitlines() if t.strip()]
    has_head = bool(git(path, "rev-parse", "--verify", "HEAD", allow_missing=True))
    tree = git(path, "ls-tree", "-r", "-z", "HEAD") if has_head else b""
    categories: collections.Counter[str] = collections.Counter()
    files = submodules = sensitive_name_signals = 0
    license_document = False
    for record in tree.split(b"\0"):
        if not record:
            continue
        header, raw_name = record.split(b"\t", 1)
        mode, kind, _object_id = header.split(b" ", 2)
        if mode == b"160000" or kind == b"commit":
            submodules += 1
            continue
        name = PurePosixPath(raw_name.decode("utf-8", errors="replace"))
        basename = name.name.lower()
        files += 1
        categories[FILE_TYPES.get(name.suffix.lower(), "Other")] += 1
        if basename in {"license", "licence", "copying", "license.txt", "license.md", "licence.txt", "licence.md"}:
            license_document = True
        if (basename == ".env" or basename.startswith(".env.") or
                basename in {"id_rsa", "id_ed25519", "credentials.json"} or
                name.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}):
            sensitive_name_signals += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "measured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository_label": "local repository",
        "scope": "Aggregate local Git metadata. Not a valuation, ownership decision, security scan or buyer acceptance.",
        "history": {
            "available_reachable_commits": count,
            "is_shallow": shallow,
            "committer_dates_sampled": len(dates),
            "date_range_complete_for_available_history": len(dates) == count,
            "earliest_observed_committer_date": utc_date(min(dates)) if dates else None,
            "latest_observed_committer_date": utc_date(max(dates)) if dates else None,
            "note": "Counts and dates cover locally available reachable commits; a shallow repository omits earlier history. Commit timestamps may be rewritten and do not verify age, authorship or production use.",
        },
        "current_committed_tree": {
            "head_available": has_head,
            "is_bare_repository": bare,
            "tracked_files": files,
            "file_types_by_extension": dict(sorted(categories.items())),
            "submodule_entries_not_traversed": submodules,
            "license_document_present": license_document,
            "potentially_sensitive_filename_count": sensitive_name_signals,
            "note": "Committed HEAD only; file types are extension-based. Working-tree changes and source contents are not examined. Filename signals are not a secret scan.",
        },
        "not_assessed": ["ownership or permission to license", "third-party licence compatibility",
                         "human versus generated authorship", "production use", "source-code quality",
                         "pull-request discussions and issue trackers", "secrets or personal data in contents/history",
                         "buyer fit, price or payment timing"],
        "sharing": "Nothing is uploaded. Review this aggregate report and decide whether to share it yourself.",
    }


def as_markdown(report: dict) -> str:
    h, t = report["history"], report["current_committed_tree"]
    lines = ["# Private-code preparation inventory", "", report["scope"], "",
             f"Measured: {report['measured_at']}", "",
             f"- Available reachable commits: {h['available_reachable_commits']}",
             f"- Shallow history: {'yes' if h['is_shallow'] else 'no'}",
             f"- Earliest observed commit date: {h['earliest_observed_committer_date'] or 'none'}",
             f"- Latest observed commit date: {h['latest_observed_committer_date'] or 'none'}",
             f"- Date range covers all locally available reachable commits: {'yes' if h['date_range_complete_for_available_history'] else 'no; sampled only'}",
             f"- Files at committed HEAD: {t['tracked_files']}",
             f"- Submodules, not traversed: {t['submodule_entries_not_traversed']}",
             f"- Licence document present: {'yes; contents not assessed' if t['license_document_present'] else 'not detected'}",
             f"- Potentially sensitive filename signals: {t['potentially_sensitive_filename_count']}", "",
             "## File types", "", "| Type inferred from extension | Files |", "| --- | ---: |"]
    lines.extend(f"| {kind} | {count} |" for kind, count in t["file_types_by_extension"].items())
    lines += ["", h["note"], "", t["note"], "", "## Still to establish", ""]
    lines.extend("- " + item for item in report["not_assessed"])
    lines += ["", report["sharing"], ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path, help="A local Git repository; no clone is performed.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()
    try:
        report = inspect_repository(args.repository)
    except (InventoryError, ValueError, OSError) as exc:
        message = str(exc) if isinstance(exc, InventoryError) else "Repository metadata could not be interpreted."
        print("Inventory incomplete: " + message, file=sys.stderr)
        return 1
    print(as_markdown(report) if args.format == "markdown" else json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
