"""Phase 3 Checkpoint 5: System Settings API tests.

Standalone (urllib-based) suite matching the project's test style.
Restores default settings at the end so other suites are unaffected.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

from pathlib import Path

BASE = "http://localhost:8000"
ADMIN_EMAIL = "admin@careflow.ai"
ADMIN_PASSWORD = "admin123"

RUN_TOKEN = str(int(time.time() * 1000))

_RZP_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
if not _RZP_SECRET:
    _env_file = Path(__file__).resolve().parents[2] / ".env"
    if _env_file.exists():
        for _line in _env_file.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line.startswith("RAZORPAY_KEY_SECRET="):
                _RZP_SECRET = _line.split("=", 1)[1].strip()
                break

SECRET_PATTERNS = [
    _RZP_SECRET or "test-placeholder-razorpay-secret",  # Razorpay key secret
    "careflow_secret",           # db password
    "JWT",                       # jwt env key
    "RAZORPAY",                  # razorpay env keys
    "WEBHOOK",                   # webhook secret env key
]


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
            return resp.status, (json.loads(raw) if raw else None), raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw), raw
        except Exception:
            return e.code, raw, raw


PASS = 0
FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {extra}")


DEFAULT_PREFS = {
    "new_patient_registered": True,
    "payment_received": True,
    "appointment_confirmed": True,
    "consultation_completed": True,
    "token_called": True,
}


def full_body(prefs, ai_on):
    return {"notification_preferences": dict(prefs), "ai": {"symptom_analysis_enabled": ai_on}}


def main():
    print("=== Phase 3 Checkpoint 5: System Settings API Tests ===")

    # --- auth ---
    code, admin, _ = call("POST", "/api/auth/admin/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    check("admin login", code == 200 and admin.get("role") == "admin", f"got {code}")
    admin_token = admin.get("access_token", "")

    code, _, raw = call("GET", "/api/admin/settings")
    check("get settings without token -> 401", code == 401, f"got {code}")

    code, _, _ = call("PUT", "/api/admin/settings", full_body(DEFAULT_PREFS, True))
    check("put settings without token -> 401", code == 401, f"got {code}")

    # --- patient authorization ---
    def register(email, name, phone):
        code, u, _ = call("POST", "/api/auth/register", {"email": email, "full_name": name, "password": "pass1234", "phone": phone})
        _, lu, _ = call("POST", "/api/auth/login", {"email": email, "password": "pass1234"})
        return code, u, lu.get("access_token", "")

    code, _, p1_token = register(f"settings.p1.{RUN_TOKEN}@careflow.ai", "Settings Patient One", "9811111111")
    check("register settings test patient", code == 201, f"got {code}")

    code, _, _ = call("GET", "/api/admin/settings", token=p1_token)
    check("patient get settings -> 403", code == 403, f"got {code}")
    code, _, _ = call("PUT", "/api/admin/settings", full_body(DEFAULT_PREFS, True), token=p1_token)
    check("patient put settings -> 403", code == 403, f"got {code}")

    # --- admin read ---
    code, data, raw = call("GET", "/api/admin/settings", token=admin_token)
    check("admin get settings -> 200", code == 200, f"got {code}")
    check("settings has notification_preferences", "notification_preferences" in data)
    check("settings has ai section", "ai" in data and "model" in data["ai"] and "ollama_available" in data["ai"])
    check("settings has system section", "system" in data and "database" in data["system"])
    check("preference values are booleans", all(isinstance(data["notification_preferences"].get(k), bool) for k in DEFAULT_PREFS))
    check("ai symptom flag is boolean", isinstance(data["ai"]["symptom_analysis_enabled"], bool))
    check("ollama availability is boolean", isinstance(data["ai"]["ollama_available"], bool))
    check("ai model is non-empty string", isinstance(data["ai"]["model"], str) and len(data["ai"]["model"]) > 0)
    check("system database is ok/unreachable", data["system"]["database"] in ("ok", "unreachable"))
    check("defaults enabled on first read", all(data["notification_preferences"].get(k) for k in DEFAULT_PREFS) and data["ai"]["symptom_analysis_enabled"])

    leaked = [p for p in SECRET_PATTERNS if p in raw]
    check("no secrets leaked in settings response", not leaked, f"found {leaked}")

    # --- invalid updates ---
    bad1 = {"notification_preferences": {k: "yes" for k in DEFAULT_PREFS}, "ai": {"symptom_analysis_enabled": True}}
    code, _, _ = call("PUT", "/api/admin/settings", bad1, token=admin_token)
    check("put string booleans -> 422", code == 422, f"got {code}")

    code, _, _ = call("PUT", "/api/admin/settings", {"ai": {"symptom_analysis_enabled": True}}, token=admin_token)
    check("put missing notification_preferences -> 422", code == 422, f"got {code}")

    code, _, _ = call("PUT", "/api/admin/settings", {}, token=admin_token)
    check("put empty body -> 422", code == 422, f"got {code}")

    bad2 = full_body(DEFAULT_PREFS, True)
    bad2["foo"] = 1
    code, _, _ = call("PUT", "/api/admin/settings", bad2, token=admin_token)
    check("put unknown root key -> 422", code == 422, f"got {code}")

    bad3 = full_body(DEFAULT_PREFS, True)
    bad3["notification_preferences"]["nope"] = True
    code, _, _ = call("PUT", "/api/admin/settings", bad3, token=admin_token)
    check("put unknown preference key -> 422", code == 422, f"got {code}")

    bad4 = full_body(DEFAULT_PREFS, True)
    bad4["ai"] = {"foo": True}
    code, _, _ = call("PUT", "/api/admin/settings", bad4, token=admin_token)
    check("put missing ai flag -> 422", code == 422, f"got {code}")

    # --- valid update + persistence ---
    off = {k: False for k in DEFAULT_PREFS}
    code, data, _ = call("PUT", "/api/admin/settings", full_body(off, False), token=admin_token)
    check("put all off -> 200", code == 200, f"got {code}")
    check("put returns updated prefs", all(data["notification_preferences"].get(k) is False for k in DEFAULT_PREFS))
    check("put returns ai disabled", data["ai"]["symptom_analysis_enabled"] is False)

    code, data, _ = call("GET", "/api/admin/settings", token=admin_token)
    check("prefs persisted across requests", all(data["notification_preferences"].get(k) is False for k in DEFAULT_PREFS))
    check("ai flag persisted across requests", data["ai"]["symptom_analysis_enabled"] is False)

    code, _, raw = call("GET", "/api/admin/settings", token=admin_token)
    leaked = [p for p in SECRET_PATTERNS if p in raw]
    check("no secrets after update", not leaked, f"found {leaked}")

    # --- AI gate disabled ---
    code, _, _ = call("POST", "/api/ai/symptom-analysis", {"symptoms": "Fever and headache for two days"}, token=p1_token)
    check("symptom analysis blocked when disabled -> 403", code == 403, f"got {code}")
    code, body, _ = call("POST", "/api/ai/symptom-analysis", {"symptoms": "Fever and headache for two days"}, token=p1_token)
    check("disabled message is clear", code == 403 and "disabled" in str(body.get("detail", "")).lower(), f"got {code} {body}")

    # --- AI gate enabled ---
    code, data, _ = call("PUT", "/api/admin/settings", full_body(off, True), token=admin_token)
    check("re-enable ai only -> 200", code == 200 and data["ai"]["symptom_analysis_enabled"] is True, f"got {code}")
    code, _, _ = call("POST", "/api/ai/symptom-analysis", {"symptoms": "Fever and headache for two days"}, token=p1_token)
    check("symptom analysis allowed when enabled (200/503)", code in (200, 503), f"got {code}")

    # --- notification preference respected ---
    disabled = dict(DEFAULT_PREFS)
    disabled["new_patient_registered"] = False
    code, _, _ = call("PUT", "/api/admin/settings", full_body(disabled, True), token=admin_token)
    check("disable new-patient notifications -> 200", code == 200, f"got {code}")

    email_a = f"settings.silent.{RUN_TOKEN}@careflow.ai"
    code, _, _ = call("POST", "/api/auth/register", {"email": email_a, "full_name": "Silent Patient", "password": "pass1234", "phone": "9822222222"})
    check("register while notifications disabled -> 201", code == 201, f"got {code}")

    code, inbox, _ = call("GET", "/api/notifications?limit=200", token=admin_token)
    items = inbox.get("notifications") if isinstance(inbox, dict) and "notifications" in inbox else inbox
    silent_hit = [n for n in items if n.get("title") == "New Patient Registered" and email_a in str(n.get("message", ""))]
    check("no new-patient notification while disabled", not silent_hit, f"found {len(silent_hit)}")

    code, _, _ = call("PUT", "/api/admin/settings", full_body(DEFAULT_PREFS, True), token=admin_token)
    check("re-enable new-patient notifications -> 200", code == 200, f"got {code}")

    email_b = f"settings.heard.{RUN_TOKEN}@careflow.ai"
    code, _, _ = call("POST", "/api/auth/register", {"email": email_b, "full_name": "Heard Patient", "password": "pass1234", "phone": "9833333333"})
    check("register while notifications enabled -> 201", code == 201, f"got {code}")

    code, inbox, _ = call("GET", "/api/notifications?limit=200", token=admin_token)
    items = inbox.get("notifications") if isinstance(inbox, dict) and "notifications" in inbox else inbox
    heard_hit = [n for n in items if n.get("title") == "New Patient Registered" and email_b in str(n.get("message", ""))]
    check("new-patient notification delivered when enabled", len(heard_hit) == 1, f"found {len(heard_hit)}")

    # --- restore defaults ---
    code, data, _ = call("PUT", "/api/admin/settings", full_body(DEFAULT_PREFS, True), token=admin_token)
    check("restore default settings -> 200", code == 200, f"got {code}")
    check("defaults restored", all(data["notification_preferences"].get(k) for k in DEFAULT_PREFS) and data["ai"]["symptom_analysis_enabled"])

    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()