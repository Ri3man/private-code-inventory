# Preparing a private codebase for an AI licensing inquiry

This guide is for a code owner or an authorized representative considering a licensing inquiry. The first step can be a short description of the software and its available history. A repository upload is a separate decision, after the buyer's requirements and review terms are clear.

The inventory tool in this repository helps prepare a few facts locally. It does not establish that the code is yours to license, find secrets, value a repository or approve it for any buyer.

## 1. Measure the history you actually have

Inspect the script before running it. Point it at the **root** of a repository already on your device:

```sh
python3 private-code-inventory.py /path/to/local/repository --format markdown
```

The output remains in your terminal unless you save or share it yourself. The tool has no upload step. It does not report source contents, repository paths, authors, messages or private remote URLs. See the [README](README.md) for scope, privacy limits and tests.

## 2. Interpret the report conservatively

| Report field | What it describes | What it cannot establish |
| --- | --- | --- |
| Available reachable commits | History currently present in the local repository | All history ever created or the value of that history |
| Observed dates | Commit timestamps in the available sample | Verified project age, authorship or production use |
| Shallow history | Whether Git reports a shallow repository | What is missing from the remote or other copies |
| File types and file count | Extension-based categories in committed `HEAD` | Lines of code, token counts, working-tree changes or code quality |
| Licence-document filename | Whether a conventional filename was found | Ownership or compatible licence terms |
| Sensitive-filename count | A narrow filename heuristic | Whether the contents or old commits contain secrets or personal data |
| Submodule entries | Gitlinks, counted without entering them | The contents or rights of dependencies |

Even aggregate counts and dates may be confidential. Review the report before sharing. A zero filename warning does not make a repository safe to transfer.

## 3. Add the facts a script cannot verify

Prepare a category-level description of the system, its actual use, the history and supporting context that remain, and the person or entity able to authorize a licence. Identify unresolved client, employer, contractor, third-party and prior-licence restrictions. Relevant public releases or forks should be disclosed to the selected buyer.

You do not need to put customer names, credentials, private repository links or source excerpts in that first description. If authority is uncertain, resolve it with the rights holder before making a submission. A local report is not proof of permission.

## 4. Read the selected buyer's own process

Public sources were reviewed on 9 November 2026. Two routes are recorded in the dated [source-linked criteria snapshot](criteria/code-routes.json). This is a small selection, not a complete market list or a recommendation for a particular repository.

- **Patronus AI:** its [partner page](https://data.patronus.ai/partners) describes private codebases with development history and supporting context. Its [sample terms](https://data.patronus.ai/evaluation-terms) describe a signed NDA before sharing and a specified evaluation scope. Its [owner process](https://data.patronus.ai/) says full review may take up to 30 days and owner payment follows acceptance. These are published process statements, not an offer for your code.
- **Pangea.ai:** its [public code-licensing programme](https://pangea.ai/code-licensing/referral) describes owned production code and Git history, exclusions for client/NDA-restricted material, and redaction before submission. Its price examples are illustrative. Confirm the track, requirements, contract and payment event that apply to you.

Check the original pages again before acting. Buyer acceptance, owner compensation and any introducer's fee are different things. This repository does not receive or forward your report.

## 5. Ask a precise first question

You can adapt this outline yourself. It is not sent by the tool:

```text
I am the rights holder / authorized representative for a private software system.
Its purpose is: [category-level description].
It was used for: [actual use, without customer information].
Available context includes: [Git history, reviews, issues, documentation].
Known restrictions or exclusions are: [categories, or questions still unresolved].

Does this fit your current programme and country requirements?
What information is needed before any repository access or sample?
What review terms, licence scope, acceptance criteria and owner-payment event apply?
```

Before transferring files or connecting an account, agree which materials and recipients are in scope, what uses are permitted, what must be excluded, and what happens if the buyer declines. Ask about continued use of your software, exclusivity, sublicensing, retention/deletion, costs and payment. Obtain appropriate advice for unresolved rights or contract questions.

Data Ledger maintains this utility. Its separate website has a guided preparation checklist and a disclosed referral relationship; that does not establish a licence, value or buyer acceptance for your repository.
