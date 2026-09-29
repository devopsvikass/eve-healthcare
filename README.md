# EVE Healthcare — Diagnostic Test Booking & Payment API

A backend service for diagnostic test bookings and simulated payments, built as part of the **EVE Healthcare SDE Intern Backend Engineering Assignment**.

The application provides APIs for:

* User signup and JWT authentication
* Diagnostic centres and diagnostic tests
* Test availability and centre-specific pricing
* Diagnostic test bookings
* Simulated payments
* Payment webhooks with idempotency
* Booking cancellation
* Input validation and authorization
* Automated API tests
* OpenAPI/Swagger API documentation

---

## Tech Stack

* **Python 3.12**
* **Django 6.1**
* **Django REST Framework**
* **PostgreSQL 16**
* **JWT Authentication** — `djangorestframework-simplejwt`
* **OpenAPI / Swagger** — `drf-spectacular`
* **psycopg2** — PostgreSQL database driver
* **python-dotenv** — environment variable management
* **Django Test Framework** — automated testing

---

## Project Structure

```text
eve-healthcare/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── users/
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── diagnostics/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── bookings/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── payments/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── manage.py
├── requirements.txt
├── .gitignore
├── .env                 # Not committed to Git
└── README.md
```

---

# Features

## 1. Authentication

The API provides:

* User signup
* JWT login
* JWT token refresh
* Protected API endpoints

Authentication is implemented using Django REST Framework and Simple JWT.

### Signup

```http
POST /api/auth/signup/
```

Example:

```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
}
```

### Login

```http
POST /api/auth/login/
```

Example:

```json
{
    "username": "testuser",
    "password": "password123"
}
```

Response contains:

```json
{
    "refresh": "<refresh-token>",
    "access": "<access-token>"
}
```

Use the access token for protected endpoints:

```http
Authorization: Bearer <access-token>
```

### Refresh Token

```http
POST /api/auth/token/refresh/
```

---

# 2. Diagnostic Centres

A diagnostic centre contains:

* Name
* Location

Example:

```text
Apollo Diagnostics
Delhi
```

### Get Centres

```http
GET /api/diagnostics/centres/
```

Authentication is required.

---

# 3. Diagnostic Tests

A diagnostic test contains:

* Test name
* Description

Example tests:

* CBC
* Blood Test
* Thyroid Profile

### Get Tests

```http
GET /api/diagnostics/tests/
```

Authentication is required.

---

# 4. Centre Test Availability and Pricing

A diagnostic test may be available at multiple centres and can have a different price at each centre.

For this reason, the project uses the `CentreTest` model to map:

```text
Diagnostic Centre
        +
Diagnostic Test
        +
Price
```

Example:

```text
Apollo Diagnostics
    |
    +-- CBC              ₹600
    +-- Blood Test       ₹500
    +-- Thyroid Profile  ₹900
```

The centre-test relationship has a unique constraint so the same test cannot be duplicated for the same centre.

### Get Available Centre Tests

```http
GET /api/diagnostics/centre-tests/
```

Example response:

```json
[
    {
        "id": 1,
        "centre": 1,
        "centre_name": "Apollo Diagnostics",
        "test": 1,
        "test_name": "CBC",
        "price": "600.00"
    }
]
```

---

# 5. Booking

A user can create a booking for an available diagnostic test.

### Create Booking

```http
POST /api/bookings/
```

Example:

```json
{
    "centre_test": 1,
    "appointment_datetime": "2026-10-01T10:00:00Z"
}
```

The client does **not** provide the booking amount.

The backend gets the price from `CentreTest` and calculates the amount itself.

For example:

```text
CentreTest price = ₹600

Booking amount = ₹600
```

This prevents a client from manipulating the payment amount.

### Initial Booking Status

Every newly created booking starts with:

```text
PENDING
```

Possible booking statuses:

```text
PENDING
CONFIRMED
FAILED
CANCELLED
```

---

# 6. Booking Cancellation

A pending booking can be cancelled.

```http
POST /api/bookings/{id}/cancel/
```

