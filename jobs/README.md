# whaledata — Jobs

Data sync workers. Pulls whale sighting and population data from open APIs and writes it to the database.

## Stack

- Python 3.11+
- Requests
- psycopg2

## Data Sources

- GBIF (Global Biodiversity Information Facility)
- OBIS — coming soon
- iNaturalist — coming soon

## Folder structure

```
jobs/
├── app/
│   ├── database.py     # DB connection handler
│   └── sync_gbif.py    # GBIF sync job
├── .env.example
├── Dockerfile
└── requirements.txt
```

## Local setup

```bash
cd jobs

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run the GBIF sync job
python -m app.sync_gbif
```

## What the GBIF sync does

- Fetches up to 1000 sightings per species from GBIF
- Targets 6 key species: humpback, blue whale, orca, grey whale, sperm whale, fin whale
- Skips duplicate records automatically
- Logs every run to the sync_log table
