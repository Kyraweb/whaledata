"""
send_weekly_digest.py

Sends weekly whale sighting digest emails to confirmed subscribers.
Queries new records from the past 7 days, filtered by each subscriber's preferences.
Sends via AWS SES.

Usage:
    python -m app.send_weekly_digest
    python -m app.send_weekly_digest --debug   (print emails, don't send)
    python -m app.send_weekly_digest --dry-run (same as debug)
"""

import os
import sys
from datetime import datetime, timedelta
from app.database import get_connection

DEBUG   = "--debug" in sys.argv or "--dry-run" in sys.argv
API_URL = os.getenv("API_URL", "https://api.whaledata.org")
MAP_URL = os.getenv("MAP_URL", "https://whaledata.org")

SPECIES_COLORS = {
    "Humpback whale": "#00e5ff",
    "Blue whale":     "#4d9fff",
    "Grey whale":     "#a8c5da",
    "Sperm whale":    "#7eb8d4",
    "Fin whale":      "#5dd4b8",
    "Orca":           "#ff6b9d",
}

LAYER_LABELS = {
    "sightings":   ("🔵", "Sightings",    "#00e5ff"),
    "strandings":  ("🔴", "Strandings",   "#ff5a5a"),
    "acoustics":   ("🔵", "Acoustics",    "#9664ff"),
    "inaturalist": ("🟢", "iNaturalist",  "#64c864"),
    "historical":  ("🟡", "Historical",   "#ffb432"),
}


def log(msg):
    print(msg, flush=True)


def get_new_records(conn, since: datetime, species: str = None, region: str = None, layer: str = None) -> dict:
    """Get new records from the past 7 days across relevant tables."""
    cur = conn.cursor()
    results = {}

    tables = {
        "sightings":           ("sightings",            "sighted_on",   "common_name", "region"),
        "strandings":          ("strandings",            "stranded_on",  "common_name", "region"),
        "acoustics":           ("acoustics",             "detected_on",  "common_name", "region"),
        "inaturalist":         ("inaturalist_sightings", "observed_on",  "common_name", "region"),
        "historical":          ("historical_sightings",  "sighted_on",   "common_name", "region"),
    }

    # If layer filter set, only query that layer. Otherwise query all.
    target_tables = {layer: tables[layer]} if layer and layer in tables else tables

    for key, (table, date_col, name_col, region_col) in target_tables.items():
        conditions = [f"{date_col} >= %s"]
        params     = [since.strftime("%Y-%m-%d")]

        if species:
            conditions.append(f"{name_col} = %s")
            params.append(species)
        if region:
            conditions.append(f"{region_col} ILIKE %s")
            params.append(f"%{region}%")

        where = "WHERE " + " AND ".join(conditions)

        try:
            cur.execute(f"""
                SELECT {name_col} as species, COUNT(*) as count, MAX({date_col}) as latest
                FROM {table} {where}
                GROUP BY {name_col}
                ORDER BY count DESC;
            """, params)
            rows = cur.fetchall()
            if rows:
                results[key] = rows
        except Exception as e:
            log(f"  [WARN] {table}: {e}")

    cur.close()
    return results


def build_email(subscriber: dict, new_records: dict, since: datetime) -> tuple:
    """Build subject + HTML + text for a subscriber's digest."""
    email   = subscriber["email"]
    token   = subscriber["token"]
    species = subscriber["species_filter"]
    region  = subscriber["region_filter"]
    layer   = subscriber["layer_filter"]

    unsubscribe_url = f"{API_URL}/alerts/unsubscribe/{token}"
    map_url         = MAP_URL

    # Count total new records
    total = sum(sum(r["count"] for r in rows) for rows in new_records.values())

    if total == 0:
        return None, None, None  # Nothing to send

    # Preferences summary
    prefs = []
    if species: prefs.append(f"Species: {species}")
    if region:  prefs.append(f"Region: {region}")
    if layer:   prefs.append(f"Layer: {LAYER_LABELS.get(layer, (None, layer))[1]}")
    prefs_str  = " · ".join(prefs) if prefs else "All sightings"
    week_start = since.strftime("%B %d")
    week_end   = datetime.now().strftime("%B %d, %Y")

    subject = f"🐋 {total:,} new whale records — {week_start} to {week_end}"

    # Build layer rows HTML
    layer_rows_html = ""
    layer_rows_text = ""
    for key, rows in new_records.items():
        icon, label, color = LAYER_LABELS.get(key, ("●", key, "#ffffff"))
        layer_total = sum(r["count"] for r in rows)
        species_list_html = ""
        species_list_text = ""
        for r in rows:
            sp_color = SPECIES_COLORS.get(r["species"], "#7a9bb5")
            species_list_html += f'<span style="display:inline-block;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:3px 10px;margin:2px;font-size:12px;color:{sp_color}">{r["species"]} <strong style="color:#e8f4f8">{r["count"]:,}</strong></span>'
            species_list_text += f"\n    {r['species']}: {r['count']:,}"

        layer_rows_html += f"""
        <tr>
          <td style="padding:14px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
              <span style="font-size:16px">{icon}</span>
              <strong style="color:#e8f4f8;font-size:14px">{label}</strong>
              <span style="color:{color};font-family:monospace;font-size:13px;font-weight:700;margin-left:auto">{layer_total:,} new</span>
            </div>
            <div>{species_list_html}</div>
          </td>
        </tr>"""
        layer_rows_text += f"\n{label}: {layer_total:,} new records{species_list_text}"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#050810;font-family:'Helvetica Neue',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:40px 20px">
