# whaledata.org — Deployment Guide

This guide covers self-hosting whaledata.org on a VPS using [Coolify](https://coolify.io/).

---

## Prerequisites

### Server Requirements
- **OS:** Debian 11+ or Ubuntu 22.04+
- **CPU:** 2 vCPU minimum (4 recommended)
- **RAM:** 2GB minimum (4GB recommended)
- **Disk:** 20GB minimum
- **Ports:** 80, 443, 8000 open

### Required Accounts
- [MapTiler](https://maptiler.com) — free account, get an API key
- [GBIF](https://gbif.org) — free account (for data attribution only, API is open)
- A domain name with DNS access

### Install Coolify
Follow the official Coolify installation guide at [coolify.io/docs](https://coolify.io/docs).

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Access Coolify at `http://your-server-ip:8000` and complete the setup wizard.

---

## Architecture Overview

```
whaledata/
├── api/      → FastAPI backend        → api.whaledata.org
├── map/      → Vue 3 frontend         → whaledata.org
├── admin/    → (deprecated, use API)  → api.whaledata.org/admin/
└── jobs/     → Data sync workers      → internal only
```

The admin panel runs **inside the API service** at `/admin/`. There is no separate admin service needed.

---

## Step 1 — Database (PostGIS)

### Create the Database Service

1. In Coolify, go to your project → **New Resource** → **Database** → **PostgreSQL**
2. Search for `postgis/postgis` and select **PostGIS**
3. Configure:
   - **Image:** `postgis/postgis:17-3.5-alpine`
   - **Database name:** `whaledata`
   - **Username:** `whaledata_user`
   - **Password:** generate a strong password and save it
4. Click **Start**

### Apply the Schema

Once the database is running:

1. Go to the database service → **Terminal**
2. Run:

```bash
psql -U whaledata_user -d whaledata
```

3. Copy the contents of `api/schema.sql` and paste it into the terminal, or:

```bash
psql -U whaledata_user -d whaledata < /path/to/schema.sql
```

### Note the Internal Hostname

Go to the database service → **Configuration** → note the internal hostname (e.g. `ibxfh07zdq038tccbwy2g7l4`). You'll need this as `DB_HOST` for all other services.

---

## Step 2 — API Service

### Create the Application

1. Coolify → **New Resource** → **Application** → **GitHub** (or your Git provider)
2. Select the `whaledata` repository
3. Configure:
   - **Base Directory:** `/api`
   - **Build Pack:** `Dockerfile`
   - **Port:** `8000`
   - **Domain:** `https://api.yourdomain.com`

### Environment Variables

Go to **Environment Variables** and add all of these with **Available at Runtime** checked:

| Variable | Value |
|----------|-------|
| `DB_HOST` | your PostGIS internal hostname |
| `DB_PORT` | `5432` |
| `DB_NAME` | `whaledata` |
| `DB_USER` | `whaledata_user` |
| `DB_PASSWORD` | your DB password |
| `ADMIN_USER` | your chosen admin username |
| `ADMIN_PASSWORD` | your chosen admin password |

### Network Configuration

1. Go to **Configuration** → **Custom Docker Options**
2. Add `--network=coolify` to ensure the API can reach the database

### Deploy

Click **Deploy**. Once running, verify:

```bash
curl https://api.yourdomain.com/health
# {"status":"ok","service":"whaledata-api"}
```

### Admin Panel

The admin panel is available at `https://api.yourdomain.com/admin/`

Your browser will prompt for the `ADMIN_USER` and `ADMIN_PASSWORD` you set above.

To access it via a cleaner URL (e.g. `admin.yourdomain.com`), set up a Cloudflare Redirect Rule:
- **When:** Hostname equals `admin.yourdomain.com`
- **Redirect to:** `https://api.yourdomain.com/admin/`
- **Type:** 301

---

## Step 3 — Map Frontend

### Create the Application

1. Coolify → **New Resource** → **Application** → **GitHub**
2. Select the `whaledata` repository
3. Configure:
   - **Base Directory:** `/map`
   - **Build Pack:** `Dockerfile`
   - **Port:** `80`
   - **Domain:** `https://yourdomain.com`

### Environment Variables

Go to **Environment Variables** and add both with **Available at Buildtime AND Runtime** checked:

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://api.yourdomain.com` |
| `VITE_MAPTILER_KEY` | your MapTiler API key |

> ⚠️ **Important:** Vite bakes environment variables at build time. Both `VITE_*` variables must have **Available at Buildtime** checked, otherwise the map will fail to load.

### Deploy

Click **Deploy**. Visit `https://yourdomain.com` — the globe should load with whale data.

---

## Step 4 — Jobs Service (Data Sync)

### Create the Application

1. Coolify → **New Resource** → **Application** → **GitHub**
2. Select the `whaledata` repository
3. Configure:
   - **Base Directory:** `/jobs`
   - **Build Pack:** `Dockerfile`
   - **No domain needed**

### Environment Variables

Same DB variables as the API service:

| Variable | Value |
|----------|-------|
| `DB_HOST` | your PostGIS internal hostname |
| `DB_PORT` | `5432` |
| `DB_NAME` | `whaledata` |
| `DB_USER` | `whaledata_user` |
| `DB_PASSWORD` | your DB password |

### Network Configuration

Add `--network=coolify` to **Custom Docker Options** (same as API).

### Initial Data Load

Once deployed, go to the jobs service → **Terminal** and run:

```bash
python -m app.sync_gbif
python -m app.sync_obis
```

This will populate the database with ~7,500 whale sightings. Expect it to take 2–5 minutes.

### Scheduled Sync (Keep Data Fresh)

Set up daily automatic syncs:

1. Go to the **jobs** service → **Scheduled Tasks**
2. Add two tasks:

**GBIF Sync (daily at 3:00 AM):**
- Command: `python -m app.sync_gbif`
- Schedule: `0 3 * * *`
- Timeout: `3600`

**OBIS Sync (daily at 3:30 AM):**
- Command: `python -m app.sync_obis`
- Schedule: `30 3 * * *`
- Timeout: `3600`

> Note: You can also trigger syncs manually from the admin panel at `api.yourdomain.com/admin/` → **Manual Sync**.

---

## Step 5 — DNS & Cloudflare Setup

### DNS Records

In your DNS provider (or Cloudflare), add:

| Type | Name | Value |
|------|------|-------|
| `A` | `@` | your server IP |
| `A` | `www` | your server IP |
| `A` | `api` | your server IP |

### Cloudflare Settings (if using Cloudflare)

- Set SSL/TLS mode to **Full (strict)**
- Enable **Always Use HTTPS**
- Coolify handles SSL certificates via Let's Encrypt automatically

### Auto Deploy via Webhook

To auto-deploy when you push to GitHub:

1. Go to your map/API service → **Webhooks**
2. Copy the GitHub webhook URL
3. In GitHub → your repo → **Settings → Webhooks → Add webhook**
4. Paste the URL, set content type to `application/json`, select **Just the push event**

---

## Environment Variables Reference

### API Service (`/api`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_HOST` | ✅ | PostGIS internal hostname from Coolify |
| `DB_PORT` | ✅ | Database port (default: `5432`) |
| `DB_NAME` | ✅ | Database name (default: `whaledata`) |
| `DB_USER` | ✅ | Database username |
| `DB_PASSWORD` | ✅ | Database password |
| `ADMIN_USER` | ✅ | Admin panel username |
| `ADMIN_PASSWORD` | ✅ | Admin panel password |

### Map Service (`/map`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | ✅ | Full URL of your API (e.g. `https://api.yourdomain.com`) |
| `VITE_MAPTILER_KEY` | ✅ | MapTiler API key from [maptiler.com](https://maptiler.com) |

### Jobs Service (`/jobs`)

Same DB variables as API service. No additional variables needed.

---

## Troubleshooting

### Map shows blank / no data
- Check `VITE_API_URL` is set with **Available at Buildtime** checked
- Verify the API health check: `curl https://api.yourdomain.com/health`
- Check CORS — the API's `main.py` must include your map domain in `allow_origins`

### Admin panel shows 0s / no data
- Ensure `--network=coolify` is in the API service's Custom Docker Options
- Verify all `DB_*` env vars are set correctly in the API service
- Check the API logs in Coolify for database connection errors

### Database connection refused
- Confirm the PostGIS service is running (green status in Coolify)
- Use the exact internal hostname from the database service configuration
- Both services must be on the same Coolify network

### GBIF sync returns 400 error
- This was caused by an invalid `basisOfRecord` parameter — ensure you're using the latest `sync_gbif.py`
- Check GBIF API status at [gbif.org](https://gbif.org)

### Map tiles not loading
- Verify your MapTiler API key is valid at [cloud.maptiler.com](https://cloud.maptiler.com)
- Ensure the key has no domain restrictions that would block your domain
- Check browser console for 401 errors from MapTiler

### Auto-deploy not triggering
- Verify the GitHub webhook is configured with the correct Coolify URL
- Check Coolify **Webhooks** page for delivery history
- Ensure **Auto Deploy** is checked in the service's **Advanced** settings

---

## Updating whaledata.org

### Code Updates
Push to your GitHub repository. If webhooks are configured, Coolify will auto-deploy. Otherwise, click **Redeploy** in the Coolify service.

### Database Password Change
1. Update the password in the Coolify database service
2. Update `DB_PASSWORD` in all services (API, jobs) that connect to it
3. Redeploy API and jobs services

### Adding New Species Data
Use the admin panel → **Manual Sync** to trigger a fresh data pull, or run manually in the jobs terminal:
```bash
python -m app.sync_gbif
python -m app.sync_obis
```

---

## Data Sources & Attribution

whaledata.org uses openly licensed data:

- **GBIF** — [gbif.org](https://gbif.org) — CC BY 4.0
- **OBIS** — [obis.org](https://obis.org) — CC BY 4.0
- **MapTiler** — map tiles — [maptiler.com](https://maptiler.com)

If you host a public instance of whaledata.org, please maintain attribution to these data sources.