Example:

```http
POST /api/bookings/7/cancel/
```

A booking can only be cancelled while it is:

```text
PENDING
```

Trying to cancel an already confirmed, failed, or cancelled booking returns a validation error.

Users can only cancel their own bookings.

---

# 7. Simulated Payment

The assignment requires a simulated payment system.

### Create Payment

```http
POST /api/payments/
```

Example:

```json
{
    "booking": 4
}
```

The backend:

1. Finds the booking.
2. Verifies that the booking belongs to the authenticated user.
3. Verifies that the booking is `PENDING`.
4. Gets the amount from the booking.
5. Creates a payment record.
6. Simulates a successful payment.
7. Changes the booking status to `CONFIRMED`.

Example response:

```json
{
    "id": 1,
    "booking": 4,
    "event_id": "generated-event-id",
    "amount": "600.00",
    "status": "SUCCESS",
    "created_at": "2026-09-29T10:00:00Z"
}
```

---

# 8. Payment Webhook

The payment webhook simulates an external payment provider notifying the application about a payment result.

### Webhook

```http
POST /api/payments/webhook/
```

Example successful webhook:

```json
{
    "event_id": "webhook-test-001",
    "booking": 5,
    "amount": "900.00",
    "status": "SUCCESS"
}
```

Example failed webhook:

```json
{
    "event_id": "webhook-failed-001",
    "booking": 6,
    "amount": "600.00",
    "status": "FAILED"
}
```

---

# 9. Webhook Idempotency

Webhook requests can sometimes be delivered more than once.

The API uses a unique `event_id` to prevent duplicate payment records.

Example:

### First request

```text
event_id = webhook-test-001
```

The payment is created.

### Same request again

```text
event_id = webhook-test-001
```

The API detects that the event has already been processed and does not create another payment.

Response:

```json
{
    "message": "Webhook already processed.",
    "payment_id": 5,
    "status": "SUCCESS"
}
```

This prevents duplicate payment records and protects booking state from repeated webhook events.

---

# 10. Payment Amount Validation

The webhook amount is compared with the booking amount.

For example:

```text
Booking amount:  ₹600
Webhook amount: ₹1
```

The request is rejected:

```json
{
    "error": "Payment amount does not match booking amount."
}
```

This prevents an invalid payment event from changing the booking state.

---

# 11. Authorization

Protected endpoints require a valid JWT access token.

A user cannot:

* View another user's bookings
* Pay for another user's booking
* Cancel another user's booking

For example, attempting to pay for another user's booking returns:

```text
404 Booking not found.
```

This avoids exposing whether another user's booking exists.

---

# Database Design

The application uses PostgreSQL.

## Main Entities

### User

Uses Django's built-in User model.

```text
User
 |
 +-- id
 +-- username
 +-- email
 +-- password
```

### DiagnosticCentre

```text
DiagnosticCentre
 |
 +-- id
 +-- name
 +-- location
 +-- created_at
 +-- updated_at
```

### DiagnosticTest

```text
DiagnosticTest
 |
 +-- id
 +-- name
 +-- description
 +-- created_at
 +-- updated_at
```

### CentreTest

Connects a diagnostic centre with a diagnostic test.

```text
CentreTest
 |
 +-- id
 +-- centre
 +-- test
 +-- price
 +-- created_at
```

A unique constraint is applied to:

```text
centre + test
```

### Booking

```text
Booking
 |
 +-- id
 +-- user
 +-- centre_test
 +-- appointment_datetime
 +-- amount
 +-- status
 +-- created_at
 +-- updated_at
```

### Payment

```text
Payment
 |
 +-- id
 +-- booking
 +-- event_id
 +-- amount
 +-- status
 +-- created_at
```

`event_id` is unique to support webhook idempotency.

---

# Booking and Payment Flow

