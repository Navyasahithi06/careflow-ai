import os
import urllib.request
import urllib.error
import json
import uuid
import sys
import time
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
BOUNDARY = uuid.uuid4().hex


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


def call_upload(path, filename, content, mime, token=None):
    """Multipart POST upload against the live backend."""
    parts = []
    parts.append(
        (
            f"--{BOUNDARY}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode()
    )
    parts.append(content)
    parts.append(f"\r\n--{BOUNDARY}--\r\n".encode())
    data = b"".join(parts)
    url = BASE + path
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={BOUNDARY}")
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


def download(path, token=None):
    url = BASE + path
    req = urllib.request.Request(url, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("Content-Type", "")


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
    print("=== Phase 3 Checkpoint 1: Attachments API Tests ===")
    stamp = int(time.time())

    # 0. Admin login
    code, admin = call("POST", "/api/auth/admin/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    check("admin login", code == 200 and admin.get("role") == "admin", f"got {code} {admin}")
    admin_token = admin.get("access_token", "")

    # 1. Register two patients
    emA = f"att_pa_{stamp}@test.com"
    emB = f"att_pb_{stamp}@test.com"
    code, pa = call("POST", "/api/auth/register", {"email": emA, "full_name": "Att Patient A", "password": "test1234", "phone": "9111111111"})
    check("register patient A", code == 201 and pa.get("id"), f"got {code} {pa}")
    pa_token = call("POST", "/api/auth/login", {"email": emA, "password": "test1234"})[1].get("access_token", "")
    seq = 0
    if code != 201:
        seq += 1
        emA = f"att_pa_{stamp}_{seq}@test.com"
        call("POST", "/api/auth/register", {"email": emA, "full_name": "Att Patient A", "password": "test1234", "phone": "9111111111"})
        pa = call("POST", "/api/auth/login", {"email": emA, "password": "test1234"})[1]
        pa_token = pa.get("access_token", "")

    code, pb = call("POST", "/api/auth/register", {"email": emB, "full_name": "Att Patient B", "password": "test1234", "phone": "9222222222"})
    if code != 201:
        emB = f"att_pb_{stamp}_{seq + 1}@test.com"
        call("POST", "/api/auth/register", {"email": emB, "full_name": "Att Patient B", "password": "test1234", "phone": "9222222222"})
        pb = call("POST", "/api/auth/login", {"email": emB, "password": "test1234"})[1]
    else:
        pb = call("POST", "/api/auth/login", {"email": emB, "password": "test1234"})[1]
    pb_token = pb.get("access_token", "")

    # 2. Upload validation
    code, _ = call_upload("/api/attachments/upload", "report.pdf", b"%PDF-1.4 test report", "application/pdf")
    check("upload without token -> 401", code == 401, f"got {code}")

    code, res = call_upload("/api/attachments/upload", "malware.html", b"<script>alert(1)</script>", "text/html", token=pa_token)
    check("reject unsupported mime (400)", code == 400, f"got {code} {res}")

    big = b"0" * (5 * 1024 * 1024 + 1)
    code, _ = call_upload("/api/attachments/upload", "big.pdf", big, "application/pdf", token=pa_token)
    check("reject oversize file (400)", code == 400, f"got {code}")

    # 3. Patient A uploads a PDF and a PNG
    code, attA_pdf = call_upload("/api/attachments/upload", "blood-report.pdf", b"%PDF-1.4 patient A report", "application/pdf", token=pa_token)
    check("patient A uploads pdf (201)", code == 201 and attA_pdf.get("file_name") == "blood-report.pdf", f"got {code} {attA_pdf}")
    attA_pdf_id = attA_pdf.get("id")

    code, attA_png = call_upload("/api/attachments/upload", "prescription.png", b"\x89PNG\r\n\x1a\n fake image content", "image/png", token=pa_token)
    check("patient A uploads png (201)", code == 201 and attA_png.get("id"), f"got {code} {attA_png}")
    attA_png_id = attA_png.get("id")

    # 4. Attach to a medical record (ownership + authorization)
    code, rec = call("POST", "/api/admin/medical-records", {
        "patient_id": pa["id"], "doctor_id": 1, "record_type": "LAB_REPORT",
        "title": "Blood Report", "diagnosis": "NAD",
    }, token=admin_token)
    check("admin creates medical record for patient A (201)", code == 201 and rec.get("id"), f"got {code} {rec}")
    rec_id = rec.get("id")

    # Patient B must not attach to patient A's record
    code, _ = call("POST", f"/api/attachments/entity/medical_record/{rec_id}", {"attachment_id": attA_pdf_id}, token=pb_token)
    check("patient B cannot attach to patient A record (403)", code == 403, f"got {code}")

    # Patient A attaches own file to own record
    code, lst = call("POST", f"/api/attachments/entity/medical_record/{rec_id}", {"attachment_id": attA_pdf_id}, token=pa_token)
    check("patient A attaches pdf to own record (200)", code == 200 and any(a["id"] == attA_pdf_id for a in lst), f"got {code} {lst}")

    # Attaching again to same entity -> 409
    code, _ = call("POST", f"/api/attachments/entity/medical_record/{rec_id}", {"attachment_id": attA_pdf_id}, token=pa_token)
    check("reattaching same attachment -> 409", code == 409, f"got {code}")

    # 5. List
    code, lst = call("GET", f"/api/attachments/entity/medical_record/{rec_id}", token=pa_token)
    check("patient A lists own record attachments", code == 200 and len(lst) == 1 and lst[0]["id"] == attA_pdf_id, f"got {code} {lst}")
    code, lst = call("GET", f"/api/attachments/entity/medical_record/{rec_id}", token=pb_token)
    check("patient B cannot list patient A record attachments (403)", code == 403, f"got {code}")
    code, lst = call("GET", f"/api/attachments/entity/medical_record/{rec_id}", token=admin_token)
    check("admin lists record attachments", code == 200 and len(lst) == 1, f"got {code} {lst}")

    # patient B cannot list a nonexistent/other's consultation either (invalid entity type)
    code, _ = call("GET", "/api/attachments/entity/badtype/1", token=pa_token)
    check("reject invalid entity type (400)", code == 400, f"got {code}")

    # 6. Download: owner + admin OK, other patient 403
    code, data, ctype = download(f"/api/attachments/{attA_pdf_id}/download", token=pa_token)
    check("patient A downloads own attachment (200)", code == 200 and ctype == "application/pdf" and data == b"%PDF-1.4 patient A report", f"got {code} {ctype}")
    code, data, ctype = download(f"/api/attachments/{attA_pdf_id}/download", token=admin_token)
    check("admin downloads attachment (200)", code == 200 and data == b"%PDF-1.4 patient A report", f"got {code}")
    code, _, _ = download(f"/api/attachments/{attA_pdf_id}/download", token=pb_token)
    check("patient B cannot download patient A attachment (403)", code == 403, f"got {code}")

    # 7. Attach to a consultation note
    # Deterministically create a CONFIRMED appointment for patient A via the payment
    # create-order + locally-computed HMAC verify flow, then add a consultation note.
    import hashlib, hmac
    RZP_SECRET = _RZP_SECRET or "test-placeholder-razorpay-secret"
    code, appt = call(
        "POST", "/api/appointments",
        {"doctor_id": 2, "appointment_date": "2026-09-25", "appointment_time": "10:00"},
        token=pa_token,
    )
    if code != 201:
        # Slot may be taken by a prior run; find a free slot over the next days
        for d in range(10, 31):
            code, appt = call(
                "POST", "/api/appointments",
                {"doctor_id": 2, "appointment_date": f"2026-09-{d:02d}", "appointment_time": "10:00"},
                token=pa_token,
            )
            if code == 201:
                break
    check("patient A books an appointment (201)", code == 201 and appt.get("id"), f"got {code} {appt}")
    appt_id = appt.get("id")
    note_id = None
    if code == 201:
        code, order = call("POST", "/api/payments/create-order", {"appointment_id": appt_id}, token=pa_token)
        check("create-order succeeds (200)", code == 200 and order.get("gateway_order_id"), f"got {code} {order}")
        if code == 200:
            order_id = order["gateway_order_id"]
            payment_id = f"pay_test_{stamp}"
            sig = hmac.new(RZP_SECRET.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
            code, vresp = call("POST", "/api/payments/verify", {
                "appointment_id": appt_id,
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": sig,
            }, token=pa_token)
            check("patient A payment verified / appointment confirmed (200)", code == 200, f"got {code} {vresp}")
            code, note = call("POST", f"/api/admin/consultations/appointments/{appt_id}/notes", {"notes": "Consult report attached", "diagnosis": "BP check"}, token=admin_token)
            check("admin creates consultation note (201)", code == 201 and note.get("id"), f"got {code} {note}")
            note_id = note.get("id")

    if note_id:
        code, _ = call("POST", f"/api/attachments/entity/consultation/{note_id}", {"attachment_id": attA_png_id}, token=pb_token)
        check("patient B cannot attach to patient A consultation (403)", code == 403, f"got {code}")

        code, lst = call("POST", f"/api/attachments/entity/consultation/{note_id}", {"attachment_id": attA_png_id}, token=pa_token)
        check("patient A attaches png to own consultation (200)", code == 200 and any(a["id"] == attA_png_id for a in lst), f"got {code} {lst}")

        code, lst = call("GET", f"/api/attachments/entity/consultation/{note_id}", token=pa_token)
        check("patient A lists own consultation attachments", code == 200 and lst[0]["id"] == attA_png_id, f"got {code} {lst}")

        # Same attachment cannot be linked to another entity (medical record)
        code, _ = call("POST", f"/api/attachments/entity/medical_record/{rec_id}", {"attachment_id": attA_png_id}, token=pa_token)
        check("attachment already linked elsewhere -> 409", code == 409, f"got {code}")

        # Admin attaches a second file to the consultation
        code, attA_txt = call_upload("/api/attachments/upload", "notes.txt", b"some text notes", "text/plain", token=admin_token)
        check("admin uploads txt (201)", code == 201 and attA_txt.get("id"), f"got {code} {attA_txt}")
        code, lst = call("POST", f"/api/attachments/entity/consultation/{note_id}", {"attachment_id": attA_txt["id"]}, token=admin_token)
        check("admin attaches file to consultation (200)", code == 200 and len(lst) == 2, f"got {code} {lst}")

    # 8. Delete/detach
    # Admin deletes the PDF attachment on the medical record
    code, _ = call("DELETE", f"/api/attachments/{attA_pdf_id}", token=pb_token)
    check("patient B cannot delete patient A attachment (403)", code == 403, f"got {code}")

    code, _ = call("DELETE", f"/api/attachments/{attA_pdf_id}", token=admin_token)
    check("admin deletes attachment (200)", code == 200, f"got {code}")

    code, lst = call("GET", f"/api/attachments/entity/medical_record/{rec_id}", token=admin_token)
    check("record attachments list empty after delete", code == 200 and len(lst) == 0, f"got {code} {lst}")

    code, data, ctype = download(f"/api/attachments/{attA_pdf_id}/download", token=admin_token)
    check("download deleted attachment -> 404", code == 404, f"got {code}")

    code, _ = call("DELETE", "/api/attachments/999999", token=admin_token)
    check("delete nonexistent attachment -> 404", code == 404, f"got {code}")

    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()