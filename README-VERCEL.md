# MG Engineering Academy — Vercel Ready

This package is configured specifically for the new GitHub + Vercel project.

## Vercel entrypoint
- `api/index.py` — Flask WSGI application
- `vercel.json` — explicit Python Function routing
- `templates/` — Jinja templates
- `public/` — CSS, JS and logo
- `requirements.txt` — Flask dependencies

## Health check
Open `/health` after deployment. It should return JSON with:
`{"ok": true, ...}`

## Important
The app uses SQLite under `/tmp` when `VERCEL` is set, because Vercel's deployed filesystem is not a persistent writable database location. This is enough to get the new deployment running, but a persistent hosted database should be connected before using real student accounts, enrollments, or certificates in production.

## Deployment
Push the contents of this ZIP to the root of the NEW GitHub repository, then redeploy the NEW Vercel project. Do not move the old domain yet. Test the Vercel `.vercel.app` URL first.
