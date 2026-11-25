"""
ShopNow - Online Shopping System
Email Notification System & Responsive HTML Templates
Built using standard library: smtplib, email, threading, os
"""

import os
import smtplib
import threading
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, 
    SMTP_USE_TLS, SMTP_FROM_EMAIL, SMTP_FROM_NAME, 
    APP_URL, LOGS_DIR
)

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)
OUTBOX_LOG_FILE = os.path.join(LOGS_DIR, 'email_outbox.log')

def _log_email_outbox(to_email, subject, body_summary):
    """
    Records outbound email into local outbox log for auditing and when SMTP is offline.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] TO: {to_email} | SUBJECT: {subject}\nSUMMARY:\n{body_summary}\n{'-'*70}\n"
    try:
        with open(OUTBOX_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write to email outbox log: {e}")

def _send_smtp_worker(to_email, subject, html_body, text_body):
    """
    Worker function executed in a background daemon thread.
    Safely delivers email via SMTP or writes to simulated outbox without blocking checkout.
    """
    # 1. Always log outbox for audit tracking
    _log_email_outbox(to_email, subject, text_body[:300] + ("..." if len(text_body) > 300 else ""))

    # 2. Check if real SMTP server is configured
    if not SMTP_HOST or not SMTP_USER:
        print(f"[Email Service] SMTP not configured. Logged to outbox: '{subject}' -> {to_email}")
        return

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg['To'] = to_email

        part1 = MIMEText(text_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)

        server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
        server.quit()
        print(f"[Email Service] Successfully delivered email to {to_email}")
    except Exception as e:
        print(f"[Email Service Warning] Failed to deliver SMTP email to {to_email}: {e}")

def send_email_async(to_email: str, subject: str, html_body: str, text_body: str):
    """
    Spawns a detached background thread to send email without delaying API responses.
    """
    thread = threading.Thread(
        target=_send_smtp_worker,
        args=(to_email, subject, html_body, text_body),
        daemon=True
    )
    thread.start()

# ----------------------------------------------------------------------
# RESPONSIVE HTML EMAIL TEMPLATES
# ----------------------------------------------------------------------

def _base_email_template(title: str, content_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1f2937; }}
  .email-container {{ max-width: 600px; margin: 30px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e5e7eb; }}
  .email-header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 24px; text-align: center; color: #ffffff; }}
  .email-header h1 {{ margin: 0; font-size: 24px; letter-spacing: -0.5px; }}
  .email-body {{ padding: 32px 24px; line-height: 1.6; font-size: 15px; }}
  .btn-action {{ display: inline-block; padding: 12px 24px; background-color: #2563eb; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
  .table-items {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  .table-items th {{ background-color: #f9fafb; text-align: left; padding: 10px; border-bottom: 2px solid #e5e7eb; font-size: 13px; }}
  .table-items td {{ padding: 10px; border-bottom: 1px solid #f3f4f6; font-size: 14px; }}
  .email-footer {{ background-color: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
  .badge-tag {{ display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; background-color: #e0e7ff; color: #3730a3; }}
</style>
</head>
<body>
<div class="email-container">
  <div class="email-header">
    <h1>🛍️ Shop<span style="color:#fbbf24;">Now</span></h1>
  </div>
  <div class="email-body">
    {content_html}
  </div>
  <div class="email-footer">
    <p>&copy; 2026 ShopNow Online Shopping System. Built for Educational & Production MVP Purposes.</p>
    <p>Please do not reply directly to this automated security message.</p>
  </div>
</div>
</body>
</html>"""

