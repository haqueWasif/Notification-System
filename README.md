# Background Job Based Notification System

A Django REST Framework backend API where authenticated users can schedule notifications.  
The system uses PostgreSQL for persistent storage, Redis as the Celery broker, and Celery workers for background notification processing.

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Docker
- Docker Compose
- Redis
- Celery
- JWT Authentication

## Features

- User registration
- JWT login and refresh token
- Create scheduled notification
- Reject notification if scheduled time is in the past
- View user-specific notifications
- View notification history
- Background notification processing with Celery
- Retry failed notification
- Prevent infinite retries
- Mark notification as permanently failed after 3 failures
- User-based API security

## Project Structure

```txt
notification-system/
├── app/
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── __init__.py
│   ├── accounts/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   └── notifications/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── tasks.py
│       ├── admin.py
│       └── urls.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
````

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd notification-system
```

### 2. Create environment file

```bash
cp .env.example .env
```

For Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 3. Build and start services

```bash
docker compose up --build
```

This starts:

* Django web server
* PostgreSQL database
* Redis server
* Celery worker

### 4. Run migrations

In another terminal:

```bash
docker compose run --rm web python manage.py migrate
```

### 5. Create superuser

```bash
docker compose run --rm web python manage.py createsuperuser
```

### 6. Access admin panel

```txt
http://localhost:8000/admin/
```

## API Endpoints

### Register User

```http
POST /api/auth/register/
```

Request body:

```json
{
  "username": "wasiful",
  "email": "wasiful@example.com",
  "password": "strongpass123"
}
```

### Login

```http
POST /api/auth/token/
```

Request body:

```json
{
  "username": "wasiful",
  "password": "strongpass123"
}
```

Response:

```json
{
  "refresh": "refresh_token_here",
  "access": "access_token_here"
}
```

Use the access token for protected routes:

```http
Authorization: Bearer your_access_token_here
```

### Refresh Token

```http
POST /api/auth/token/refresh/
```

Request body:

```json
{
  "refresh": "refresh_token_here"
}
```

### Create Notification

```http
POST /api/notifications/
```

Headers:

```http
Authorization: Bearer your_access_token_here
Content-Type: application/json
```

Request body:

```json
{
  "title": "Interview Reminder",
  "message": "Prepare DSA, DB, OOP and interpersonal answers.",
  "scheduled_time": "2026-05-24T20:00:00+06:00"
}
```

### List Notifications

```http
GET /api/notifications/
```

### View Notification History

```http
GET /api/notifications/history/
```

### Retry Failed Notification

```http
POST /api/notifications/{id}/retry/
```

Example:

```http
POST /api/notifications/1/retry/
```

## Notification Statuses

| Status               | Meaning                                           |
| -------------------- | ------------------------------------------------- |
| `PENDING`            | Notification is scheduled or queued               |
| `SENT`               | Notification was successfully processed           |
| `FAILED`             | Notification failed but can still be retried      |
| `PERMANENTLY_FAILED` | Notification failed 3 times and cannot be retried |

## Time Validation

If the scheduled time is in the past, the API rejects the request.

Example invalid request:

```json
{
  "title": "Old Notification",
  "message": "This should fail.",
  "scheduled_time": "2024-01-01T10:00:00+06:00"
}
```

Example response:

```json
{
  "scheduled_time": [
    "Scheduled time must be in the future."
  ]
}
```

## Background Job Flow

```txt
User creates notification
        ↓
Django validates request
        ↓
Notification is saved in PostgreSQL
        ↓
Celery task is scheduled using ETA
        ↓
Redis stores the queued job
        ↓
Celery worker processes the job
        ↓
Notification status becomes SENT or FAILED
```

## Retry Logic

If notification processing fails:

```txt
retry_count increases by 1
```

If:

```txt
retry_count < 3
```

the notification becomes:

```txt
FAILED
```

and can be manually retried.

If:

```txt
retry_count >= 3
```

the notification becomes:

```txt
PERMANENTLY_FAILED
```

and retry is blocked.

## Failure Simulation for Testing

For testing retry logic, the project can simulate failure when the notification title contains the word:

```txt
fail
```

Example:

```json
{
  "title": "Fail Test",
  "message": "This should fail intentionally.",
  "scheduled_time": "2026-05-24T20:00:00+06:00"
}
```

After Celery processes it, the notification should become `FAILED`.

After 3 failed attempts, it becomes `PERMANENTLY_FAILED`.

## Security Considerations

* JWT authentication is required for notification APIs.
* Users can only view their own notifications.
* Users cannot retry another user's notification.
* Scheduled time must be in the future.
* Retry count is limited to prevent infinite retries.
* System-generated fields like `status`, `retry_count`, and `last_error` are read-only from the API.

## Scalability Notes

This project separates API requests from background processing.

The Django API handles validation and persistence, while Celery handles scheduled and retryable jobs asynchronously. This avoids blocking API requests and allows workers to be scaled independently.

For larger production systems, a periodic scheduler can scan due notifications from the database instead of scheduling many long-future ETA tasks directly.
