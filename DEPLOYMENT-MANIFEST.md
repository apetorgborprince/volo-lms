# Volo LMS V6 Deployment Manifest

## Required
- Python 3.10+
- Flask and dependencies from `requirements.txt`
- WSGI-capable hosting
- HTTPS
- Persistent writable database/storage

## Required environment variables
- SECRET_KEY
- ADMIN_USERNAME
- ADMIN_PASSWORD
- ADMIN_FULL_NAME

## Roles
- admin
- tutor
- student

## Explicitly absent
- admin
- parent
- AI
- demo users
- default credentials

## First launch
1. Set environment variables.
2. Start the application.
3. Volo creates the single Administrator if none exists.
4. Administrator creates Teachers and Students.
5. Administrator creates/maintains school learning content.
