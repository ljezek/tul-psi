# Code Review Exam — PR #3

> Review this pull request as if you were the reviewer on GitHub. Talk through the
> problems you would raise and how you would ask for them to be fixed. You have ~5 minutes.

---

## Pull request

**Title:** `Add Square shape`

**Description:**

> Adds a Square class that reuses Rectangle so we don't duplicate the area code.

### Files changed — `shapes.py`

```python
class Rectangle:
    """Rectangle is a shape with width and height."""
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def set_width(self, w):
        self.w = w

    def set_height(self, h):
        self.h = h

    def area(self):
        return self.w * self.h


# A square is a rectangle, so we just inherit
class Square(Rectangle):
    def __init__(self, size):
        super().__init__(size, size)

    def set_width(self, w):
        self.w = w
        self.h = w   # keep it square

    def set_height(self, h):
        self.w = h
        self.h = h
```

---

<details>
<summary><b>⚠️ EXAMINER ANSWER KEY — do not expand while screen-sharing</b></summary>

### Core planted issues

1. **Broken class hierarchy (Liskov substitution violation).** `Square(Rectangle)` overrides the
   setters so a `Square` cannot stand in for a `Rectangle`. Any code that sets width and height
   independently breaks:
   ```python
   def stretch(r: Rectangle):
       r.set_width(3)
       r.set_height(4)
       assert r.area() == 12   # fails for Square -> 16
   ```
   Inheritance was chosen for **code reuse**, not a true "is-a" relationship. Prefer a shared
   `Shape` interface/abstract base, or composition.
2. **Misleading comment.** `# A square is a rectangle, so we just inherit` actively justifies the
   wrong design — it is exactly the reasoning a reviewer should challenge, not accept.
3. **Bad naming.** `w`, `h`, `size` as attributes/params; and the setters `set_width`/`set_height`
   secretly mutate *both* dimensions — a surprising side effect hidden behind an innocent name.
4. **Missing tests.** No tests at all, and crucially none exercising the substitutability trap that
   would have exposed the design flaw.

### Bonus spots (for strong students)

- **No validation** of negative/zero dimensions.
- The **duplication concern is real**, but inheritance is the wrong tool to solve it — a good
  student names the legitimate goal *and* the better solution.

### Rubric (5 min, max 12)

- **2 pts** per core issue *named + why it matters* (max 8).
- **+1** per bonus spot (cap +2).
- **+1** for proposing a sound fix/refactor (shared base or composition).
- **+1** for prioritizing by severity (the LSP break is the headline issue).

</details>
