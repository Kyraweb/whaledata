FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command runs the GBIF sync job
CMD ["python", "-m", "app.sync_gbif"]
