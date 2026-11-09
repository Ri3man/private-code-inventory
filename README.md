# Private-code inventory

A small, local Git metadata report for people preparing to discuss licensing a private codebase. Python 3.9+ and Git are the only requirements. No dependencies, account, network request or repository upload.

This tool helps answer **what history and file types are available**. It does not determine ownership, licence compatibility, security, quality, price or whether a buyer will accept your code.

For the next step, read [Preparing a private codebase for an AI licensing inquiry](GUIDE.md): how to interpret the report, describe the material without uploading it, and ask a buyer about review and payment terms.

## Run it locally

Download and inspect `private-code-inventory.py`, then run it against the root directory of a repository already on your device. Nested directories are rejected so a subfolder cannot silently produce a report for its whole parent repository:

```sh
python3 private-code-inventory.py /path/to/local/repository
python3 private-code-inventory.py /path/to/local/repository --format markdown
```

Output goes to your terminal. To keep a local copy, use your shell's normal redirection:

```sh
python3 private-code-inventory.py /path/to/local/repository > inventory.json
```

Review the output before sharing it. This program never submits it to a buyer or to Data Ledger. It does not clone a remote repository or install anything. Worktrees, bare repositories and shallow repositories are supported; a shallow clone can report only the history present locally.

## What is measured

- Number of commits reachable from the locally available refs and HEAD.
- Earliest/latest observed committer timestamps, sampling at most 100,000 commits.
- Number and broad file types of files in the committed HEAD tree, inferred from a fixed extension list.
- Whether a conventional licence-document name appears, without reading its contents.
- A count of filenames commonly associated with sensitive files, without reporting those names or reading their contents.
- Submodule entries, counted without entering them.

Dates can be rewritten. File types are guesses from extensions. A licence filename does not establish legal rights. Filename signals are **not a secret scan**. Uncommitted files are outside the inventory. Aggregate counts and dates can themselves be confidential.

## What is not exported or assessed

The report omits repository paths/names, remote URLs, branches, commit hashes, authors, emails, commit messages, filenames and source-file contents. Git metadata commands run with network protocols disabled and without optional locks, paging, fsmonitor hooks or inherited Git configuration variables. Each command has a 60-second timeout.

The tool does not establish human authorship, production use, ownership, permission from clients or employers, third-party licence compatibility, the absence of secrets/personal data, or buyer eligibility. It does not execute your project, run tests, fetch missing objects or traverse submodules. Run it only against a local repository you are authorized to inspect.

Before sharing anything, establish who can authorize the proposed use, which client/employer/third-party material must be excluded, and the buyer's actual review terms. This is a preparation aid, not a security or legal review.

## Buyer-source notes

[`criteria/code-routes.json`](criteria/code-routes.json) records a small, dated set of public statements with primary source links. It separates owner payments from introducer payments. It is neither a comprehensive marketplace nor evidence of a completed transaction. Unknowns stay explicit, and source statements may change.

Data Ledger maintains this utility and the [private-code preparation guide](https://requiem-lead-lab.shortbuddy.chatgpt.site/guides/license-private-code). The guide discloses its referral relationship. This repository does not contain affiliate redirects or collect reports.

## Tests and example

```sh
python3 -m unittest discover -s tests -v
```

The tests create synthetic local repositories, exercise empty/bare/shallow repositories and submodules, check sensitive text is absent, and verify inherited Git variables cannot redirect the selected repository. The example report under `examples/` is synthetic test output, not someone's private repository or a buyer acceptance.

The [JSON schema](schema/inventory.schema.json) describes version 1.0.0 reports. Contributions should preserve the local-only boundary and include tests. Do not attach private reports, repository URLs, code or credentials to public issues.

MIT licence. No warranties or payout claims.
