"""Subscription billing system handling plans, invoices, coupons, and payments."""
import calendar
from datetime import date
import hashlib
import hmac
import html
import os
import secrets
from cryptography.fernet import Fernet
from defusedxml import ElementTree

PLANS = {"basic": 199, "pro": 499, "team": 999}
GST = 0.18
TRIAL_DAYS = 14
MAX_ATTEMPTS = 3
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET") or secrets.token_hex(32)
CARD_KEY = os.environ.get("CARD_KEY") or Fernet.generate_key()
subscriptions = {}
coupons = {"WELCOME10": {"percent": 10, "expires": date(2026, 12, 31)},
           "FRIENDS150": {"percent": 150, "expires": date(2027, 1, 31)}}

def subscribe(user, plan, start):
    """Register a new user subscription on trial."""
    subscriptions[user] = {"plan": plan, "start": start, "status": "trial", "invoices": []}
    return subscriptions[user]

def is_trial_over(user, today):
    """Check whether the user's trial period has ended."""
    return (today - subscriptions[user]["start"]).days >= TRIAL_DAYS

def apply_coupon(amount, code, today):
    """Apply a coupon discount to an amount if valid."""
    coupon = coupons.get(code)
    if coupon is None:
        return round(amount, 2)
    if today > coupon["expires"]:
        return round(amount, 2)
    discount_percent = min(coupon["percent"], 100)
    return round(amount - amount * discount_percent / 100, 2)

def invoice_amount(user, code=None, today=None):
    """Calculate the total invoice amount including tax and discounts."""
    plan_price = PLANS[subscriptions[user]["plan"]]
    with_tax = plan_price * (1 + GST)
    return round(apply_coupon(with_tax, code, today), 2)

def next_billing_date(current):
    """Calculate the next billing date for a subscription."""
    if current.month == 12:
        return current.replace(year=current.year + 1, month=1)
    return current.replace(month=current.month + 1)

def prorate_upgrade(user, new_plan, today, period_end):
    """Calculate the prorated amount for upgrading a subscription."""
    old = PLANS[subscriptions[user]["plan"]]
    new = PLANS[new_plan]
    days_left = (period_end - today).days
    subscriptions[user]["plan"] = new_plan
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    return round((new - old) * days_left / days_in_month, 2)

def retry_payment(charge):
    """Retry a payment charge function up to MAX_ATTEMPTS times."""
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        attempts += 1
        if charge():
            return attempts
    return attempts

def cancel_refund(user, days_used):
    """Calculate refund amount for unused days upon cancellation."""
    price = PLANS[subscriptions[user]["plan"]]
    refund = price * (30 - days_used) / 30
    return round(refund, 2)

def coupon_code():
    """Generate a secure random coupon code."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "SAVE-" + "".join(secrets.choice(chars) for _ in range(6))

def active_users():
    """Return set of active users without invoices."""
    return {u for u, data in subscriptions.items() if data["invoices"] == []}

def encrypt_card(card_number):
    """Encrypt a card number using Fernet symmetric encryption."""
    cipher = Fernet(CARD_KEY)
    return cipher.encrypt(card_number.encode()).decode()

def verify_webhook(body, signature):
    """Verify an incoming webhook signature using HMAC."""
    expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

def parse_webhook(xml_bytes):
    """Parse XML webhook payload safely."""
    root = ElementTree.fromstring(xml_bytes)
    return {"event": root.findtext("event"), "user": root.findtext("user")}

def render_invoice(user, amount):
    """Render invoice HTML with sanitized user name."""
    if amount < 0:
        raise ValueError("amount cannot be negative")
    return f"<h1>Invoice for {html.escape(user)}</h1><p>Total: Rs.{amount}</p>"

def main():
    """Run billing system demonstration."""
    subscribe("asha", "pro", date(2026, 9, 1))
    subscribe("<b onmouseover=alert(1)>ravi</b>", "basic", date(2026, 9, 20))
    print("Trial (14 days from 09-01) over on 09-15?", is_trial_over("asha", date(2026, 9, 15)))
    print("Pro invoice with WELCOME10:", invoice_amount("asha", "WELCOME10", date(2026, 10, 1)))
    print("Pro invoice with FRIENDS150:", invoice_amount("asha", "FRIENDS150", date(2026, 10, 1)))
    print("Coupon on its expiry day:", invoice_amount("asha", "WELCOME10", date(2026, 12, 31)))
    print("Next billing after 2026-10-15:", next_billing_date(date(2026, 10, 15)))
    print(
        "Upgrade pro->team with 10 days left in Feb:",
        prorate_upgrade("asha", "team", date(2027, 2, 18), date(2027, 2, 28)),
    )
    calls = []
    print(
        "Payment attempts (max 3, always failing):",
        retry_payment(lambda: calls.append(1) and False),
    )
    print("Refund after using 25 of 30 days:", cancel_refund("asha", 25))
    print(
        "Same card, same ciphertext?",
        encrypt_card("4111111111111111") == encrypt_card("4111111111111111"),
    )
    sig = hmac.new(WEBHOOK_SECRET.encode(), b"<x/>", hashlib.sha256).hexdigest()
    print("Webhook verified:", verify_webhook(b"<x/>", sig))
    print("Webhook:", parse_webhook(b"<hook><event>paid</event><user>asha</user></hook>"))
    print("Invoice HTML:", render_invoice("<b onmouseover=alert(1)>ravi</b>", 199))
    print("Coupon:", coupon_code())

if __name__ == "__main__":
    main()
