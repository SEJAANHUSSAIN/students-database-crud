# Students Database CRUD Application

A complete individual backend project using **Python, FastAPI, SQLite, and an HTML/CSS/JavaScript frontend**. The application supports creating, listing, searching, viewing, updating, and deleting student records. No AI extension is included.

## Features

- Add a student with name, date of birth, and unique email.
- Store optional phone, course, address, and enrollment date.
- List and search students by name, email, or course.
- Filter by course.
- View an individual student through the API.
- Edit and delete records in the web interface.
- Persistent SQLite database (`students.db`).
- Interactive API documentation at `/docs`.
- Validation for dates, email addresses, required fields, and duplicate email addresses.

## Requirements

- Python 3.10 or newer (Python 3.11+ recommended)
- pip
- A modern browser

## 1. Open the project folder

Extract `students-crud.zip`, then open a terminal in the extracted `students-crud` folder (the folder containing `main.py`).

## 2. Create and activate a virtual environment

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Run the application

```bash
uvicorn main:app --reload
```

Open these addresses:

- Web frontend: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

The database is created automatically when the app starts. Keep the terminal running while using the application. Press `Ctrl+C` to stop it.

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/students` | Create a student |
| `GET` | `/students` | List/search students |
| `GET` | `/students/{student_id}` | Get one student |
| `PUT` | `/students/{student_id}` | Update supplied fields |
| `DELETE` | `/students/{student_id}` | Delete a student |
| `GET` | `/health` | Check API status |

### Create a student

```bash
curl -X POST http://127.0.0.1:8000/students \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Aisha Khan\",\"date_of_birth\":\"2005-04-12\",\"email\":\"aisha@example.com\",\"phone\":\"9876543210\",\"course\":\"B.Tech CSE\",\"address\":\"Lucknow, India\"}"
```

Example response (IDs and timestamps will vary):

```json
{
  "id": 1,
  "name": "Aisha Khan",
  "date_of_birth": "2005-04-12",
  "email": "aisha@example.com",
  "phone": "9876543210",
  "course": "B.Tech CSE",
  "address": "Lucknow, India",
  "enrollment_date": "2026-10-25",
  "created_at": "2026-10-25 10:00:00",
  "updated_at": "2026-10-25 10:00:00"
}
```

### List all students

```bash
curl http://127.0.0.1:8000/students
```

### Search by name, email, or course

```bash
curl "http://127.0.0.1:8000/students?search=Aisha"
```

### Filter by course

```bash
curl "http://127.0.0.1:8000/students?course=B.Tech"
```

### Get one student

```bash
curl http://127.0.0.1:8000/students/1
```

### Update a student

Only send the fields you want to change. Although the route uses `PUT`, this implementation accepts partial updates for convenience.

```bash
curl -X PUT http://127.0.0.1:8000/students/1 \
  -H "Content-Type: application/json" \
  -d "{\"course\":\"B.Tech Computer Science\"}"
```

### Delete a student

```bash
curl -X DELETE http://127.0.0.1:8000/students/1
```

## Expected error responses

- `404 Not Found`: student ID does not exist.
- `409 Conflict`: email is already used by another student.
- `422 Unprocessable Entity`: invalid input, invalid date, or invalid email.
- `400 Bad Request`: update body contains no fields.

## Project structure

```text
students-crud/
├── main.py
├── requirements.txt
├── README.md
├── students.db          # created automatically when the server starts
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```

## How it works

1. The browser sends HTTP requests using JavaScript `fetch()`.
2. FastAPI receives the request and validates its JSON with Pydantic models.
3. Python uses SQLite parameterized queries to read or change records.
4. The API returns JSON; JavaScript updates the table without reloading the page.
5. SQLite saves the data in `students.db`, so records remain after restarting the server.

## Notes

- This is a learning/demo project. Before production use, add authentication, authorization, backups, logging, and deployment security.
- Do not store real students' personal information in a public deployment without appropriate permission and security controls.
- Do not delete `students.db` unless you intend to erase the saved records.
