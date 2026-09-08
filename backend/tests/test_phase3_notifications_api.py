import urllib.request
import urllib.error
import urllib.parse
import json
import hmac
import hashlib
import sys
import time
import threading
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_RZP_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
if not _RZP_SECRET:
    _env_file = Path(__file__).resolve().parents[2] / ".env"
    if _env_file.exists():
        for _line in _env_file.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line.startswith("RAZORPAY_KEY_SECRET="):
                _RZP_SECRET = _line.split("=", 1)[1].strip()
                break
RZP_SECRET = _RZP_SECRET or "test-placeholder-razorpay-secret"

BASE = "http://localhost:8000"
ADMIN_EMAIL = "admin@careflow.ai"
ADMIN_PASSWORD = "admin123"


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


def _confirm_appt(ptoken, appt_id):
    code, order = call("POST", "/api/payments/create-order", {"appointment_id": appt_id}, token=ptoken)
    if code != 200:
        return code
    order_id = order["gateway_order_id"]
    payment_id = f"pay_notif_{int(time.time())}"
    sig = hmac.new(RZP_SECRET.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
    return call("POST", "/api/payments/verify", {
        "appointment_id": appt_id,
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": sig,
    }, token=ptoken)[0]


def main():
    print("=== Phase 3 Checkpoint 2: Notifications API Tests ===")
    stamp = int(time.time())

    # 0. Admin + patients
    code, admin = call("POST", "/api/auth/admin/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    check("admin login", code == 200 and admin.get("role") == "admin", f"got {code}")
    admin_token = admin.get("access_token", "")

    def register(email, name, phone):
        code, u = call("POST", "/api/auth/register", {"email": email, "full_name": name, "password": "test1234", "phone": phone})
        _, lu = call("POST", "/api/auth/login", {"email": email, "password": "test1234"})
        return u, lu.get("access_token", "")

    pa, pa_token = register(f"notif_pa_{stamp}@test.com", "Notif Patient A", "9333333331")
    pb, pb_token = register(f"notif_pb_{stamp}@test.com", "Notif Patient B", "9333333332")
    check("register patients A and B", bool(pa.get("id")) and bool(pb.get("id")))

    # 1. Fresh inbox / unread count
    code, lst = call("GET", "/api/notifications", token=pa_token)
    check("patient A inbox readable (200)", code == 200 and isinstance(lst, list), f"got {code}")
    code, cnt = call("GET", "/api/notifications/unread-count", token=pa_token)
    check("patient A initial unread count is 0", code == 200 and cnt.get("count") == 0, f"got {code} {cnt}")

    # 2. New patient registration notifies admin(s)
    code, _ = register(f"notif_pc_{stamp}@test.com", "Notif Patient C", "9333333333")
    code, cnt = call("GET", "/api/notifications/unread-count", token=admin_token)
    check("admin unread count increases on registration", code == 200 and cnt.get("count", 0) >= 1, f"got {code} {cnt}")
    code, alst = call("GET", "/api/notifications", token=admin_token)
    check("admin inbox has new-patient notification",
          code == 200 and any(n["notification_type"] == "new_patient_registered" for n in alst),
          f"got {code}")

    # 3. Appointment + payment triggers patient notifications
    code, appt = call("POST", "/api/appointments", {"doctor_id": 2, "appointment_date": "2026-09-26", "appointment_time": "10:00"}, token=pa_token)
    if code != 201:
        for d in range(10, 31):
            code, appt = call("POST", "/api/appointments", {"doctor_id": 2, "appointment_date": f"2026-09-{d:02d}", "appointment_time": "10:00"}, token=pa_token)
            if code == 201:
                break
    check("patient A books appointment (201)", code == 201 and appt.get("id"), f"got {code} {appt}")
    appt_id = appt.get("id")

    vcode = _confirm_appt(pa_token, appt_id)
    check("payment verified / appointment confirmed (200)", vcode == 200, f"got {vcode}")

    code, lst = call("GET", "/api/notifications", token=pa_token)
    ntypes = {n["notification_type"] for n in lst}
    check("patient A received payment-success notification", "payment_success" in ntypes, f"got {ntypes}")
    check("patient A received appointment-confirmed notification", "appointment_confirmed" in ntypes, f"got {ntypes}")
    code, cnt = call("GET", "/api/notifications/unread-count", token=pa_token)
    check("patient A unread count >= 2 after payment", code == 200 and cnt.get("count", 0) >= 2, f"got {code} {cnt}")

    # admin received payment received notification
    code, alst = call("GET", "/api/notifications", token=admin_token)
    pay_msgs = [n for n in alst if n["notification_type"] == "payment_success"]
    check("admin inbox has payment-received notification", len(pay_msgs) >= 1, f"got {len(pay_msgs)}")

    # 4. Token called / consultation completed triggers
    qdate = appt["appointment_date"]
    code, _ = call("POST", "/api/admin/tokens/call-next", {"doctor_id": 2, "queue_date": qdate}, token=admin_token)
    check("admin calls next token (200)", code == 200, f"got {code}")
    code, lst = call("GET", "/api/notifications", token=pa_token)
    check("patient A received token-called notification",
          any(n["notification_type"] == "token_called" for n in lst), f"got {code}")

    call("POST", "/api/admin/tokens/start-consultation", {"doctor_id": 2, "queue_date": qdate}, token=admin_token)
    code, _ = call("POST", "/api/admin/tokens/complete", {"doctor_id": 2, "queue_date": qdate}, token=admin_token)
    check("admin completes consultation (200)", code == 200, f"got {code}")
    code, lst = call("GET", "/api/notifications", token=pa_token)
    check("patient A received consultation-completed notification",
          any(n["notification_type"] == "consultation_completed" for n in lst), f"got {code}")

    # 5. Ownership / authorization
    pa_ids = {n["id"] for n in lst}
    code, blst = call("GET", "/api/notifications", token=pb_token)
    check("patient B inbox does not contain patient A notifications", code == 200 and not (pa_ids & {n["id"] for n in blst}), f"got {code}")
    if pa_ids:
        other_id = next(iter(pa_ids))
        code, _ = call("POST", f"/api/notifications/{other_id}/read", token=pb_token)
        check("patient B cannot mark patient A notification read (404)", code == 404, f"got {code}")
    code, _ = call("GET", "/api/notifications/unread-count")
    check("no token -> 401 on unread count", code == 401, f"got {code}")

    # 6. Mark individual read
    unread_before = call("GET", "/api/notifications/unread-count", token=pa_token)[1].get("count", 0)
    target = next((n["id"] for n in lst if not n["is_read"]), None)
    if target:
        code, n = call("POST", f"/api/notifications/{target}/read", token=pa_token)
        check("mark single notification read (200)", code == 200 and n.get("is_read") is True, f"got {code} {n}")
        code, cnt = call("GET", "/api/notifications/unread-count", token=pa_token)
        check("unread count decreased by 1", cnt.get("count", 0) == unread_before - 1, f"got {cnt}")
    else:
        check("mark single notification read (200)", False, "no unread notifications found")

    # 7. Mark all read
    code, res = call("POST", "/api/notifications/read-all", token=pa_token)
    check("mark-all-read (200)", code == 200 and res.get("updated", 0) >= 1, f"got {code} {res}")
    code, cnt = call("GET", "/api/notifications/unread-count", token=pa_token)
    check("unread count is 0 after read-all", cnt.get("count") == 0, f"got {cnt}")

    # 8. SSE stream delivery (admin receives live new-patient event)
    sse_results = []

    def sse_watch(token):
        url = BASE + "/api/notifications/stream?token=" + urllib.parse.quote(token)
        req = urllib.request.Request(url, method="GET")
        deadline = time.time() + 25
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                while time.time() < deadline:
                    raw = resp.readline()
                    if not raw:
                        continue
                    line = raw.decode().strip()
                    if line.startswith("data:"):
                        payload = line[5:].strip()
                        try:
                            ev = json.loads(payload)
                            sse_results.append(ev)
                        except Exception:
                            pass
        except Exception:
            return

    t = threading.Thread(target=sse_watch, args=(admin_token,), daemon=True)
    t.start()
    time.sleep(2.0)  # let the connection register on the hub

    e_mail = f"notif_pe_{stamp}@test.com"
    call("POST", "/api/auth/register", {"email": e_mail, "full_name": "Notif Patient E", "password": "test1234", "phone": "9333333335"})

    t.join(timeout=20)
    got_live = any(ev.get("notification_type") == "new_patient_registered" for ev in sse_results)
    check("SSE delivered live new-patient event to admin", got_live, f"got {sse_results[:2]}")

    # 9. Unauthenticated SSE rejected
    req = urllib.request.Request(BASE + "/api/notifications/stream", method="GET")
    try:
        urllib.request.urlopen(req, timeout=10)
        check("SSE without token -> 401", False, "was 200")
    except urllib.error.HTTPError as e:
        check("SSE without token -> 401", e.code == 401, f"got {e.code}")

    # 10. Notification failure never breaks the business operation
    os.environ.setdefault("DATABASE_URL", "postgresql://careflow:careflow_secret@localhost:5432/careflow_ai")
    from app.services.notification import create_notification
    from app.models.notification import NotificationType as _NT
    r = create_notification(
        recipient_id=999999999,
        title="should never persist",
        message="bogus recipient",
        notification_type=_NT.NEW_PATIENT_REGISTERED,
    )
    check("notification creation failure swallowed (returns None)", r is None, f"got {r}")

    # Business op still works after a failed notification attempt
    code, appt2 = call("POST", "/api/appointments", {"doctor_id": 1, "appointment_date": "2026-09-27", "appointment_time": "09:00"}, token=pb_token)
    if code != 201:
        for d in range(10, 31):
            code, appt2 = call("POST", "/api/appointments", {"doctor_id": 1, "appointment_date": f"2026-09-{d:02d}", "appointment_time": "09:00"}, token=pb_token)
            if code == 201:
                break
    check("booking still works (201)", code == 201 and appt2.get("id"), f"got {code}")
    vcode2 = _confirm_appt(pb_token, appt2["id"])
    check("payment still works after notification failure (200)", vcode2 == 200, f"got {vcode2}")
    qdate2 = appt2["appointment_date"]
    code, _ = call("POST", "/api/admin/tokens/call-next", {"doctor_id": 1, "queue_date": qdate2}, token=admin_token)
    check("token call still works (200)", code == 200, f"got {code}")
    call("POST", "/api/admin/tokens/start-consultation", {"doctor_id": 1, "queue_date": qdate2}, token=admin_token)
    code, _ = call("POST", "/api/admin/tokens/complete", {"doctor_id": 1, "queue_date": qdate2}, token=admin_token)
    check("consultation completion still works (200)", code == 200, f"got {code}")

    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()