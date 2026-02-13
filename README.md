# Dorm Maintenance Ticket API

REST API for dorm maintenance tickets built with FastAPI, SQLAlchemy, and SQLite.

## Tech Stack
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy ORM (SQLite file: `dorm.db`)
- Pydantic validation
- Pytest

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Server
```bash
uvicorn app.main:app --reload
```

- API base: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Run Tests
```bash
pytest -q
```

## Example CRUD Commands

### 1) Create Category
```bash
curl -X POST http://127.0.0.1:8000/categories \
  -H "Content-Type: application/json" \
  -d '{"name":"Electrical","description":"Power-related issues"}'
```

Response:
```json
{
  "id": 1,
  "name": "Electrical",
  "description": "Power-related issues",
  "is_active": true,
  "created_at": "2026-02-13T12:00:00.000000"
}
```

### 2) List Categories
```bash
curl http://127.0.0.1:8000/categories
```

### 3) Update Category
```bash
curl -X PUT http://127.0.0.1:8000/categories/1 \
  -H "Content-Type: application/json" \
  -d '{"description":"Electrical and appliance issues"}'
```

### 4) Delete Category (soft delete: `is_active=false`)
```bash
curl -X DELETE http://127.0.0.1:8000/categories/1
```

### 5) Create Ticket
```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Air conditioner broken",
    "description":"The air conditioner has stopped cooling for two days.",
    "room":"A-1207",
    "priority":"high",
    "category_id":1
  }'
```

Response:
```json
{
  "id": 1,
  "title": "Air conditioner broken",
  "description": "The air conditioner has stopped cooling for two days.",
  "room": "A-1207",
  "priority": "high",
  "category_id": 1,
  "status": "open",
  "created_at": "2026-02-13T12:01:00.000000",
  "updated_at": "2026-02-13T12:01:00.000000",
  "comments": []
}
```

### 6) List Tickets (filter/sort/pagination)
```bash
curl "http://127.0.0.1:8000/tickets?status=open&priority=high&sort_by=created_at&sort_order=desc&skip=0&limit=10"
```

### 7) Get Ticket by ID
```bash
curl http://127.0.0.1:8000/tickets/1
```

### 8) Update Ticket (student only if status=open)
```bash
curl -X PUT http://127.0.0.1:8000/tickets/1 \
  -H "X-Role: student" \
  -H "Content-Type: application/json" \
  -d '{"description":"Please check after 6 PM."}'
```

### 9) Add Comment
```bash
curl -X POST http://127.0.0.1:8000/tickets/1/comments \
  -H "X-Role: student" \
  -H "Content-Type: application/json" \
  -d '{"message":"The issue is getting worse."}'
```

### 10) Update Ticket Status (technician only)
```bash
curl -X PUT http://127.0.0.1:8000/tickets/1/status \
  -H "X-Role: technician" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'
```

### 11) Delete Ticket
```bash
curl -X DELETE http://127.0.0.1:8000/tickets/1
```

## Status Transition Rules
Allowed transitions:
- `open -> in_progress`
- `in_progress -> done`
- `open -> rejected`
- `in_progress -> rejected`

Others return:
```json
{
  "code": "INVALID_STATUS_TRANSITION",
  "message": "Cannot transition from in_progress to open",
  "details": []
}
```

## Error Response Format
All errors are returned in consistent JSON:
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [
    {"field": "title", "message": "String should have at least 5 characters"}
  ]
}
```

Possible codes:
- `VALIDATION_ERROR` (HTTP 400)
- `NOT_FOUND` (HTTP 404)
- `FORBIDDEN` (HTTP 403)
- `INVALID_STATUS_TRANSITION` (HTTP 409)