```text
              ┌──────────────┐
              │    User      │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │    Signup    │
              │   / Login    │
              └──────┬───────┘
                     │
                     │ JWT
                     ▼
          ┌──────────────────────┐
          │ Diagnostic Centres   │
          │ & Available Tests    │
          └──────────┬───────────┘
                     │
                     ▼
             ┌──────────────┐
             │ Create       │
             │ Booking      │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │   PENDING    │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │   Payment    │
             └──────┬───────┘
                    │
             ┌──────┴───────┐
             │              │
          SUCCESS         FAILED
             │              │
             ▼              ▼
       CONFIRMED          FAILED
```

Webhook flow:

```text
External Payment Provider
          │
          ▼
   /api/payments/webhook/
          │
          ▼
     Validate event
          │
          ▼
   Check event_id
          │
          ├── Already processed
          │       │
          │       ▼
          │    Ignore duplicate
          │
          ▼
   Validate booking
          │
          ▼
   Validate amount
          │
          ▼
     Create Payment
          │
          ▼
   Update Booking Status
```

---

# API Endpoints

| Method | Endpoint                         | Authentication | Purpose                  |
| ------ | -------------------------------- | -------------- | ------------------------ |
| POST   | `/api/auth/signup/`              | No             | Register user            |
| POST   | `/api/auth/login/`               | No             | Obtain JWT tokens        |
| POST   | `/api/auth/token/refresh/`       | No             | Refresh access token     |
| GET    | `/api/diagnostics/centres/`      | Yes            | List diagnostic centres  |
| GET    | `/api/diagnostics/tests/`        | Yes            | List diagnostic tests    |
| GET    | `/api/diagnostics/centre-tests/` | Yes            | List tests and prices    |
| GET    | `/api/bookings/`                 | Yes            | List user's bookings     |
| POST   | `/api/bookings/`                 | Yes            | Create booking           |
| POST   | `/api/bookings/{id}/cancel/`     | Yes            | Cancel pending booking   |
| POST   | `/api/payments/`                 | Yes            | Create simulated payment |
| POST   | `/api/payments/webhook/`         | No*            | Process payment webhook  |
| GET    | `/api/schema/`                   | No             | OpenAPI schema           |
| GET    | `/api/docs/`                     | No             | Swagger UI               |

`/api/payments/webhook/` is intentionally available without JWT because it represents a callback from an external payment provider. In a production system, it should be protected using webhook signature verification/shared-secret authentication.

---

# API Documentation

Swagger/OpenAPI documentation is available at:

```text
http://127.0.0.1:8000/api/docs/
```

OpenAPI schema:

```text
http://127.0.0.1:8000/api/schema/
```

Swagger can be used to test the APIs without building a frontend application.

---

# Local Setup

## 1. Clone the repository

```bash
git clone <repository-url>
cd eve-healthcare
```

## 2. Create a virtual environment

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Windows:

```powershell
venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Create PostgreSQL database

Create a PostgreSQL database and user.

Example:

```sql
CREATE DATABASE eve_healthcare;
CREATE USER eve_user WITH PASSWORD 'your_password';
```

Grant the required permissions to the user.

---

## 5. Configure environment variables

Create `.env` in the project root:

```env
DB_NAME=eve_healthcare
DB_USER=eve_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

Do not commit `.env` to Git.

---

## 6. Apply migrations

```bash
python manage.py migrate
```

---

## 7. Create a superuser

```bash
python manage.py createsuperuser
```

---

## 8. Run the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

Swagger:

```text
http://127.0.0.1:8000/api/docs/
```

Django Admin:

```text
http://127.0.0.1:8000/admin/
```

---

# Running Tests

Run the complete test suite:

```bash
python manage.py test
```

The project currently includes tests covering:

* Booking creation
* Invalid/past appointment time
* Booking cancellation
* Unauthorized booking access
* Successful payments
* Failed payments
* Successful webhooks
* Duplicate webhook events
* Invalid booking IDs
* Payment amount mismatch
* Unauthorized payment attempts
* Payment state validation

Expected result:

```text
Ran 14 tests

OK
```

---

# Validation and Edge Cases

The application handles several important edge cases.

### Invalid appointment

Appointments must be in the future.

