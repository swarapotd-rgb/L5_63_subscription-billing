# Reflection — Lab 5: Static Code Analysis

**Swara Ashish Potdar · PES1UG24CS487 · `L5_63_subscription-billing`**

## Results at a glance

| Tool | Before | After |
|---|---|---|
| Pylint | 4.43 / 10 | **10.00 / 10** |
| Bandit | 5 issues (1 High, 1 Medium, 3 Low) | **0 issues** |
| Flake8 | 36 warnings | **0 warnings** |

No warnings were hidden with `# nosec`, `# noqa` or `# pylint: disable` — every issue was fixed in the code itself.

## 1. Which issues were the easiest to fix, and which were the hardest? Why?

**Easiest:** the Flake8 formatting issues. Most of the 36 warnings were the same two problems repeated — missing blank lines between functions (E302) and lines over 79 characters (E501). They are purely about layout, so fixing them could not break anything.

**Hardest:** two of the Bandit issues.

- **B413 (deprecated pyCrypto, High severity).** This was not a one-line change. The card encryption had to move to a different library (`cryptography`'s Fernet), with a different way of handling the key. It also fixed a second problem Bandit did not mention by name: the old code used **ECB mode**, so the same card number always produced the same encrypted text. The demo proved it — `Same card, same ciphertext?` changed from `True` to `False` after the fix.
- **B702 (Mako template, Medium severity).** Bandit flags *any* use of Mako, so just adding escaping would not have cleared it. The template had to be removed and replaced with an f-string using `html.escape()`. After the fix, the attack name `<b onmouseover=alert(1)>` shows up as harmless text (`&lt;b ...`) instead of running as HTML.

The logic bugs were also harder than they looked, because no tool pointed at them at all — I had to notice them myself in the program's output.

## 2. Did the tools report any false positives? If so, describe one.

None of the reported issues were false positives in this file — every one pointed at a real problem. But a few were closer to borderline:

- **B101 (`assert` used).** On its own an `assert` is not dangerous. Bandit flags it because Python removes asserts when run with `-O`, so here the "amount must not be negative" check would silently disappear. It was worth fixing, but it is a "this could go wrong" warning rather than an actual hole.
- **B105 (hardcoded password).** Bandit guesses based on the variable name. Here it was right — `WEBHOOK_SECRET = "whsec_live_..."` really was a live secret — but the same rule would also flag a harmless test value, so it needs a human to judge.

The more interesting finding was the opposite: **false negatives** — real problems the tools missed.

- **Seven logic bugs** that no tool flagged: a 150% coupon giving a negative invoice (−294.41), a coupon rejected on its own expiry day, a trial ending a day late, 4 payment attempts instead of 3, a full 999 refund after 25 of 30 days used, a billing-date crash every December, and proration dividing by 30 for February. These only showed up by running the program and reading the output.
- **Security problems Bandit did not flag:** comparing the webhook signature with `==` (open to timing attacks; fixed with `hmac.compare_digest`), and parsing untrusted XML with `lxml` (fixed with `defusedxml`).

Also, the tools **disagree with each other** on line length: Pylint allows 100 characters, Flake8 only 79. After Pylint reached 10/10, Flake8 still flagged 11 lines between 80 and 98 characters.

## 3. How would you integrate static analysis tools into a real development workflow?

- **In the editor:** run Pylint and Flake8 as you type, so problems are fixed while the code is fresh instead of piling up into 36 warnings.
- **Before every commit:** a pre-commit hook that runs all three tools and blocks the commit if Bandit finds a High or Medium issue.
- **On every push or pull request:** a CI pipeline (for example GitHub Actions) that runs all three and fails the build if the Pylint score drops below an agreed level, such as 9.5.
- **One shared config:** agree on settings like line length in a single config file, so Pylint and Flake8 stop disagreeing.

But this lab showed the limit: a perfect 10/10 does not mean the program is correct. Static analysis has to sit alongside **tests** — a unit test for "coupon total is never negative" would have caught the FRIENDS150 bug immediately, and no linter ever could.

## 4. What improvements did you see in code quality, readability or robustness?

- **Security:** card numbers are now properly encrypted, secrets come from environment variables instead of the source code, coupon codes cannot be predicted, invoice HTML cannot be used for an XSS attack, and webhook XML and signatures are handled safely.
- **Correctness:** every number in the demo output is now right — no negative invoice, the coupon works on its last day, 3 payment attempts, a fair 166.5 refund, and the February upgrade uses 28 days.
- **Robustness:** the December crash is gone, the negative-amount check can no longer be switched off by `-O`, and the `return` inside `finally` that could swallow errors was removed.
- **Readability:** snake_case function names, a docstring on every function, one import per line, and consistent spacing. The file is now easier for someone else to read and change.
- **Reusability:** `main()` now only runs when the file is executed directly, so other code can import these functions without triggering the demo.
