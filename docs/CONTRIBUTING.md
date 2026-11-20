# Collaboration Guide

1. Clone the repository and create a local virtual environment when implementation begins.
2. Pull the latest `main` before starting work.
3. Create a feature branch, for example `feature/student-management` or `feature/face-enrollment-ui`.
4. Keep changes focused and commit with clear messages.
5. Run relevant tests and inspect the diff before pushing.
6. Open a pull request to `main`; request review from the other developer.
7. Resolve conflicts together. Do not force-push shared branches without agreement.

## File ownership

Backend work primarily belongs in `config/` and `integrity/`. Frontend work primarily belongs in `templates/` and `static/`. Shared files require coordination.

## Never commit

- `.env` files or credentials
- `db.sqlite3` or production databases
- Virtual environments and caches
- Student personal records, photographs, or biometric samples/templates
- Real access tokens, passwords, or private keys
