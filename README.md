# Job Tracker

A small web app to keep track of your job applications.

- Add an application (company, role, status, date applied)
- See all applications in a table, newest first
- Filter the table by status
- Change an application's status, or delete it, directly from the table
- See quick stats at the top: total, waiting (Applied + Interviewing) and rejected

## Tech stack

- **Backend:** Python, [FastAPI](https://fastapi.tiangolo.com/), Uvicorn
- **Database:** SQLite (file `jobs.db`, created automatically on first run)
- **Frontend:** plain HTML, CSS and JavaScript (no build step), served by FastAPI
- **Tests:** pytest

## Run the app

Requires Python 3.10 or newer. The commands below are for Windows PowerShell.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Then open http://127.0.0.1:8000. Interactive API docs are at http://127.0.0.1:8000/docs.

On macOS or Linux, activate the virtual environment with `source .venv/bin/activate` instead.

## Run the tests

```powershell
pip install -r requirements-dev.txt
pytest
```

Each test uses its own temporary database, so your `jobs.db` is never touched.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/applications?status=...` | List applications (`status` is optional) |
| `POST` | `/api/applications` | Add an application |
| `PATCH` | `/api/applications/{id}` | Change an application's status |
| `DELETE` | `/api/applications/{id}` | Delete an application |
| `GET` | `/api/stats` | Total, rejected and waiting counts |

Allowed statuses: `Applied`, `Interviewing`, `Offer`, `Rejected`.

## Project structure

```
backend/     FastAPI app, database access and data models
frontend/    The web page (HTML, CSS, JS)
tests/       API tests
```
