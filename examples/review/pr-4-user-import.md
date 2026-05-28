# Code Review Exam — PR #4

> Review this pull request as if you were the reviewer on GitHub. Talk through the
> problems you would raise and how you would ask for them to be fixed. You have ~5 minutes.

---

## Pull request

**Title:** `Update README`

**Description:**

> Minor docs update.

### Files changed — `import_users.py`

```python
import requests

API_KEY = "sk_live_8f3a9c2b7d1e4f60"   # production key

def import_users(path):
    f = open(path)
    data = f.read()
    rows = data.split("\n")
    for r in rows:
        try:
            parts = r.split(",")
            requests.post(
                "https://api.example.com/users",
                headers={"Authorization": "Bearer " + API_KEY},
                json={"email": parts[0], "name": parts[1]},
            )
        except:
            pass   # ignore bad rows
```

---

<details>
<summary><b>⚠️ EXAMINER ANSWER KEY — do not expand while screen-sharing</b></summary>

### Core planted issues

1. **Hardcoded secret (security).** A live API key (`sk_live_...`) is committed in source. It must
   come from an environment variable / secret store. Once committed it is already compromised and
   must be rotated.
2. **Bare `except: pass`.** Swallows *every* error silently — network failures, malformed rows,
   even `KeyboardInterrupt`. It hides real bugs and makes the import look successful when it isn't.
   Catch specific exceptions and log/handle them.
3. **No context manager.** `open(path)` is never closed; the file handle leaks. Use
   `with open(path) as f:`.
4. **Misleading PR title/description.** Titled "Update README" / "Minor docs update", but the diff
   adds networking code **and a production secret**. A reviewer must flag the title/scope mismatch
   and require the change be split out and reviewed properly.
5. **Missing tests.** The parsing and networking path has no tests.

### Bonus spots (for strong students)

- **No timeout** on `requests.post` — a hung server blocks the whole import indefinitely.
- **`IndexError` on short rows** (`parts[1]`) is masked by the bare except.
- **Trailing newline** produces an empty final row that is silently POSTed/failed.

### Rubric (5 min, max 12)

- **2 pts** per core issue *named + why it matters* (max 8 — there are 5 core issues here, so cap at 8).
- **+1** per bonus spot (cap +2).
- **+1** for proposing a sound fix on at least one issue.
- **+1** for prioritizing by severity (secret + silent failures before style).

</details>
