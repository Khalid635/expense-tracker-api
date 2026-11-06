# Expense Tracker API

A REST API for tracking personal income and expenses, with JWT authentication. Built with FastAPI and SQLAlchemy.

## Features

- User registration and login with JWT (HS256, 30-minute tokens, bcrypt-hashed passwords)
- Full transaction CRUD — create, list, view, update and delete transactions
- Filter transactions by type, category, amount and date range
- Per-user data isolation — users only ever see their own transactions
- Health-check endpoint
- Automated test suite (`test_main.py`, ~430 lines)

## Tech stack

FastAPI, SQLAlchemy, Pydantic v2, pydantic-settings, passlib (bcrypt), PyJWT, SQLite (local) / PostgreSQL (via `DATABASE_URL`), pytest

## API overview

| Method | Path | Auth |
|---|---|---|
| POST | `/auth/register` | Public |
| POST | `/auth/login` | Public |
| POST | `/transactions` | JWT |
| GET | `/transactions` | JWT |
| GET | `/transactions/filter` | JWT |
| GET | `/transactions/{transaction_id}` | JWT |
| PUT | `/transactions/{transaction_id}` | JWT |
| DELETE | `/transactions/{transaction_id}` | JWT |
| GET | `/health` | Public |

Filter query parameters for `GET /transactions/filter`: `type` (`income` or `expense`), `category`, `minimum_amount`, `maximum_amount`, `start_date`, `end_date`, `limit` (default 100, max 1000), `offset`.

Interactive docs: http://127.0.0.1:8000/docs

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate        # on Windows Git Bash: source .venv/Scripts/activate
pip install fastapi "uvicorn[standard]" sqlalchemy pydantic pydantic-settings "passlib[bcrypt]" pyjwt python-multipart pytest httpx
cp .env.example .env             # then edit .env and set a real SECRET_KEY
uvicorn main:app --reload
```

## Environment variables (`.env`)

| Name | Purpose |
|---|---|
| `DATABASE_URL` | Database connection string (SQLite file by default) |
| `SECRET_KEY` | Secret used to sign JWTs — use a long random value, never commit the real one |
| `ALGORITHM` | JWT algorithm (`HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (`30`) |

## Tests

```bash
pytest
```

## Author

**Khalid Bin Masud**

[GitHub](https://github.com/Khalid635) · [LinkedIn](https://www.linkedin.com/in/khalid-bin-masud-817a913b9)
