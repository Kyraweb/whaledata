# whaledata.org — Deployment Guide

Self-hosting whaledata.org on a VPS using [Coolify](https://coolify.io/).

---

## Prerequisites

### Server
- **OS:** Debian 11+ or Ubuntu 22.04+
- **CPU:** 2 vCPU minimum (4 recommended)
- **RAM:** 2GB minimum (4GB recommended)
- **Disk:** 20GB minimum
- **Ports:** 80, 443 open

### Accounts needed
- [MapTiler](https://maptiler.com) — free tier, get an API key
- A domain name with Cloudflare DNS (recommended)

### Install Coolify
```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```
Access at `http://your-server-ip:8000` and complete setup.

---

## Architecture

```
whaledata/
├── api/    → FastAPI backend   → api.yourdomain.com
├── map/    → Vue 3 frontend    → yourdomain.com
└── jobs/   → Sync workers      → internal (no domain)
```

The **admin panel** lives inside the API service at `/admin/` — no separate service needed.

---

## Step 1 — Database (PostGIS)

1. Coolify → project → **New Resource → Database → PostgreSQL**
2. Select image: `postgis/postgis:17-3.5-alpine`
3. Set:
   - Database name: `whaledata`
   - Username: `whaledata_user`
   - Password: generate a strong one and save it
4. Click **Start**
5. Go to database service → **Terminal**:

```bash
psql -U whaledata_user -d whaledata
```

Paste the contents of `api/schema.sql`, then `api/schema_phase2.sql`. Verify with `\dt` — you should see 10 tables. Exit with `\q`.

**Note the internal hostname** from the database configuration (e.g. `ibxfh07zdq038tccbwy2g7l4`). You'll use this as `DB_HOST` everywhere.

---

## Step 2 — API Service

1. Coolify → **New Resource → Application → GitHub**
2. Select the `whaledata` repo
3. Configuration:
   - **Base Directory:** `/api`
   - **Build Pack:** `Dockerfile`
   - **Port:** `8000`
   - **Domain:** `https://api.yourdomain.com`
4. **Configuration → Custom Docker Options:** `--network=coolify`
5. **Environment Variables** (all Runtime):

| Variable | Value |
|----------|-------|
| `DB_HOST` | your PostGIS internal hostname |
| `DB_PORT` | `5432` |
| `DB_NAME` | `whaledata` |
| `DB_USER` | `whaledata_user` |
| `DB_PASSWORD` | your DB password |
| `ADMIN_USER` | your admin username |
| `ADMIN_PASSWORD` | your admin password |

6. **Deploy**. Verify:
```bash
curl https://api.yourdomain.com/health
# {"status":"ok","service":"whaledata-api","version":"2.0.0"}
```

Admin panel: `https://api.yourdomain.com/admin/`
API docs: `https://api.yourdomain.com/docs`

---

## Step 3 — Map Frontend

1. Coolify → **New Resource → Application → GitHub**
2. Select the `whaledata` repo
3. Configuration:
   - **Base Directory:** `/map`
   - **Build Pack:** `Dockerfile`
   - **Port:** `80`
   - **Domain:** `https://yourdomain.com`
4. **Environment Variables** (both **Buildtime AND Runtime**):

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://api.yourdomain.com` |
| `VITE_MAPTILER_KEY` | your MapTiler API key |

> ⚠️ `VITE_*` variables must have **Available at Buildtime** checked — Vite bakes them in at build time.

5. **Deploy**. Visit `https://yourdomain.com` — the globe loads with data.

---

## Step 4 — Jobs Service

1. Coolify → **New Resource → Application → GitHub**
2. Select the `whaledata` repo
3. Configuration:
   - **Base Directory:** `/jobs`
   - **Build Pack:** `Dockerfile`
   - **No domain needed**
4. **Custom Docker Options:** `--network=coolify`
5. Same DB environment variables as API service (no `ADMIN_*` needed)
6. **Deploy**

### Seed initial data

Go to jobs service → **Terminal**:

```bash
python -m app.sync_gbif
python -m app.sync_obis
python -m app.sync_strandings
python -m app.sync_acoustics
python -m app.sync_inaturalist
python -m app.sync_historical
```

Each takes 1–5 minutes. Total: ~25,000 records across all sources.

Alternatively trigger syncs from the admin panel at `api.yourdomain.com/admin/` → **Manual Sync**.

### Scheduled tasks

Go to jobs service → **Scheduled Tasks** → **Add** for each:

| Name | Command | Schedule | Timeout |
|------|---------|----------|---------|
| GBIF sync | `python -m app.sync_gbif` | `0 3 * * 0` | 3600 |
| OBIS sync | `python -m app.sync_obis` | `0 4 * * 0` | 3600 |
| Strandings | `python -m app.sync_strandings` | `0 3 1 * *` | 3600 |
| Acoustics | `python -m app.sync_acoustics` | `0 4 1 * *` | 3600 |
| iNaturalist | `python -m app.sync_inaturalist` | `0 3 * * 3` | 3600 |
| Historical | `python -m app.sync_historical` | `0 5 1 1 *` | 3600 |

---

## Step 5 — DNS & Cloudflare

### DNS records
| Type | Name | Value |
|------|------|-------|
| `A` | `@` | your server IP |
| `A` | `www` | your server IP |
| `A` | `api` | your server IP |

### Cloudflare settings
- SSL/TLS: **Full (strict)**
- Always Use HTTPS: **On**

### Admin URL redirect (optional)
Cloudflare → **Rules → Redirect Rules → Create**:
- When: Hostname equals `admin.yourdomain.com`
- Then: Redirect to `https://api.yourdomain.com/admin/`
- Type: 301

### Auto-deploy via webhook
1. Coolify → service → **Webhooks** → copy URL
2. GitHub → repo → **Settings → Webhooks → Add**
3. Paste URL, content type `application/json`, trigger: push event

---

## Troubleshooting

**Globe loads but no data**
- Check `VITE_API_URL` has Buildtime checked, redeploy map service
- Verify: `curl https://api.yourdomain.com/sightings/species-summary`

**Admin shows all zeros**
- Confirm `--network=coolify` in API service Custom Docker Options
- Check all `DB_*` env vars are set correctly in the API service

**DB connection refused**
- Confirm PostGIS service is running (green in Coolify)
- Use exact internal hostname from database service configuration

**GBIF sync fails with 400**
- Ensure you're on the latest `sync_gbif.py` (removed invalid `basisOfRecord` param)

**Manual sync fails with "No module named..."**
- The sync scripts in `api/app/admin/` use `from app.admin.sync_db import get_connection`
- The scripts in `jobs/app/` use `from app.database import get_connection`
- Do not mix them between services

**Map tiles not loading**
- Verify MapTiler key at [cloud.maptiler.com](https://cloud.maptiler.com)
- Check browser console for 401 errors

---

## Updating

Push to GitHub — Coolify auto-deploys if webhooks are configured, otherwise click **Redeploy**.

**After schema changes:** Connect to DB terminal and run the new SQL before deploying the API.

**After adding new sync scripts:** Copy them to both `jobs/app/` and `api/app/admin/` (with different import paths).
