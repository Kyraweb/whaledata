import os
import secrets
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_connection

router = APIRouter(prefix="/alerts", tags=["Alerts"])

API_URL = os.getenv("API_URL", "https://api.whaledata.org")
MAP_URL = os.getenv("MAP_URL", "https://whaledata.org")


class SubscribeRequest(BaseModel):
    email: EmailStr
    species_filter: Optional[str] = None
    region_filter:  Optional[str] = None
    layer_filter:   Optional[str] = None


def send_confirmation_email(email: str, token: str, prefs: dict):
    """Send double opt-in confirmation email via AWS SES."""
    import boto3
    from botocore.exceptions import ClientError

    confirm_url     = f"{API_URL}/alerts/confirm/{token}"
    unsubscribe_url = f"{API_URL}/alerts/unsubscribe/{token}"

    prefs_lines = []
    if prefs.get("species_filter"): prefs_lines.append(f"Species: {prefs['species_filter']}")
    if prefs.get("region_filter"):  prefs_lines.append(f"Region: {prefs['region_filter']}")
    if prefs.get("layer_filter"):   prefs_lines.append(f"Layer: {prefs['layer_filter']}")
    prefs_text = "\n".join(prefs_lines) if prefs_lines else "All sightings (no filter)"
    prefs_html = "<br>".join(prefs_lines) if prefs_lines else "All sightings — no filter applied"

    subject = "Confirm your whaledata.org alerts"

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#050810;font-family:'Helvetica Neue',Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 20px">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#0d1528;border-radius:16px;overflow:hidden;border:1px solid rgba(0,229,255,0.15)">

        <!-- Header -->
        <tr><td style="padding:32px 40px 24px;border-bottom:1px solid rgba(255,255,255,0.06)">
          <div style="font-size:22px;font-weight:700;color:#e8f4f8">🐋 whaledata<span style="color:#00e5ff">.org</span></div>
          <div style="font-size:13px;color:#7a9bb5;margin-top:4px">Global whale sightings map</div>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:32px 40px">
          <h2 style="color:#e8f4f8;font-size:18px;margin:0 0 12px">Confirm your weekly alerts</h2>
          <p style="color:#7a9bb5;font-size:14px;line-height:1.7;margin:0 0 24px">
            You signed up for weekly whale sighting alerts. Click the button below to confirm your email address.
          </p>

          <div style="background:rgba(0,229,255,0.06);border:1px solid rgba(0,229,255,0.15);border-radius:10px;padding:16px 20px;margin-bottom:28px">
            <div style="font-size:11px;color:#7a9bb5;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Your alert preferences</div>
            <div style="color:#e8f4f8;font-size:14px;line-height:1.8">{prefs_html}</div>
          </div>

          <a href="{confirm_url}" style="display:inline-block;background:rgba(0,229,255,0.1);border:1px solid rgba(0,229,255,0.3);color:#00e5ff;text-decoration:none;padding:14px 32px;border-radius:30px;font-size:14px;font-weight:600">
            ✓ Confirm my alerts
          </a>

          <p style="color:#3d5a72;font-size:12px;margin:28px 0 0;line-height:1.7">
            If you didn't sign up for this, just ignore this email — no action needed.<br>
            <a href="{unsubscribe_url}" style="color:#3d5a72">Unsubscribe</a>
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:20px 40px;border-top:1px solid rgba(255,255,255,0.06)">
          <div style="color:#3d5a72;font-size:11px">
            whaledata.org · <a href="{MAP_URL}" style="color:#3d5a72">Visit the map</a>
          </div>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    text = f"""Confirm your whaledata.org alerts

You signed up for weekly whale sighting alerts.

Your preferences:
{prefs_text}

Confirm here: {confirm_url}

If you didn't sign up, ignore this email.
Unsubscribe: {unsubscribe_url}
"""

    client = boto3.client("ses", region_name=os.getenv("AWS_SES_REGION", "us-east-2"))
    try:
        client.send_email(
            Source="alerts@whaledata.org",
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html, "Charset": "UTF-8"},
                    "Text": {"Data": text, "Charset": "UTF-8"},
                },
            },
        )
        return True
    except ClientError as e:
        print(f"[SES ERROR] {e.response['Error']['Message']}")
        return False


# ── Subscribe ─────────────────────────────────────────────────

@router.post("/subscribe")
def subscribe(req: SubscribeRequest):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        # Check if already subscribed
        cur.execute("SELECT id, confirmed FROM alert_subscribers WHERE email = %s;", (req.email,))
        existing = cur.fetchone()

        if existing:
            if existing["confirmed"]:
                return {"status": "already_subscribed", "message": "This email is already subscribed."}
            else:
                # Resend confirmation
                cur.execute("SELECT token FROM alert_subscribers WHERE email = %s;", (req.email,))
                row = cur.fetchone()
                send_confirmation_email(req.email, row["token"], req.dict())
                return {"status": "pending", "message": "Confirmation email resent. Please check your inbox."}

        token = secrets.token_urlsafe(32)
        cur.execute("""
            INSERT INTO alert_subscribers (email, token, species_filter, region_filter, layer_filter)
            VALUES (%s, %s, %s, %s, %s);
        """, (req.email, token, req.species_filter, req.region_filter, req.layer_filter))
        conn.commit()

        sent = send_confirmation_email(req.email, token, req.dict())
        if not sent:
            # Roll back the insert so they can retry
            conn.rollback()
            raise HTTPException(status_code=500, detail="Failed to send confirmation email. Please check AWS SES configuration.")

        return {"status": "pending", "message": "Check your email to confirm your subscription."}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ── Confirm ───────────────────────────────────────────────────

