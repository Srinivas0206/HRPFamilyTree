# HRP Family Tree

HRP Family Tree is a Flask web application for searching the provided family tree CSV datasets and viewing relationship details for a selected person.

## Features

- Search the Persons dataset using partial names, places, gotra, notes, or identifiers.
- Display matching people in a simple, clickable results list.
- Show detailed information for a selected person:
  - Full name and alternate-language name
  - Place, generation, gotra, and notes
  - Parents
  - Spouse or spouses discovered through relationship records
  - Children
  - Additional relationship notes from the relationship dataset
- Toggle display names and places between English and Kannada.
- Modular Python structure for future maintenance:
  - `app.py` creates the Flask application and routes.
  - `family_tree/models.py` defines data models.
  - `family_tree/repository.py` loads and indexes CSV data.
  - `family_tree/services.py` assembles view-friendly family details.
  - `templates/` contains the HTML pages.
  - `static/` contains styling.

## Data Files

The app expects these CSV files in the repository root:

- `personsData.csv`
- `relation.csv`

`relation.csv` is interpreted as parent/spouse-to-child rows where `pid` and `mid` identify the parent pair and `cid` identifies the child.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the Application

```bash
flask --app app run
```

Then open <http://127.0.0.1:5000> and search for a person, such as `Kiran`, `Bhatta`, or `Bengaluru`.

## Run Tests

```bash
python -m pytest
```

## Deployment

The included `render.yaml` can be used as a starting point for Render deployment. The app also exposes the module-level `app` object for WSGI servers such as Gunicorn:

```bash
gunicorn app:app
```
