# MG Engineering Academy — Vercel Ready

This build uses Vercel's current zero-configuration Flask deployment model.

- Keep `app.py` at the repository root.
- Keep `requirements.txt` at the repository root.
- Static assets are in `public/` for Vercel CDN delivery.
- No `api/` wrapper and no rewrite rule are required.
- Vercel should detect Flask automatically.

Deploy by pushing the repository root to GitHub and importing the repository into Vercel.

Health check: `/health`
