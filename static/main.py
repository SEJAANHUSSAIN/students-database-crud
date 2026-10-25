from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "students.db"
STATIC_DIR = BASE_DIR / "static"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                course TEXT,
                address TEXT,
                enrollment_date TEXT NOT NULL DEFAULT (DATE('now')),
                created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
                updated_at TEXT NOT NULL DEFAULT (DATETIME('now'))
            )
        """)
        connection.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Students Database CRUD API",
    description="A student-record management API built with FastAPI and SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class StudentBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    date_of_birth: date
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=250)
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value

    @field_validator("phone", "course", "address", mode="before")
    @classmethod
    def trim_optional_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=250)
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def trim_update_name(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value

    @field_validator("phone", "course", "address", mode="before")
    @classmethod
    def trim_update_optional_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date_of_birth: date
    email: EmailStr
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: date
    created_at: str
    updated_at: str


def row_to_student(row: sqlite3.Row) -> dict:
    return dict(row)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Students API is running"}


@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate):
    data = student.model_dump()
    data["date_of_birth"] = data["date_of_birth"].isoformat()
    if data["enrollment_date"] is None:
        data["enrollment_date"] = date.today().isoformat()
    else:
        data["enrollment_date"] = data["enrollment_date"].isoformat()

    fields = ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]
    values = [data[field] for field in fields]
    placeholders = ", ".join("?" for _ in fields)

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                f"INSERT INTO students ({', '.join(fields)}) VALUES ({placeholders})",
                values,
            )
            connection.commit()
            row = connection.execute("SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return row_to_student(row)
    except sqlite3.IntegrityError as exc:
        if "students.email" in str(exc) or "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="A student with this email already exists.") from exc
        raise HTTPException(status_code=400, detail="Could not create student.") from exc


@app.get("/students", response_model=list[StudentOut])
def list_students(
    search: Optional[str] = Query(default=None, description="Search name, email, or course"),
    course: Optional[str] = Query(default=None, description="Filter by course"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    sql = "SELECT * FROM students WHERE 1=1"
    params = []
    if search:
        term = f"%{search.strip()}%"
        sql += " AND (name LIKE ? OR email LIKE ? OR course LIKE ?)"
        params.extend([term, term, term])
    if course:
        sql += " AND course LIKE ?"
        params.append(f"%{course.strip()}%")
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_connection() as connection:
        rows = connection.execute(sql, params).fetchall()
        return [row_to_student(row) for row in rows]


@app.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: int):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    return row_to_student(row)


@app.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, student: StudentUpdate):
    changes = student.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one field to update.")
    for key, value in changes.items():
        if hasattr(value, "isoformat"):
            changes[key] = value.isoformat()
    if "name" in changes and changes["name"] is None:
        raise HTTPException(status_code=422, detail="Name cannot be null.")
    if "date_of_birth" in changes and changes["date_of_birth"] is None:
        raise HTTPException(status_code=422, detail="Date of birth cannot be null.")
    if "email" in changes and changes["email"] is None:
        raise HTTPException(status_code=422, detail="Email cannot be null.")

    assignments = ", ".join(f"{key} = ?" for key in changes)
    values = list(changes.values())
    values.append(student_id)
    try:
        with get_connection() as connection:
            existing = connection.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone()
            if existing is None:
                raise HTTPException(status_code=404, detail="Student not found.")
            connection.execute(
                f"UPDATE students SET {assignments}, updated_at = DATETIME('now') WHERE id = ?",
                values,
            )
            connection.commit()
            row = connection.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
            return row_to_student(row)
    except sqlite3.IntegrityError as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="A student with this email already exists.") from exc
        raise HTTPException(status_code=400, detail="Could not update student.") from exc


@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
        connection.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student not found.")
    return {"message": f"Student {student_id} deleted successfully."}
