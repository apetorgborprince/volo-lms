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

## V6 Management & Learning Resource Upgrades

This V6 build now includes:

- **Teacher learner creation:** teachers can create learner accounts from People and optionally enroll the learner into one of their assigned courses.
- **Administrator Excel account management:** administrators can import teachers and learners from `.xlsx`/`.xlsm` using `Role, Name, Username, Class, Subject, Course Code, Password`. If Password is blank, Volo generates a strong temporary password and downloads a credentials workbook after the import.
- **Administrator course assignment:** administrators create courses and assign a teacher at creation time. Teacher course visibility is limited to assigned courses.
- **Teacher learner notes:** teachers can publish PDF, Word, PowerPoint, spreadsheet, image or text notes, or publish an external resource URL. Uploaded note files are stored in the production database for persistence across Render deployments.
- **Google Forms deployment:** teachers can create the assessment in Google Forms, paste its published `docs.google.com/forms` URL into Volo, and deploy it to the selected course. Learners can open the form directly or inside the LMS.
- **Course-aware permissions:** teachers can only create lessons, assignments, quizzes, notes and Google Forms for courses assigned to them.

### Excel import columns

`Role | Name | Username | Class | Subject | Course Code | Password`

`Role` accepts `Student` or `Teacher`. Leave `Password` blank to generate a secure temporary password. `Course Code` can be used to enroll imported learners into an existing course.

### Google Forms workflow

1. Teacher opens Google Forms and creates the form.
2. Teacher publishes the form and copies the responder URL ending in `/viewform`.
3. Teacher selects the Volo course, enters the title and published URL, then chooses **Deploy Google Form in Volo**.
4. Learners open the deployed form from their course page.

Google Forms remains hosted by Google; Volo stores the course mapping and published link.

## V7 Management & Engagement Upgrade

This release adds non-AI analytics, a notification center, optional SMTP email notifications, forced temporary-password changes, login lockout protection, scheduled/expiring course notes, persisted virtual-lab sessions/submissions, and richer Excel account imports with optional email addresses.

### Optional SMTP configuration
Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, and `SMTP_STARTTLS` to enable email delivery. The LMS continues to work with in-app notifications when SMTP is not configured.
