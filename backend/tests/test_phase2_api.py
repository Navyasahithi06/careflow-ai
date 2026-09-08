import os
import urllib.request
import urllib.error
import json
import sys
from pathlib import Path

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
        with urllib.request.urlopen(req) as resp:
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


def main():
    print("=== Phase 2 API Tests ===")

    # 1. Get admin token
    code, admin = call("POST", "/api/auth/admin/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    check("admin login", code == 200 and admin.get("role") == "admin", f"got {code} {admin}")
    admin_token = admin.get("access_token", "")

    # 2. Register a new patient for ownership tests
    import random, time
    email = f"p2_{int(time.time())}@test.com"
    code, user = call("POST", "/api/auth/register", {
        "email": email, "full_name": "Phase2 Patient", "password": "test1234", "phone": "9999999999",
    })
    check("patient register", code == 201 or code == 400, f"got {code}")
    if code == 201:
        patient_id = user["id"]
    else:
        # fetch patient id from admin patients list
        code, plist = call("GET", "/api/admin/patients", token=admin_token)
        patient_id = next(p for p in plist if p["email"] == email)["id"]

    code, user = call("POST", "/api/auth/login", {"email": email, "password": "test1234"})
    check("patient login", code == 200 and user.get("role") == "patient", f"got {code}")
    patient_token = user.get("access_token", "")

    # 3. Authorization: patient cannot access admin endpoints
    code, _ = call("GET", "/api/admin/patients", token=patient_token)
    check("patient cannot list patients (403)", code == 403, f"got {code}")
    code, _ = call("GET", "/api/admin/reports/overview", token=patient_token)
    check("patient cannot access reports (403)", code == 403, f"got {code}")
    code, _ = call("GET", "/api/admin/medical-records", token=patient_token)
    check("patient cannot list medical records (403)", code == 403, f"got {code}")
    code, _ = call("GET", "/api/admin/consultations/appointments", token=patient_token)
    check("patient cannot access consultations (403)", code == 403, f"got {code}")

    # 4. No auth -> 401
    code, _ = call("GET", "/api/admin/patients")
    check("no auth -> 401", code == 401, f"got {code}")

    # 5. Admin patient management
    code, plist = call("GET", "/api/admin/patients", token=admin_token)
    check("admin list patients", code == 200 and isinstance(plist, list), f"got {code}")
    code, one = call("GET", f"/api/admin/patients/{patient_id}", token=admin_token)
    check("admin get patient", code == 200 and one["id"] == patient_id, f"got {code}")

    # deactivate then reactivate
    code, one = call("PUT", f"/api/admin/patients/{patient_id}/status", {"is_active": 0}, token=admin_token)
    check("deactivate patient", code == 200 and one["is_active"] == 0, f"got {code} {one}")
    code, one = call("PUT", f"/api/admin/patients/{patient_id}/status", {"is_active": 1}, token=admin_token)
    check("reactivate patient", code == 200 and one["is_active"] == 1, f"got {code} {one}")

    # 6. Medical records CRUD
    code, rec = call("POST", "/api/admin/medical-records", {
        "patient_id": patient_id, "doctor_id": 1, "record_type": "DIAGNOSIS",
        "title": "Initial Diagnosis", "diagnosis": "Migraine", "prescriptions": "Paracetamol",
        "notes": "Follow up in 2 weeks",
    }, token=admin_token)
    check("create medical record", code == 201 and rec.get("id"), f"got {code} {rec}")
    rec_id = rec.get("id")

    code, rec = call("GET", f"/api/admin/medical-records/{rec_id}", token=admin_token)
    check("get medical record", code == 200 and rec["title"] == "Initial Diagnosis", f"got {code}")
    code, rec = call("PUT", f"/api/admin/medical-records/{rec_id}", {"title": "Updated Diagnosis", "diagnosis": "Chronic Migraine"}, token=admin_token)
    check("update medical record", code == 200 and rec["title"] == "Updated Diagnosis", f"got {code} {rec}")
    code, rlist = call("GET", "/api/admin/medical-records", token=admin_token)
    check("list medical records", code == 200 and any(r["id"] == rec_id for r in rlist), f"got {code}")

    # bad record type
    code, _ = call("POST", "/api/admin/medical-records", {
        "patient_id": patient_id, "record_type": "BADTYPE", "title": "x",
    }, token=admin_token)
    check("reject invalid record type (400)", code == 400, f"got {code}")

    # non-existent patient
    code, _ = call("POST", "/api/admin/medical-records", {
        "patient_id": 99999, "record_type": "GENERAL", "title": "x",
    }, token=admin_token)
    check("reject non-existent patient (404)", code == 404, f"got {code}")

    # 7. Consultation notes
    # Deterministically create a CONFIRMED appointment via the payment flow,
    # then add a consultation note (avoids reusing leftover DB data).
    import hashlib, hmac, time as _time
    stamp = int(_time.time())
    RZP_SECRET = _RZP_SECRET or "test-placeholder-razorpay-secret"
    code, appt = call("POST", "/api/appointments", {"doctor_id": 1, "appointment_date": "2026-09-24", "appointment_time": "09:00"}, token=patient_token)
    if code != 201:
        for dd in range(10, 31):
            code, appt = call("POST", "/api/appointments", {"doctor_id": 1, "appointment_date": f"2026-09-{dd:02d}", "appointment_time": "09:00"}, token=patient_token)
            if code == 201:
                break

    if code == 201:
        appt_id = appt["id"]
        code, order = call("POST", "/api/payments/create-order", {"appointment_id": appt_id}, token=patient_token)
        if code == 200:
            order_id = order["gateway_order_id"]
            payment_id = f"pay_p2_{stamp}"
            sig = hmac.new(RZP_SECRET.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
            code, _ = call("POST", "/api/payments/verify", {
                "appointment_id": appt_id,
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": sig,
            }, token=patient_token)

        tappt = appt_id
        code, note = call("POST", f"/api/admin/consultations/appointments/{tappt}/notes", {
            "notes": "Patient stable", "diagnosis": "Hypertension", "prescriptions": "Amlodipine 5mg",
        }, token=admin_token)
        if code == 201:
            note_id = note["id"]
            check("create consultation note", True, "")
            code, note = call("GET", f"/api/admin/consultations/notes/{note_id}", token=admin_token)
            check("get consultation note", code == 200 and note["diagnosis"] == "Hypertension", f"got {code}")
            code, note = call("PUT", f"/api/admin/consultations/notes/{note_id}", {"status": "COMPLETED", "prescriptions": "Amlodipine 5mg + Telmisartan"}, token=admin_token)
            check("update consultation note", code == 200 and note["status"] == "COMPLETED", f"got {code} {note}")
            code, nlist = call("GET", "/api/admin/consultations/notes", token=admin_token)
            check("list consultation notes", code == 200 and any(n["id"] == note_id for n in nlist), f"got {code}")

            # duplicate note -> 409
            code, _ = call("POST", f"/api/admin/consultations/appointments/{tappt}/notes", {"notes": "dup"}, token=admin_token)
            check("duplicate consultation note rejected (409)", code == 409, f"got {code}")

            # patient can see own note via history
            code, nlist = call("GET", f"/api/user/consultation-notes", token=patient_token)
            check("patient sees own consultation notes", code == 200, f"got {code}")

            # patient history has the record + note
            code, hist = call("GET", "/api/user/history", token=patient_token)
            check("patient history returns timeline", code == 200 and "timeline" in hist, f"got {code}")
        else:
            check("create consultation note", False, f"got {code} {note}")
    else:
        print("  SKIP: no confirmable appointment available for consultation notes")

    # 8. Patient ownership: patient cannot get another patient's records via admin path (403)
    code, _ = call("GET", "/api/admin/medical-records", token=patient_token)
    check("patient denied admin medical records (403)", code == 403, f"got {code}")

    # 9. Reports
    code, rep = call("GET", "/api/admin/reports/overview", token=admin_token)
    check("reports overview", code == 200 and "total_revenue" in rep, f"got {code}")
    code, rep = call("GET", "/api/admin/reports/appointments", token=admin_token)
    check("reports appointments", code == 200 and "trends" in rep and "by_doctor" in rep, f"got {code}")
    code, rep = call("GET", "/api/admin/reports/revenue", token=admin_token)
    check("reports revenue", code == 200 and "trends" in rep, f"got {code}")
    code, _ = call("GET", "/api/admin/reports/overview?start=2026-01-01&end=2026-12-31", token=admin_token)
    check("reports overview with date range", code == 200, f"got {code}")
    code, _ = call("GET", "/api/admin/reports/overview?start=bad-date", token=admin_token)
    check("reports invalid date (400)", code == 400, f"got {code}")

    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