@router.get("/confirm/{token}", response_class=HTMLResponse)
def confirm(token: str):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            UPDATE alert_subscribers SET confirmed = TRUE
            WHERE token = %s AND confirmed = FALSE
            RETURNING email;
        """, (token,))
        row = conn.commit() or cur.fetchone()
        # fetchone after commit
        cur.execute("SELECT email FROM alert_subscribers WHERE token = %s;", (token,))
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close()
        conn.close()

    if not row:
        return _page("Already confirmed", "Your subscription is already active.", "Visit the map", MAP_URL)

    return _page(
        "You're subscribed! 🐋",
        f"<strong>{row['email']}</strong> will receive weekly whale sighting alerts.<br><br>You can unsubscribe at any time from the link in any alert email.",
        "Explore the map",
        MAP_URL,
    )


# ── Unsubscribe ───────────────────────────────────────────────

@router.get("/unsubscribe/{token}", response_class=HTMLResponse)
def unsubscribe(token: str):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM alert_subscribers WHERE token = %s RETURNING email;", (token,))
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close()
        conn.close()

    if not row:
        return _page("Already unsubscribed", "This email has been removed from all alerts.", "Visit the map", MAP_URL)

    return _page(
        "Unsubscribed",
        f"<strong>{row['email']}</strong> has been removed from whale sighting alerts.",
        "Visit the map",
        MAP_URL,
    )


# ── HTML response helper ──────────────────────────────────────

def _page(title: str, body: str, cta: str, url: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title} — whaledata.org</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #050810; font-family: 'Helvetica Neue', Arial, sans-serif;
            display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }}
    .card {{ background: #0d1528; border: 1px solid rgba(0,229,255,0.15); border-radius: 16px;
             padding: 40px; max-width: 480px; text-align: center; }}
    .whale {{ font-size: 48px; margin-bottom: 16px; }}
    h1 {{ color: #e8f4f8; font-size: 22px; margin-bottom: 12px; }}
    p {{ color: #7a9bb5; font-size: 14px; line-height: 1.7; margin-bottom: 28px; }}
    a {{ display: inline-block; background: rgba(0,229,255,0.1); border: 1px solid rgba(0,229,255,0.3);
         color: #00e5ff; text-decoration: none; padding: 12px 28px; border-radius: 30px;
         font-size: 14px; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="whale">🐋</div>
    <h1>{title}</h1>
    <p>{body}</p>
    <a href="{url}">{cta} →</a>
  </div>
</body>
</html>"""


# ── Contact form ──────────────────────────────────────────────

class ContactRequest(BaseModel):
    name:    str = ""
    email:   EmailStr
    subject: str = "other"
    message: str


@router.post("/contact")
def contact(req: ContactRequest):
    """Send a contact form submission to alerts@whaledata.org via SES."""
    import boto3
    from botocore.exceptions import ClientError

    subject_labels = {
        "bug": "Bug Report",
        "suggestion": "Suggestion / Feature Request",
        "data": "Data Question",
        "collaboration": "Collaboration Inquiry",
        "other": "General Enquiry",
    }
    label = subject_labels.get(req.subject, "Message")

    html = f"""
<html><body style="font-family:Arial,sans-serif;padding:20px;background:#f5f5f5">
<div style="background:white;padding:24px;border-radius:8px;max-width:560px">
  <h2 style="color:#0a1628;margin-top:0">whaledata.org — {label}</h2>
  <p><strong>From:</strong> {req.name or "—"} &lt;{req.email}&gt;</p>
  <p><strong>Subject:</strong> {label}</p>
  <hr style="border:1px solid #eee">
  <p style="white-space:pre-wrap">{req.message}</p>
</div>
</body></html>"""

    text = f"whaledata.org contact form\n\nFrom: {req.name} <{req.email}>\nSubject: {label}\n\n{req.message}"

    try:
        client = boto3.client("ses", region_name=os.getenv("AWS_SES_REGION", "us-east-2"))
        client.send_email(
            Source="alerts@whaledata.org",
            Destination={"ToAddresses": ["alerts@whaledata.org"]},
            ReplyToAddresses=[req.email],
            Message={
                "Subject": {"Data": f"[whaledata.org] {label}", "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html, "Charset": "UTF-8"},
                    "Text": {"Data": text, "Charset": "UTF-8"},
                },
            },
        )
        return {"status": "sent"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
