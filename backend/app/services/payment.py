import hmac
import hashlib
import time
from decimal import Decimal
from typing import Optional
import httpx
from app.config import get_settings

settings = get_settings()

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"


def _get_auth():
    return (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)


async def create_razorpay_order(amount: Decimal, currency: str, receipt: str) -> dict:
    """Create a Razorpay order. Amount must be in paise (INR)."""
    amount_paise = int(amount * 100)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{RAZORPAY_API_BASE}/orders",
            auth=_get_auth(),
            json={
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt,
                "payment_capture": 1,
            },
        )
        if response.status_code != 200:
            raise Exception(f"Razorpay order creation failed: {response.text}")
        return response.json()


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature using HMAC SHA256."""
    payload = f"{order_id}|{payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook signature."""
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return False
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