<table width="560" cellpadding="0" cellspacing="0" style="background:#0d1528;border-radius:16px;overflow:hidden;border:1px solid rgba(0,229,255,0.15);max-width:100%">

  <!-- Header -->
  <tr><td style="padding:28px 36px 24px;border-bottom:1px solid rgba(255,255,255,0.06)">
    <table width="100%"><tr>
      <td><div style="font-size:20px;font-weight:700;color:#e8f4f8">🐋 whaledata<span style="color:#00e5ff">.org</span></div>
          <div style="font-size:12px;color:#7a9bb5;margin-top:3px">Weekly Sighting Alert</div></td>
      <td align="right"><div style="font-size:11px;color:#3d5a72">{week_start} – {week_end}</div></td>
    </tr></table>
  </td></tr>

  <!-- Summary -->
  <tr><td style="padding:28px 36px">
    <h2 style="color:#e8f4f8;font-size:24px;margin:0 0 6px">{total:,} new records</h2>
    <p style="color:#7a9bb5;font-size:13px;margin:0 0 24px">New whale data added this week matching your preferences: <strong style="color:#e8f4f8">{prefs_str}</strong></p>

    <!-- Layer breakdown -->
    <table width="100%" cellpadding="0" cellspacing="0">
      {layer_rows_html}
    </table>

    <!-- CTA -->
    <div style="text-align:center;margin-top:28px">
      <a href="{map_url}" style="display:inline-block;background:rgba(0,229,255,0.1);border:1px solid rgba(0,229,255,0.3);color:#00e5ff;text-decoration:none;padding:14px 32px;border-radius:30px;font-size:14px;font-weight:600">
        View on the globe →
      </a>
    </div>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:18px 36px;border-top:1px solid rgba(255,255,255,0.06)">
    <div style="color:#3d5a72;font-size:11px;line-height:1.8">
      You're receiving this because you subscribed to whale sighting alerts on whaledata.org.<br>
      Data from GBIF · OBIS · iNaturalist · NOAA<br>
      <a href="{unsubscribe_url}" style="color:#3d5a72">Unsubscribe</a> ·
      <a href="{map_url}" style="color:#3d5a72">Visit whaledata.org</a>
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    text = f"""whaledata.org — Weekly Sighting Alert
{week_start} to {week_end}

{total:,} new records this week
Preferences: {prefs_str}
{layer_rows_text}

View on the map: {map_url}

---
Unsubscribe: {unsubscribe_url}
Data: GBIF · OBIS · iNaturalist · NOAA
"""

    return subject, html, text


def send_email(to: str, subject: str, html: str, text: str) -> bool:
    if DEBUG:
        log(f"\n{'='*50}")
        log(f"TO: {to}")
        log(f"SUBJECT: {subject}")
        log(f"[HTML email — {len(html)} chars]")
        log(f"TEXT:\n{text}")
        return True

    import boto3
    from botocore.exceptions import ClientError

    client = boto3.client("ses", region_name=os.getenv("AWS_SES_REGION", "us-east-2"))
    try:
        client.send_email(
            Source="alerts@whaledata.org",
            Destination={"ToAddresses": [to]},
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
        log(f"  [SES ERROR] {to}: {e.response['Error']['Message']}")
        return False


def run():
    print("=" * 52)
    print("whaledata — Weekly digest")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if DEBUG: print("DEBUG MODE — emails will not be sent")
    print("=" * 52)

    since = datetime.now() - timedelta(days=7)
    conn  = get_connection()
    cur   = conn.cursor()

    # Get all confirmed subscribers
    cur.execute("""
        SELECT id, email, token, species_filter, region_filter, layer_filter
        FROM alert_subscribers
        WHERE confirmed = TRUE;
    """)
    subscribers = cur.fetchall()
    cur.close()

    log(f"\nSubscribers: {len(subscribers)}")

    sent = 0
    skipped = 0

    for sub in subscribers:
        log(f"\n→ {sub['email']}")

        new_records = get_new_records(
            conn,
            since,
            species=sub["species_filter"],
            region=sub["region_filter"],
            layer=sub["layer_filter"],
        )

        subject, html, text = build_email(sub, new_records, since)

        if subject is None:
            log("  No new records — skipping")
            skipped += 1
            continue

        total = sum(sum(r["count"] for r in rows) for rows in new_records.values())
        log(f"  {total:,} new records — sending")

        ok = send_email(sub["email"], subject, html, text)

        if ok and not DEBUG:
            # Update last_sent_at
            upd = conn.cursor()
            upd.execute("UPDATE alert_subscribers SET last_sent_at = NOW() WHERE id = %s;", (sub["id"],))
            conn.commit()
            upd.close()
            sent += 1

    conn.close()

    print("\n" + "=" * 52)
    print(f"Done — sent: {sent}, skipped (no new data): {skipped}")
    print("=" * 52)


if __name__ == "__main__":
    run()
