from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles

from .database import get_connection, init_db
from .models import (
    WAITING_STATUSES,
    Application,
    ApplicationCreate,
    Stats,
    Status,
    StatusUpdate,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Job Tracker", lifespan=lifespan)


@app.post("/api/applications", response_model=Application, status_code=201)
def create_application(data: ApplicationCreate):
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO applications (company, role, status, date_applied) VALUES (?, ?, ?, ?)",
            (data.company, data.role, data.status, data.date_applied.isoformat()),
        )
        new_id = cursor.lastrowid
    return Application(id=new_id, **data.model_dump())


@app.get("/api/applications", response_model=list[Application])
def list_applications(status: Status | None = None):
    query = "SELECT * FROM applications"
    params: tuple = ()
    if status:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY date_applied DESC, id"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


@app.patch("/api/applications/{application_id}", response_model=Application)
def update_status(application_id: int, data: StatusUpdate):
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE applications SET status = ? WHERE id = ?",
            (data.status, application_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Application not found")
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
    return dict(row)


@app.delete("/api/applications/{application_id}", status_code=204)
def delete_application(application_id: int):
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM applications WHERE id = ?", (application_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Application not found")
    return Response(status_code=204)


@app.get("/api/stats", response_model=Stats)
def get_stats():
    placeholders = ", ".join("?" for _ in WAITING_STATUSES)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(status = 'Rejected'), 0) AS rejected,
                COALESCE(SUM(status IN ({placeholders})), 0) AS waiting
            FROM applications
            """,
            WAITING_STATUSES,
        ).fetchone()
    return dict(row)


# Serve the frontend once it exists (mounted last so /api routes take priority)
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
