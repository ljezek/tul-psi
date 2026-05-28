# Code Review Exam — Examiner Guide

A kit of **4 short pull requests** for a 5-minute oral code-review exam. Each PR fits on one
screen and contains 3–5 deliberately planted issues that a competent reviewer should catch.
Use this file as your grading sheet; the per-PR answer keys are also embedded (collapsed) in
each handout.

## The handouts

| PR | File | Primary flaws |
|----|------|---------------|
| #1 | [pr-1-money-transfer.md](pr-1-money-transfer.md)   | god function · bad naming · bad PR title/no description · missing tests |
| #2 | [pr-2-shopping-cart.md](pr-2-shopping-cart.md)     | mutable default arg · comment misuse · magic numbers · useless test |
| #3 | [pr-3-square-rectangle.md](pr-3-square-rectangle.md) | broken class hierarchy (LSP) · misleading comment · bad naming · missing tests |
| #4 | [pr-4-user-import.md](pr-4-user-import.md)         | hardcoded secret · bare `except` · no context manager · misleading PR title · missing tests |

## How to run a 5-minute slot

1. Open **one** handout and share **only the student-facing block** (PR header + code).
   Keep the `⚠️ EXAMINER ANSWER KEY` `<details>` section **collapsed** — don't expand it on screen.
2. Ask the student to review aloud as if leaving comments on the PR: *what would you raise, and how?*
3. Prompt at most once if they stall — e.g. *"Anything about the PR title or description?"* or
   *"What about testing?"* — then let them continue.
4. Score against the rubric below.

## Issue → PR coverage matrix

| Issue type                               | PR1 | PR2 | PR3 | PR4 |
|------------------------------------------|:---:|:---:|:---:|:---:|
| God function                             |  ●  |     |     |     |
| Bad naming                               |  ●  |  ○  |  ●  |     |
| Comment misuse (restate/dead/misleading) |     |  ●  |  ●  |  ○  |
| Broken class hierarchy (LSP)             |     |     |  ●  |     |
| Bad PR title / no description            |  ●  |     |     |  ●  |
| Missing tests                            |  ●  |     |  ●  |  ●  |
| Useless test (asserts nothing)           |     |  ●  |     |     |
| Mutable default argument                 |     |  ●  |     |     |
| Magic numbers                            |     |  ●  |     |     |
| Hardcoded secret (security)              |     |     |     |  ●  |
| Bare `except` / swallowed errors         |     |     |     |  ●  |
| Resource leak (no context manager)       |  ○  |     |     |  ●  |

● = core planted issue (counts toward the rubric)  ○ = bonus spot (for strong students)

## Scoring rubric (per PR, max 12)

- **2 pts** per core issue *named **and** explained why it matters* (cap at 8).
- **+1** per bonus spot identified (cap +2).
- **+1** for proposing a sound fix/refactor on at least one issue.
- **+1** for prioritizing by severity — calling out security/correctness before style.

### Holistic band (alternative to points)

| Band | Behavior |
|------|----------|
| **Fail**      | Spots 0–1 issues, or only cosmetic ones. |
| **Pass**      | Spots ~half the core issues and can say *why* each is a problem. |
| **Good**      | Spots most core issues and proposes at least one concrete fix. |
| **Excellent** | Spots all core issues + a bonus, prioritizes by severity, and gives constructive, actionable feedback. |

## Notes

- The code blocks are teaching artifacts, not runnable programs (e.g. PR #1 calls an undefined
  `send_email`). That's intentional and irrelevant to the review.
- To make a slot **easier**, hide one bonus row; to make it **harder**, remove an obvious core
  issue (e.g. strip the hardcoded key from PR #4 so the student must find the subtler problems).
