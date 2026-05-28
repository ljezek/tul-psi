# Code Review Exam — PR #1

> Review this pull request as if you were the reviewer on GitHub. Talk through the
> problems you would raise and how you would ask for them to be fixed. You have ~5 minutes.

---

## Pull request

**Title:** `fix`

**Description:**

_(none)_

### Files changed — `payments.py`

```python
import datetime

users = {}

def process(a, b, amt):
    # process
    u1 = users[a]
    u2 = users[b]
    if u1["bal"] >= amt:
        u1["bal"] = u1["bal"] - amt
        u2["bal"] = u2["bal"] + amt
        # log it
        f = open("transactions.log", "a")
        f.write(str(datetime.datetime.now()) + " " + a + "->" + b + " " + str(amt) + "\n")
        f.write("balance " + a + " = " + str(u1["bal"]) + "\n")
        # send email
        print("Sending email to " + u1["email"])
        msg = "Dear " + u1["name"] + ", you sent " + str(amt) + " to " + u2["name"]
        send_email(u1["email"], msg)
        # send email to receiver
        print("Sending email to " + u2["email"])
        msg2 = "Dear " + u2["name"] + ", you received " + str(amt)
        send_email(u2["email"], msg2)
        return True
    else:
        return False
```

---

<details>
<summary><b>⚠️ EXAMINER ANSWER KEY — do not expand while screen-sharing</b></summary>

### Core planted issues

1. **God function.** `process` validates funds, mutates two balances, opens and writes a log
   file, and formats & sends two emails. Far too many responsibilities — should be decomposed
   (e.g. `transfer`, `record_transaction`, `notify`).
2. **Bad naming.** `process`, `a`, `b`, `amt`, `u1`, `u2`, `f`, `msg2` carry no meaning. Opaque
   names are especially dangerous in money-handling code.
3. **Bad PR hygiene.** Title `fix` is meaningless; description is empty. No rationale, no scope,
   no risk note for a change that moves money. A reviewer should refuse to merge until this is
   explained.
4. **Missing tests.** The balance arithmetic and the insufficient-funds branch are completely
   untested.

### Bonus spots (for strong students)

- **Resource leak** — `open(...)` is never closed and no `with` block is used.
- **Returns booleans instead of raising** on failure — easy for callers to ignore.
- **Module-level mutable global** `users` — shared state, hard to test.
- **No atomicity / rollback** — if the log write or second email fails, money has already moved.

### Rubric (5 min, max 12)

- **2 pts** per core issue *named + why it matters* (max 8).
- **+1** per bonus spot (cap +2).
- **+1** for proposing a sound fix/refactor on at least one issue.
- **+1** for prioritizing by severity (correctness/money safety before style).

</details>
