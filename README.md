# Meteo WebApp

This project is a Python/Flask web application that shows an interactive global map of meteorological stations backed by a local PostgreSQL database. Data is currently sourced from ECA&D (European Climate Assessment & Dataset). For each station, the app can render static Bokeh graphs of maximum, minimum and mean temperatures to visualize their evolution over time.

The front-end uses OpenLayers to display an OpenStreetMap base layer and clickable station markers. A toolbar allows you to filter stations by provider and country, and to switch the user interface language between English and Spanish.

## Features

- Flask-based web application with an app factory (`flaskr/app.py`).
- PostgreSQL database for stations, providers, magnitudes, measurements and ECAD sources.
- ECAD provider integration (download, parse, and persist source files).
- Per-station temperature graphs generated as static HTML using Bokeh.
- OpenLayers map with station markers and popups.
- Toolbar with:
  - Provider filter.
  - Country filter (names localized via `country-list`).
  - Language selector (English/Spanish) for UI labels.

## Project structure (high level)

- `flaskr/app.py` – Flask app factory, logging configuration, route registration and data-processing bootstrap.
- `flaskr/config/config.py` – Central configuration (paths, DB credentials, log file location).
- `flaskr/db/` – Database connection (`db.py`), SQL helper methods (`statements.py`), schema (`schema.sql`).
- `flaskr/data/` – Data orchestration, including ECAD provider implementation under `flaskr/data/ecad/`.
- `flaskr/graphs/` – Bokeh utilities and ECAD-specific graph generation.
- `flaskr/osmap/os_map.py` – Blueprint that renders the OpenLayers-based map and toolbar.
- `flaskr/templates/index.html` – Main HTML template for the map UI.
- `flaskr/static/` – OpenLayers library, CSS and JS assets.

## Requirements

This project does not ship a `requirements.txt`, but you can infer the main dependencies from the imports:

- Python 3.x
- Flask
- psycopg2 or psycopg2-binary
- pandas
- bokeh
- tqdm
- country-list

Example setup with a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install Flask psycopg2-binary pandas bokeh tqdm country-list
```

## Database setup

The schema targets PostgreSQL. Defaults are:

- Database name: `meteo`
- Host: `localhost`
- User: `meteo`
- Password: `meteo`

1. **Create database and user** (run as a PostgreSQL superuser):

```bash
sudo -u postgres psql -c "CREATE USER meteo WITH ENCRYPTED PASSWORD 'meteo';"
sudo -u postgres psql -c "CREATE DATABASE meteo OWNER meteo;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE meteo TO meteo;"
```

2. **Initialize schema and seed metadata** using the Flask CLI command defined in `flaskr/db/db.py`:

```bash
export PYTHONPATH=$(pwd)/flaskr
flask --app flaskr/app init-db
```

> Warning: `init-db` drops and recreates all tables defined in `flaskr/db/schema.sql`. Do not run it against a database with data you want to keep.

## Running the development server

Use the Flask CLI (recommended for debug and auto-reload):

```bash
export PYTHONPATH=$(pwd)/flaskr
flask --app flaskr/app run --debug
```

Alternatively, run the module directly:

```bash
python3 -m flaskr.app
```

On startup (outside of the `init-db` command), the app will:

- Initialize provider definitions from the database.
- Download and process ECAD data if needed.
- Populate the database with stations and source metadata.
- Generate per-station Bokeh HTML graphs under `flaskr/graphs/current/<provider>/`.

This data pipeline can take a while on the first run.

## Using the web UI

1. Open your browser at `http://127.0.0.1:5000/`.
2. Use the toolbar at the top to:
   - Select a **language** (English/Spanish) for the UI labels.
   - Select a **provider** (e.g. `ecad`).
   - Select a **country** (only countries with stations from the database are listed).
3. Click **Show Map** to display the stations that match the filters.
4. Hover over a marker to see a short tooltip for the station.
5. Click a marker to open a popup with more detailed information and a link to the station-temperature graph.

## Useful checks and endpoints

- List map markers:

```bash
curl http://127.0.0.1:5000/stationsmarkers
```

- Fetch a station popup (replace `1` with a valid station ID from the `stations` table):

```bash
curl http://127.0.0.1:5000/popup/1
```

## Type checking and linting

If you have `mypy` and `pyright` installed, you can run:

```bash
mypy .
pyright
```

## Notes

- Logs are written to `flaskr/logs/app.log`.
- The `init-db` command uses `flaskr/db/schema.sql` as the source of truth for the database schema.
- The `tests/` directory is present but does not yet contain test files; automated testing is a good next step for further development.
