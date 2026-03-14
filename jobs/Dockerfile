FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Run sync once on startup, then sleep 24h in a loop
CMD ["sh", "-c", "while true; do python -m app.sync_gbif; echo 'Sync done, sleeping 24h'; sleep 86400; done"]