def send_verification_email(to_email: str, user_name: str, raw_token: str):
    """
    Sends account verification email with single-use expiring token.
    """
    verify_url = f"{APP_URL}/verify-email.html?token={raw_token}"
    subject = "Verify Your ShopNow Customer Account"
    
    html = _base_email_template(
        subject,
        f"""<h2>Welcome to ShopNow, {user_name}!</h2>
        <p>Thank you for creating an account with our online shopping system. Please verify your email address to confirm your account and access all customer features.</p>
        <p style="text-align: center;">
            <a href="{verify_url}" class="btn-action">Verify Email Address</a>
        </p>
        <p style="font-size: 13px; color: #6b7280;">This verification link will expire in 24 hours. If the button above does not work, copy and paste this link into your browser:</p>
        <p style="font-size: 12px; word-break: break-all; color: #2563eb;">{verify_url}</p>"""
    )
    text = f"Welcome to ShopNow, {user_name}!\nPlease verify your account by visiting:\n{verify_url}\nThis link expires in 24 hours."
    send_email_async(to_email, subject, html, text)

def send_welcome_email(to_email: str, user_name: str):
    """
    Sends welcome greeting after email address has been verified.
    """
    subject = "Welcome to ShopNow - Account Verified"
    catalog_url = f"{APP_URL}/products.html"

    html = _base_email_template(
        subject,
        f"""<h2>Your Account is Verified!</h2>
        <p>Hello {user_name},</p>
        <p>Your email address has been successfully verified. You can now browse our full product catalog, manage your shopping cart and wishlist, place Cash on Delivery orders, and submit product reviews.</p>
        <p style="text-align: center;">
            <a href="{catalog_url}" class="btn-action">Start Shopping</a>
        </p>"""
    )
    text = f"Hello {user_name},\nYour ShopNow account has been successfully verified!\nStart shopping at: {catalog_url}"
    send_email_async(to_email, subject, html, text)

def send_password_reset_email(to_email: str, user_name: str, raw_token: str):
    """
    Sends single-use password reset link with 30-minute expiration.
    """
    reset_url = f"{APP_URL}/reset-password.html?token={raw_token}"
    subject = "Reset Your ShopNow Password"

    html = _base_email_template(
        subject,
        f"""<h2>Password Reset Request</h2>
        <p>Hello {user_name},</p>
        <p>We received a request to reset the password for your ShopNow account. Click the button below to choose a new secure password:</p>
        <p style="text-align: center;">
            <a href="{reset_url}" class="btn-action" style="background-color: #dc2626;">Reset Password</a>
        </p>
        <p style="font-size: 13px; color: #6b7280;">This single-use link is valid for <strong>30 minutes</strong>. If you did not request a password reset, you can safely ignore this email.</p>
        <p style="font-size: 12px; word-break: break-all; color: #dc2626;">{reset_url}</p>"""
    )
    text = f"Hello {user_name},\nReset your ShopNow password at:\n{reset_url}\nThis link expires in 30 minutes. If you did not request this, ignore this email."
    send_email_async(to_email, subject, html, text)

def send_password_changed_notification(to_email: str, user_name: str):
    """
    Sends security notice when password has been modified.
    """
    subject = "Security Alert: ShopNow Password Changed"

    html = _base_email_template(
        subject,
        f"""<h2>Password Successfully Changed</h2>
        <p>Hello {user_name},</p>
        <p>This is a confirmation that the password for your ShopNow account was recently changed.</p>
        <p>All previous login sessions on other devices have been automatically revoked for your security.</p>
        <p style="color: #dc2626; font-size: 13px;">If you did not perform this change, please contact store support immediately.</p>"""
    )
    text = f"Hello {user_name},\nYour ShopNow account password was successfully changed. All old sessions were revoked. If you did not make this change, contact support."
    send_email_async(to_email, subject, html, text)

