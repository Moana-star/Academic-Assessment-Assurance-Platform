# Development Guide

1. Clone the repository and create a local virtual environment.
2. Pull the latest `main` branch before starting a new development session.
3. Create a focused feature branch, for example `feature/student-management` or `feature/face-enrollment-ui`.
4. Keep changes focused and use clear commit messages.
5. Run relevant checks and tests before committing.
6. Review the complete diff before pushing changes.
7. Keep documentation aligned with application behavior and configuration.

## Project structure

- Backend application code and configuration are primarily in `config/` and `integrity/`.
- Frontend templates and browser assets are primarily in `templates/` and `static/`.
- Project architecture, API contracts, and development notes are in `docs/`.

## Validation

Run the following commands from the project root:

```powershell
python manage.py check
python manage.py test
```

## Never commit

- `.env` files or credentials
- `db.sqlite3` or production databases
- Virtual environments and caches
- Student personal records, photographs, or biometric samples/templates
- Real access tokens, passwords, or private keys
