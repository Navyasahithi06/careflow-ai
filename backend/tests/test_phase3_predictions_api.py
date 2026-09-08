import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import time
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = "http://localhost:8000"
ADMIN_EMAIL = "admin@careflow.ai"
ADMIN_PASSWORD = "admin123"

KNOWN_STATUS = {"OVERBOOKED", "HIGH", "MODERATE", "LOW", "NO_ACTIVITY"}

PASS = 0
FAIL = 0


def call(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {extra}")


def structure_ok(res):
    if not isinstance(res, dict):
        return False
    if "generated_at" not in res or "methodology" not in res or "demand" not in res or "doctor_utilization" not in res:
        return False
    meth = res["methodology"]
    if not all(k in meth for k in ("demand_model", "demand_description", "utilization_formula", "disclaimer")):
        return False
    demand = res["demand"]
    if not all(k in demand for k in (
        "sufficient_historical_data", "data_points", "total_appointments",
        "history_start", "history_end", "history", "forecast",
    )):
        return False
    util = res["doctor_utilization"]
    if not all(k in util for k in ("consultation_slot_minutes", "capacity_formula", "doctors")):
        return False
    if not isinstance(util["doctors"], list):
        return False
    required_doc = ("doctor_id", "doctor_name", "specialization", "avg_daily_booked", "worked_days",
                    "capacity_per_day", "historical_utilization_pct", "predicted_utilization_pct",
                    "forecast_appointments", "status", "notice")
    for d in util["doctors"]:
        if not all(k in d for k in required_doc):
            return False
    return True


def main():
    print("=== Phase 3 Checkpoint 3: Predictions API Tests ===")
    stamp = int(time.time())

    # 0. Admin login
    code, admin = call("POST", "/api/auth/admin/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    check("admin login", code == 200 and admin.get("role") == "admin", f"got {code}")
    admin_token = admin.get("access_token", "")

    # 1. Patient (non-admin) login + authorization
    pat_email = f"predpat_{stamp}@test.com"
    call("POST", "/api/auth/register", {"email": pat_email, "full_name": "Pred Pat", "password": "test1234", "phone": "9111223344"})
    code, pat = call("POST", "/api/auth/login", {"email": pat_email, "password": "test1234"})
    check("patient login", code == 200, f"got {code}")
    patient_token = pat.get("access_token", "")

    code, body = call("GET", "/api/admin/reports/predictions", token=patient_token)
    check("non-admin access denied (403)", code == 403, f"got {code}")

    code, body = call("GET", "/api/admin/reports/predictions")
    check("no token denied (401)", code == 401, f"got {code}")

    # 2. Valid prediction response (default params)
    code, res = call("GET", "/api/admin/reports/predictions", token=admin_token)
    check("valid predictions response (200)", code == 200, f"got {code}")
    check("response structure complete", structure_ok(res))
    check("methodology is statistical baseline", res["methodology"]["demand_model"] == "statistical_baseline")
    check("disclaimer present", bool(res["methodology"]["disclaimer"]))
    check("default forecast length == 7", len(res["demand"]["forecast"]) == 7, f"len={len(res['demand']['forecast'])}")
    check("active doctor utilization computed", len(res["doctor_utilization"]["doctors"]) >= 1)

    # 3. Deterministic values (no random/fake predictions): two calls are identical
    code2, res2 = call("GET", "/api/admin/reports/predictions", token=admin_token)
    check("repeat call 200", code2 == 200, f"got {code2}")
    check("forecast values deterministic", res["demand"] == res2["demand"])
    check("utilization values deterministic", res["doctor_utilization"] == res2["doctor_utilization"])

    # 4. Forecast internal consistency
    forecast = res["demand"]["forecast"]
    check("forecast counts non-negative", all(isinstance(f["forecast"], int) and f["forecast"] >= 0 for f in forecast))
    check("low<=forecast<=high", all(f["low"] <= f["forecast"] <= f["high"] for f in forecast))
    check("forecast period after history end", all(f["date"] > res["demand"]["history_end"] for f in forecast))
    check("weekday labels valid", all(f["weekday"] in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"} for f in forecast))
    check("history counts non-negative ints", all(isinstance(h["count"], int) and h["count"] >= 0 for h in res["demand"]["history"]))

    # 5. Historical data handling with a controlled window
    code, res = call("GET", "/api/admin/reports/predictions?start=2026-08-26&end=2026-09-02&horizon_days=3", token=admin_token)
    check("controlled-window request 200", code == 200, f"got {code}")
    forecast = res["demand"]["forecast"]
    check("controlled forecast length == 3", len(forecast) == 3, f"len={len(forecast)}")
    expected_first = date.fromisoformat("2026-09-02") + timedelta(days=1)
    check(
        "forecast starts the day after history end",
        forecast[0]["date"] == str(expected_first),
        f"{forecast[0]['date']} vs {expected_first}",
    )
    for i, f in enumerate(forecast):
        expect = date.fromisoformat("2026-09-02") + timedelta(days=1 + i)
        if f["date"] != str(expect) or f["weekday"] != ("Mon Tue Wed Thu Fri Sat Sun".split())[expect.weekday()]:
            check(f"forecast day {i} date/weekday mismatch", False, f"{f['date']} {f['weekday']} vs {expect}")
            break
    else:
        check("forecast day dates and weekdays correct", True)
    check("controlled window uses real history", res["demand"]["total_appointments"] >= 1 and res["demand"]["data_points"] >= 1)
    check("sufficient with 7+ distinct days", res["demand"]["sufficient_historical_data"] is True)

    # 6. Insufficient-data handling (single day, 1 appointment)
    code, res = call("GET", "/api/admin/reports/predictions?start=2026-08-26&end=2026-08-26", token=admin_token)
    check("insufficient-data request 200", code == 200, f"got {code}")
    check("insufficient data flagged", res["demand"]["sufficient_historical_data"] is False)
    check("insufficient data -> empty forecast", res["demand"]["forecast"] == [])
    check("insufficient data -> notice present", bool(res["demand"]["notice"]))
    check("utilization still returned", len(res["doctor_utilization"]["doctors"]) >= 1)

    # 7. Date / range validation
    code, body = call("GET", "/api/admin/reports/predictions?start=2026-09-05&end=2026-09-01", token=admin_token)
    check("start after end -> 400", code == 400, f"got {code}")
    code, body = call("GET", "/api/admin/reports/predictions?start=not-a-date", token=admin_token)
    check("invalid date -> 400", code == 400, f"got {code}")
    code, body = call("GET", "/api/admin/reports/predictions?horizon_days=0", token=admin_token)
    check("horizon 0 -> 422", code == 422, f"got {code}")
    code, body = call("GET", "/api/admin/reports/predictions?horizon_days=31", token=admin_token)
    check("horizon 31 -> 422", code == 422, f"got {code}")
    code, body = call("GET", "/api/admin/reports/predictions?horizon_days=abc", token=admin_token)
    check("horizon non-int -> 422", code == 422, f"got {code}")

    # 8. Doctor utilization calculation is consistent with its documented formula
    code, res = call("GET", "/api/admin/reports/predictions", token=admin_token)
    check("utilization fetch 200", code == 200, f"got {code}")
    util = res["doctor_utilization"]
    check("slot minutes documented", util["consultation_slot_minutes"] == 15)
    ok = True
    for d in util["doctors"]:
        if d["status"] not in KNOWN_STATUS:
            ok = False
            break
        if d["capacity_per_day"] <= 0:
            ok = False
            break
        if d["worked_days"] > 0:
            expected = round(100 * d["avg_daily_booked"] / d["capacity_per_day"], 1)
            if d["historical_utilization_pct"] != expected or d["predicted_utilization_pct"] != expected:
                ok = False
                break
            if d["status"] == "NO_ACTIVITY":
                ok = False
                break
        else:
            if d["avg_daily_booked"] != 0 or d["historical_utilization_pct"] != 0 or d["status"] != "NO_ACTIVITY":
                ok = False
                break
    check("utilization formula consistent across doctors", ok)

    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()