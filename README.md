# Library Service API

A Django REST Framework backend for managing a book borrowing service: book inventory, user accounts, borrowings, fines, Stripe payments, and Telegram notifications.

## Features

**Books**
- Full CRUD for books (title, author, cover type, inventory, daily fee)
- Read access for everyone, write access restricted to admins

**Users**
- Custom user model with email as the login field
- JWT authentication (registration, token obtain/refresh, profile management)
- Custom auth header (`Authorize` instead of `Authorization`) for convenient testing with the ModHeader extension

**Borrowings**
- Create a borrowing with automatic inventory validation and decrement
- Filter by active status (`is_active`) and, for admins, by user (`user_id`)
- Non-admin users only see their own borrowings
- Return endpoint that restores inventory and blocks double returns
- Automatic fine calculation and charge for overdue returns
- New borrowings are blocked while the user has an unpaid pending payment
- Daily scheduled check for overdue borrowings with Telegram alerts

**Payments**
- Stripe Checkout Sessions created automatically on borrowing creation
- Success/cancel callback endpoints that confirm payment status with Stripe
- Automatic fine payments on overdue returns
- Expired session detection (scheduled check) with a renew endpoint
- Telegram notification on every successful payment

**Notifications**
- Telegram bot messages for new borrowings, daily overdue summaries, and successful payments

**Infrastructure**
- Dockerized: Django, PostgreSQL, Redis, Celery worker, Celery beat
- Scheduled background tasks via Celery Beat
- CI pipeline (GitHub Actions): flake8, black, unit tests

## Tech stack

- Python 3.12, Django 6, Django REST Framework
- PostgreSQL, Redis
- Celery + Celery Beat
- Simple JWT
- Stripe API
- Telegram Bot API
- Docker / Docker Compose
- GitHub Actions

## Project structure

```
library_service_project/   # settings, root urls, celery app
books/                      # Book model, CRUD, permissions
user/                       # custom User model, JWT auth
  management/commands/wait_for_db.py
borrowings/                 # Borrowing model, business logic, telegram helper
payments/                   # Payment model, Stripe integration
```

## Getting started

### Prerequisites

- Docker and Docker Compose
- A Telegram bot token and a chat/group id
- A Stripe test account and secret key

### Environment variables

Copy `.env.sample` to `.env` and fill in the values:

```
SECRET_KEY=
DEBUG=True

POSTGRES_DB=library
POSTGRES_USER=library
POSTGRES_PASSWORD=
POSTGRES_HOST=library_db
POSTGRES_PORT=5432
PGDATA=/var/lib/postgresql/data

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

STRIPE_SECRET_KEY=

CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
```

### Run with Docker Compose

```bash
docker-compose up --build
```

This starts five services:

| Service       | Purpose                          |
|---------------|-----------------------------------|
| `library`     | Django app (runs migrations first) |
| `library_db`  | PostgreSQL                        |
| `redis`       | Celery broker/result backend      |
| `celery`      | Celery worker                     |
| `celery-beat` | Celery scheduler                  |

The API is available at `http://localhost:8000/`.

Create an admin account:

```bash
docker-compose exec library python manage.py createsuperuser
```

### Run locally (without Docker)

Useful for fast iteration (e.g. running tests directly from an IDE). Requires PostgreSQL and Redis installed and running locally.

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start PostgreSQL and Redis (e.g. via Homebrew on macOS):

   ```bash
   brew services start postgresql@16
   brew services start redis
   ```

3. Create the database and user matching your `.env` values:

   ```bash
   psql postgres
   CREATE DATABASE library;
   CREATE USER library WITH PASSWORD 'library';
   GRANT ALL PRIVILEGES ON DATABASE library TO library;
   ```

4. In `.env`, point at `localhost` instead of the Docker service names:

   ```
   POSTGRES_HOST=localhost
   CELERY_BROKER_URL=redis://localhost:6379
   CELERY_RESULT_BACKEND=redis://localhost:6379
   ```

   > This is the one setting that differs between Docker and local runs — `library_db`/`redis` are hostnames that only resolve inside the Docker network.

5. Run migrations and the dev server:

   ```bash
   python manage.py wait_for_db
   python manage.py migrate
   python manage.py runserver
   ```

6. In separate terminals, run the Celery worker and beat scheduler:

   ```bash
   celery -A library_service_project worker -l info
   celery -A library_service_project beat -l info
   ```

## Authentication

Register at `POST /users/`, then obtain a token at `POST /users/token/`.

Send the access token on subsequent requests using the **`Authorize`** header (not the standard `Authorization`):

```
Authorize: Bearer <access_token>
```

## API overview

| Endpoint                          | Methods              | Notes                                  |
|------------------------------------|-----------------------|------------------------------------------|
| `/books/`                          | GET, POST             | Write access: admin only               |
| `/books/<id>/`                     | GET, PUT, PATCH, DELETE | Write access: admin only              |
| `/users/`                          | POST                  | Registration                           |
| `/users/token/`                    | POST                  | Obtain JWT pair                        |
| `/users/token/refresh/`            | POST                  | Refresh access token                   |
| `/users/me/`                       | GET, PUT, PATCH        | Current user profile                   |
| `/borrowings/`                     | GET, POST              | `?is_active=`, `?user_id=` (admin)     |
| `/borrowings/<id>/`                | GET                    | Includes nested book and payments      |
| `/borrowings/<id>/return/`         | POST                   | Restores inventory, charges fine if overdue |
| `/payments/`                       | GET                    | Non-admins see only their own payments |
| `/payments/<id>/`                  | GET                    |                                          |
| `/payments/success/`               | GET                    | Stripe success callback (`?session_id=`) |
| `/payments/cancel/`                | GET                    | Stripe cancel callback                 |
| `/payments/<id>/renew/`            | POST                   | Renews an expired payment session      |

## Background tasks

Scheduled via Celery Beat:

| Task                                     | Schedule       | Purpose                                            |
|-------------------------------------------|----------------|------------------------------------------------------|
| `borrowings.tasks.overdue_borrowings`      | Daily at 09:00 | Notifies Telegram about overdue borrowings          |
| `payments.tasks.expiring_sessions`         | Every minute   | Marks expired Stripe sessions as `EXPIRED`          |

## Testing

```bash
docker-compose exec library python manage.py test
```

Each app (`books`, `user`, `borrowings`, `payments`) has its own test suite covering models, permissions, and key business logic (inventory handling, filtering, borrowing constraints).

## CI

GitHub Actions runs on every push and pull request to `main`/`master`/`dev`:

1. `flake8` — linting
2. `black --check` — formatting
3. `python manage.py test` — unit tests, against a PostgreSQL service container