# Volo LMS — Production V6

Volo LMS is a Flask-based science learning platform using the existing professional Volo HTML/CSS/JavaScript interface.

## Production account model

There are exactly three Volo application roles:

- **Administrator (`admin`)** — system owner. The initial administrator is created from environment variables; no administrator password is embedded in source code.
- **Teacher (`tutor`)** — created by an Administrator.
- **Student (`student`)** — created by an Administrator.

Volo does **not** create or support:
- Super Admin
- Parent/Guardian accounts
- Demo accounts
- Default passwords
- AI features

## Core platform

- Professional Volo dashboard and responsive shell
- Courses and lessons
- Curriculum Explorer
- Curriculum-aligned lesson creation
- Quizzes and assessment attempts
- Assignments and teacher grading
- Practical Studio / virtual laboratory experiences
- Practical design aligned to verified curriculum indicators
- Learner progress
- Teacher learner monitoring
- Notifications/activity records
- User management
- Security headers and secure sessions

## No seeded users

The application never seeds a user account.

On first startup, the app requires:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SECRET_KEY`

If an Administrator does not already exist, Volo creates exactly one from those environment variables. If they are missing, startup fails rather than creating a default account.

## Deployment

### Local verification
1. Create a Python virtual environment.
2. Install `requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Set unique production values for `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`.
5. Run `python run.py` for a development smoke test.

### Production
Use a Python-capable host and a WSGI server (for example Gunicorn or the provider's managed WSGI process). Do not expose Flask's development server directly to the public internet.

Set:
- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SESSION_COOKIE_SECURE=1`

Enable HTTPS and database/file backups.

## Important migration note

This V6 package is designed to start with a clean production database. Do not copy a database containing the previous V5 demo accounts into production.

## Interface

The existing Volo HTML/CSS/JavaScript interface is retained as the foundation. The WordPress block-editor redesign is not required.

## AI

AI functionality has been removed from the production V6 application.
