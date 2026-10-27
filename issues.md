# Issues Found — `billing_system.py`

Starting point: **Pylint 4.43/10**, **Bandit 5 issues** (1 High, 1 Medium, 3 Low), **Flake8 36 warnings**.

Sorted with the most serious first. The last section lists logic bugs that none of the tools flagged — they only showed up by running the program and reading its output.

## Security issues (Bandit)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| B413: deprecated pyCrypto import | Security — **High** | 8, 72–74 | The `Crypto.Cipher.AES` library is no longer maintained. It is also used in **ECB mode**, so the same card number always encrypts to the same text — the demo prints `Same card, same ciphertext? True`. An attacker can spot repeated cards. | Replace with `Fernet` from the maintained `cryptography` library, which uses a random value each time, so the same card gives different ciphertext. |
| B702: Mako template open to XSS | Security — **Medium** | 86 | The username is put into the HTML without escaping. The demo user `<b onmouseover=alert(1)>ravi</b>` comes out as live HTML in the invoice. | Remove Mako and build the HTML with `html.escape()` on the username, so tags are shown as text instead of running. |
| B105: hardcoded secret | Security — Low | 14–15 | `WEBHOOK_SECRET` and `CARD_KEY` are written directly in the code, so anyone who sees the code has the keys. | Read them from environment variables with `os.environ.get(...)`. |
| B311: predictable random numbers | Security — Low | 67 | Coupon codes are made with `random`, which is predictable, so codes could be guessed. | Use `secrets.choice()`, which is designed for security. |
| B101: `assert` used to check input | Security — Low | 85 | `assert` is removed when Python runs in optimised mode (`-O`), so the negative-amount check would silently disappear. | Replace with `if amount < 0: raise ValueError(...)`. |

## Code quality issues (Pylint)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| `return` inside `finally` | Bug | 60–64 | `return` in a `finally` block hides any error that happens in the `try`. The `print` after it can never run. | Remove the `try/finally`, calculate the refund normally, and drop the unreachable line. |
| Function names not in snake_case | Style | 24, 27, 35, 40, 43, 50, 58, 66, 69, 72, 76, 80, 84 | Names like `isTrialOver` and `applyCoupon` use camelCase. Python's convention is `is_trial_over`. | Rename every function to snake_case and update every call. |
| Missing docstrings | Style | whole file | No module docstring and no function docstrings, so the code doesn't explain itself. | Add a one-line docstring to the module and every function. |
| `dict()` / `list()` / `set([...])` | Style | 16, 21, 70 | Calling `dict()` and `list()` is slower and wordier than `{}` and `[]`. | Use literals: `{}`, `[]`, and a set comprehension. |
| Program runs on import | Bug | 107 | `main()` runs even if another file only imports this one. | Wrap it in `if __name__ == "__main__":`. |

## Formatting issues (Flake8)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| F401: unused imports | Style | 1 | `os` and `sys` are imported but never used. | Remove them. |
| E401: multiple imports on one line | Style | 1 | `import os, sys` on one line. | One import per line. |
| E711: comparison to `None` | Style | 29 | `coupon == None` should be `coupon is None`. | Use `is None`. |
| E302 / E305: missing blank lines | Style | 20–88, 107 | Functions need two blank lines between them. Repeated 18 times. | Add two blank lines before each function and after the last one. |
| E501: line too long | Style | 21, 67, 70, 77, 86, 91–104 | 16 lines are longer than 79 characters. | Break long lines and shorten the demo `print` labels. |

## Logic bugs found by running the program (not flagged by any tool)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Coupon over 100% | Bug | 18, 33 | `FRIENDS150` gives 150% off, so the invoice comes out **-294.41**. | Cap the discount so a total never goes below 0. |
| Coupon fails on its expiry day | Bug | 31 | `today >= expires` rejects the coupon on its last valid day. | Change to `today > expires`. |
| Trial ends one day late | Bug | 25 | Sept 1 to Sept 15 is 14 days, but `> TRIAL_DAYS` prints `False`. | Change to `>=`. |
| One extra payment attempt | Bug | 52 | "Max 3 attempts" actually tries **4** times. | Change `<=` to `<`. |
| Full refund after using most of the month | Bug | 58–63 | Refunds the full **999** after 25 of 30 days used. | Refund only the unused days: `price * (30 - days_used) / 30`. |
| Billing date crashes in December | Bug | 41 | `month + 1` becomes 13 in December, which crashes. | Roll over to January of the next year. |
| Money not rounded | Bug | 33, 38 | Amounts print as `529.938` and `588.8199999999999`. | Round money to 2 decimal places. |
