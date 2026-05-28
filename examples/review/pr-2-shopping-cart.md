# Code Review Exam — PR #2

> Review this pull request as if you were the reviewer on GitHub. Talk through the
> problems you would raise and how you would ask for them to be fixed. You have ~5 minutes.

---

## Pull request

**Title:** `Add discount support to cart`

**Description:**

> Adds discounts.

### Files changed — `cart.py`

```python
def add_to_cart(item, cart=[]):
    # add item to cart
    cart.append(item)        # append the item
    return cart

def total(cart):
    t = 0
    # loop over items
    for i in cart:
        t = t + i["price"] * i["qty"]   # multiply price by qty
    # apply discount
    if t > 100:
        t = t * 0.8          # discount
    # add tax
    t = t * 1.21
    # old logic, keep for now
    # if t > 500:
    #     t = t * 0.9
    return t


def test_total():
    cart = [{"price": 10, "qty": 2}]
    total(cart)   # should be fine
```

---

<details>
<summary><b>⚠️ EXAMINER ANSWER KEY — do not expand while screen-sharing</b></summary>

### Core planted issues

1. **Mutable default argument.** `def add_to_cart(item, cart=[])` — the default list is created
   once and shared across all calls, so items leak between "separate" carts. Fix: `cart=None`
   then `cart = cart if cart is not None else []`.
2. **Comment misuse.** The comments merely restate the code (`# append the item`,
   `# multiply price by qty`, `# loop over items`), adding noise. Worse, there is a block of
   **commented-out dead code** (`# old logic, keep for now`) that should simply be deleted —
   version control already remembers it.
3. **Magic numbers.** `100`, `0.8`, and `1.21` are unexplained. They should be named constants
   (`DISCOUNT_THRESHOLD`, `DISCOUNT_RATE`, `TAX_RATE`) with a comment on the *why*, not the *what*.
4. **Useless test.** `test_total` calls `total` but **asserts nothing** — it passes regardless of
   the result. Coverage theatre that gives false confidence.

### Bonus spots (for strong students)

- **Single-letter names** `t` and `i` hurt readability.
- **Thin PR description** — "Adds discounts" never states the rule (20% off over 100, then 21% tax),
  so a reviewer can't confirm the logic matches intent.

### Rubric (5 min, max 12)

- **2 pts** per core issue *named + why it matters* (max 8).
- **+1** per bonus spot (cap +2).
- **+1** for proposing a sound fix/refactor on at least one issue.
- **+1** for prioritizing by severity (the mutable default is a real bug, not just style).

</details>
