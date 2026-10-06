# Handover: customer reports

Branch: `practice-takehome`. Report 1 is committed in `9f387d8`. The fixes for Reports 2 and 3 are **not committed yet**.

| Report | Status | Automated test | Manual check |
|---|---|---|---|
| 1. Wrong date after midnight | Fixed | Added, passes | Passed |
| 2. New entry not at top of its day | Fixed | Added, passes | Passed |
| 3. `<Backend>` disappears from role | Fixed | Added, passes | Passed |

Full suite: **30 passed** (25 tests from before + 5 new).

## Report 1: date saved as the previous day late at night

**Reported:** An application added at about 1 AM was saved with the previous day's date. The customer didn't touch the date field, which was already filled in. It works fine during the day.

**Root cause:** `today()` in `frontend/app.js` filled in the date field with `new Date().toISOString().slice(0, 10)`. That is the **UTC** date, not the user's local date. East of UTC (for example Bucharest, UTC+3 in summer), the UTC date is still yesterday for the first hours after midnight. West of UTC, the field shows tomorrow's date in the evening.

**Changed:**
- `frontend/app.js`: `today()` now builds `YYYY-MM-DD` from `getFullYear()`, `getMonth() + 1` and `getDate()`, which use local time.
- `tests/test_frontend.py` (new): runs the real `today()` from `app.js` in a JavaScript engine with a fake clock set to a chosen time and timezone.
- `requirements-dev.txt`: added `mini-racer`, a Python package that includes the V8 JavaScript engine, so pytest can run frontend code without Node.

**Verified:**
- **Automated:** `test_default_date_is_the_users_local_date` has 3 cases: 1 AM Bucharest, 9 PM California, and daytime. On the old code, the two near-midnight cases failed. With the fix, all 3 pass.
- **Manual:** passed (checked by the developer). Steps: Set the system clock to between 00:00 and 03:00 local time, reload the page, and check that the date field shows today's local date.

**Open / next:** the fake clock only covers the `Date` methods that the old and new `today()` use. If `today()` is rewritten another way (for example with `toLocaleDateString`), the test will need updating.

## Report 2: newest entry is not at the top for the same day

**Reported:** When several applications share a date, the one just added appears below the others from that day instead of at the top.

**Root cause:** `list_applications` in `backend/main.py` sorted with `ORDER BY date_applied DESC, id`. The tie-breaker `id` had no direction, so it defaulted to **ascending**. The newest row (highest id) therefore came last within its date. The existing sort test used only different dates, so it never hit the tie-breaker.

**Changed:**
- `backend/main.py`: the sort is now `ORDER BY date_applied DESC, id DESC`. Ids come from `AUTOINCREMENT`, so they only go up and a higher id reliably means added later.
- `tests/test_api.py`: added `test_list_shows_latest_added_first_within_the_same_day`.

**Verified:**
- **Automated:** the new test adds three applications on the same date and one on an older date. Before the fix it failed (`'First' != 'Just added'` at the top). After the fix it passes.
- **Manual:** passed (checked by the developer). Steps: Add 2–3 applications with the same date and check that the last one added is at the top of that day.

**Open / next:** nothing specific.

## Report 3: role "Engineer &lt;Backend&gt;" shows as "Engineer"

**Reported:** A role named `Engineer <Backend>` shows only as "Engineer" in the table. Other roles look normal.

**Root cause:** `createRow` in `frontend/app.js` set the role cell with `role.innerHTML = app.role`. Every other cell uses `textContent`. The browser read `<Backend>` as an HTML tag and hid it. The data itself was stored correctly: the API returned the full `'Engineer <Backend>'`. This was also a **security hole (XSS)**: a role such as `<img src=x onerror=...>` would run script in the browser of anyone viewing the table.

**Changed:**
- `frontend/app.js`: `role.textContent = app.role`.
- `tests/test_frontend.py`: added `test_app_js_never_renders_text_as_html`, which fails if `app.js` contains any `.innerHTML =` assignment.

**Verified:**
- **Automated:** the new test passes with the fix. The fix was written before the test, so the test was never run against the old code. It was checked separately against the old `app.js` from the last commit and finds the `innerHTML` assignment there, so it would have failed. The test only reads `app.js` as text; it doesn't render the table.
- **Manual:** passed (checked by the developer). Steps: Add the role `Engineer <Backend>` and check that the full text shows. Then add `<img src=x onerror="alert(1)">` and check that it shows as plain text with no popup.

**Open / next:** the test only catches `.innerHTML =`. It wouldn't catch other ways of inserting HTML, such as `insertAdjacentHTML` or `outerHTML`. A real browser test (for example with Playwright) would check what actually appears on screen.

## Left open overall

1. ~~Do the three manual checks above.~~ Done, all passed.
2. Commit the fixes for Reports 2 and 3.
3. The commit message for `9f387d8` is still a placeholder ("Fix: scurta descriere a ce ai reparat"). Amend it before pushing.
4. `requirements-dev.txt` lists `httpx2`. It is probably meant to be `httpx`, which FastAPI's `TestClient` needs. Check it with a fresh virtual environment.
