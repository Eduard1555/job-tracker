import re
from pathlib import Path

import pytest
from py_mini_racer import MiniRacer

APP_JS = Path(__file__).resolve().parent.parent / "frontend" / "app.js"

HOUR = 60 * 60 * 1000

# A stand-in for Date that is frozen at one moment, seen from a chosen timezone.
# toISOString() reports UTC (like the real Date); the get* methods report local time.
FAKE_DATE = """
const RealDate = Date;
function useFakeNow(utcMillis, offsetHours) {
  const utc = new RealDate(utcMillis);
  const local = new RealDate(utcMillis + offsetHours * %d);
  globalThis.Date = class {
    toISOString() { return utc.toISOString(); }
    getFullYear() { return local.getUTCFullYear(); }
    getMonth() { return local.getUTCMonth(); }
    getDate() { return local.getUTCDate(); }
  };
}
""" % HOUR


def load_today_function():
    """Pull the today() function out of app.js (the rest of the file needs a browser)."""
    match = re.search(r"^function today\(\) \{.*?^\}", APP_JS.read_text(), re.S | re.M)
    assert match, "today() not found in frontend/app.js"
    return match.group(0)


@pytest.mark.parametrize(
    "utc_now, offset_hours, expected",
    [
        ("2026-10-06T22:00:00Z", +3, "2026-10-07"),  # 1 AM in Bucharest: UTC is still the day before
        ("2026-10-07T04:00:00Z", -7, "2026-10-06"),  # 9 PM in California: UTC is already the next day
        ("2026-10-07T11:00:00Z", +3, "2026-10-07"),  # daytime: UTC and local agree
    ],
)
def test_default_date_is_the_users_local_date(utc_now, offset_hours, expected):
    js = MiniRacer()
    js.eval(FAKE_DATE)
    js.eval(load_today_function())
    js.eval(f"useFakeNow(RealDate.parse('{utc_now}'), {offset_hours})")

    assert js.eval("today()") == expected


def test_app_js_never_renders_text_as_html():
    # innerHTML would treat user input like "Engineer <Backend>" as HTML tags (and run scripts)
    assert not re.search(r"\.innerHTML\s*=", APP_JS.read_text())