```text
Past appointment → 400 Bad Request
```

### Invalid booking

```text
Invalid booking ID → 404 Not Found
```

### Unauthorized booking access

Users cannot access another user's booking through payment/cancellation operations.

### Duplicate webhook

Repeated `event_id` does not create another payment.

### Payment amount mismatch

The webhook amount must match the booking amount.

### Payment for confirmed booking

A booking that is already confirmed cannot be paid again.

### Cancellation

Only pending bookings can be cancelled.

### Failed payment

A failed payment changes the booking status to:

```text
FAILED
```

---

# Design Decisions

## Why CentreTest?

A diagnostic test can be offered by multiple diagnostic centres and each centre can have a different price.

Instead of storing centre and test directly in the booking, `CentreTest` represents the actual test offering.

This also provides a single source for the current price used when creating a booking.

---

## Why calculate amount on the backend?

The client should not be trusted to provide the payment amount.

Instead of accepting:

```json
{
    "centre_test": 1,
    "amount": 1
}
```

the backend calculates:

```text
amount = CentreTest.price
```

This prevents basic price manipulation.

---

## Why use transactions?

Payment creation and booking status updates should be treated as one operation.

For example:

```text
Create Payment
      +
Update Booking
```

are performed inside a database transaction.

If the transaction fails, the database can roll back the operation instead of leaving inconsistent payment and booking states.

---

## Why use event_id?

External payment systems can send the same webhook more than once.

The unique `event_id` allows the backend to identify an event that has already been processed.

This provides webhook idempotency.

---

# Assumptions

1. Payments are simulated because there is no real payment gateway in the assignment.
2. Simulated payments currently return a successful payment through the payment endpoint.
3. Webhooks can report either `SUCCESS` or `FAILED`.
4. A payment can only be processed for a pending booking.
5. A booking cannot be cancelled after payment confirmation.
6. The booking amount is derived from the selected `CentreTest`.
7. Webhook requests are treated as external provider callbacks. A production implementation should add signature verification.
8. PostgreSQL is used as the primary database.
9. JWT is used for API authentication.

---

# Possible Future Improvements

The current implementation focuses on the core assignment requirements. Possible production improvements include:

* Redis caching
* Celery background tasks
* Docker and Docker Compose
* Production payment gateway integration
* Webhook signature verification
* Webhook retry handling
* Structured logging
* API rate limiting
* Pagination and filtering
* More comprehensive integration tests
* CI/CD pipeline
* Monitoring and error tracking
* Improved booking state transition management

---

# Security Considerations

* Passwords are handled through Django's password hashing system.
* JWT authentication protects user-specific APIs.
* Database credentials are stored in environment variables.
* `.env` is excluded from Git.
* Client-provided booking amounts are not trusted.
* Users cannot perform payment/cancellation operations on another user's booking.
* Webhook event IDs are unique to prevent duplicate processing.

For production use, webhook signature verification and HTTPS would also be required.

---

# Assignment Requirements Coverage

| Requirement              | Implementation |
| ------------------------ | -------------- |
| User signup              | Implemented    |
| User login               | Implemented    |
| JWT authentication       | Implemented    |
| Diagnostic centres       | Implemented    |
| Diagnostic tests         | Implemented    |
| Centre/test pricing      | Implemented    |
| Booking API              | Implemented    |
| Booking status           | Implemented    |
| Simulated payment        | Implemented    |
| Payment webhook          | Implemented    |
| Webhook idempotency      | Implemented    |
| Amount validation        | Implemented    |
| Authorization            | Implemented    |
| Booking cancellation     | Implemented    |
| Invalid request handling | Implemented    |
| Automated tests          | Implemented    |
| PostgreSQL               | Implemented    |
| Swagger/OpenAPI          | Implemented    |

---

# Author

**Vikas Yadav**

GitHub: `https://github.com/devopsvikass`

LinkedIn: `https://www.linkedin.com/in/developervikass`

---

# License

This project was developed as part of the EVE Healthcare SDE Intern Backend Engineering Assignment.