def send_order_placed_email(to_email: str, user_name: str, order_id: int, total_amount: float, shipping_address: str, items: list):
    """
    Sends Cash on Delivery order confirmation receipt invoice.
    """
    subject = f"Order Confirmation #ORD-{order_id} - ShopNow"
    order_url = f"{APP_URL}/order-confirmation.html?id={order_id}"

    items_rows = ""
    text_items = ""
    for item in items:
        p_name = item.get('product_name') or item.get('name', 'Product')
        qty = item.get('quantity', 1)
        price = float(item.get('price', 0))
        sub = round(price * qty, 2)
        items_rows += f"<tr><td>{p_name}</td><td>{qty}</td><td>${price:.2f}</td><td>${sub:.2f}</td></tr>"
        text_items += f"- {p_name} x{qty} @ ${price:.2f} = ${sub:.2f}\n"

    html = _base_email_template(
        subject,
        f"""<h2>Thank you for your order, {user_name}!</h2>
        <p>Your order <strong>#ORD-{order_id}</strong> has been placed successfully with <strong>Cash on Delivery (COD)</strong>.</p>
        <div style="background-color: #f9fafb; padding: 16px; border-radius: 6px; margin: 15px 0;">
            <p style="margin: 4px 0;"><strong>Order ID:</strong> #ORD-{order_id}</p>
            <p style="margin: 4px 0;"><strong>Payment Method:</strong> Cash on Delivery (COD)</p>
            <p style="margin: 4px 0;"><strong>Delivery Address:</strong> {shipping_address}</p>
            <p style="margin: 4px 0;"><strong>Status:</strong> <span class="badge-tag">Pending Fulfillment</span></p>
        </div>
        <h3>Items Ordered</h3>
        <table class="table-items">
            <thead>
                <tr><th>Product</th><th>Qty</th><th>Price</th><th>Total</th></tr>
            </thead>
            <tbody>{items_rows}</tbody>
        </table>
        <div style="text-align: right; font-size: 18px; margin-top: 10px;">
            <strong>Total Amount (incl. shipping): ${total_amount:.2f}</strong>
        </div>
        <p style="text-align: center; margin-top: 25px;">
            <a href="{order_url}" class="btn-action">View Order Receipt</a>
        </p>"""
    )
    text = f"Thank you for your order, {user_name}!\nOrder #ORD-{order_id}\nPayment Method: Cash on Delivery\nTotal: ${total_amount:.2f}\nItems:\n{text_items}\nView receipt: {order_url}"
    send_email_async(to_email, subject, html, text)

def send_order_status_update_email(to_email: str, user_name: str, order_id: int, new_status: str, notes: str = None):
    """
    Sends email when order status changes (Confirmed, Shipped, Delivered, Cancelled).
    """
    subject = f"Order #ORD-{order_id} Update: {new_status} - ShopNow"
    order_url = f"{APP_URL}/order-confirmation.html?id={order_id}"

    status_messages = {
        'Confirmed': "Your order has been reviewed and confirmed by our store manager.",
        'Processing': "Your order is being packaged and prepared for dispatch.",
        'Shipped': "Great news! Your package has been dispatched and is on its way to your delivery address.",
        'Delivered': "Your order has been delivered and Cash on Delivery payment received. Thank you for shopping with ShopNow!",
        'Cancelled': "Your order has been cancelled. If you did not request this, please reach out to customer support."
    }
    desc = status_messages.get(new_status, f"The status of your order is now {new_status}.")

    html = _base_email_template(
        subject,
        f"""<h2>Order Status Update: {new_status}</h2>
        <p>Hello {user_name},</p>
        <p>{desc}</p>
        <div style="background-color: #f9fafb; padding: 16px; border-radius: 6px; margin: 15px 0;">
            <p style="margin: 4px 0;"><strong>Order ID:</strong> #ORD-{order_id}</p>
            <p style="margin: 4px 0;"><strong>New Status:</strong> <span class="badge-tag">{new_status}</span></p>
            {f'<p style="margin: 4px 0;"><strong>Notes:</strong> {notes}</p>' if notes else ''}
        </div>
        <p style="text-align: center;">
            <a href="{order_url}" class="btn-action">Track Your Order</a>
        </p>"""
    )
    text = f"Hello {user_name},\nOrder #ORD-{order_id} status updated to {new_status}.\n{desc}\nTrack order: {order_url}"
    send_email_async(to_email, subject, html, text)
