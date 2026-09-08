# Watchtower

Self-hosted page-change watcher. Point it at a URL (a price, a job listing,
a restock page), give it a check interval, and it tells you when the page
actually changes — no polling it yourself.

## Features

- Per-user accounts (JWT auth), each user's watches are private to them
- Background scheduler checks pages on their own interval — no manual polling
- Optional CSS selector to watch just one part of a page (e.g. `.price`)
- Full check history per watch, with change detection by content hash
- Small live dashboard (auto-refreshing table, no page reloads)

## Quickstart

```bash
pip install -e ".[dev]"
cp .env.example .env          # edit JWT_SECRET before going anywhere near production
uvicorn watchtower.main:app --reload
```

Visit `http://localhost:8000` for the dashboard, `http://localhost:8000/docs`
for the interactive API.

```bash
# Register + log in
curl -X POST localhost:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"a-real-password"}'

curl -X POST localhost:8000/auth/login \
  -d "username=you@example.com&password=a-real-password"
# -> copy the access_token from the response

# Add a watch
curl -X POST localhost:8000/watches \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"name":"Widget price","url":"https://example.com/widget","css_selector":".price","check_interval_minutes":30}'
```

## Security measures baked in

- **SSRF protection** — every watch URL is resolved and checked before
  fetching; private/loopback/link-local IPs (including cloud metadata
  endpoints like `169.254.169.254`) are refused. See `scraper.py::_assert_public_host`.
- **Auth** — passwords hashed with bcrypt, JWT-based sessions, no secrets hardcoded.
- **Ownership checks** — every watch lookup re-verifies the requester owns
  it server-side; a mismatch returns 404, not 403, so existence isn't leaked.
- **Rate limiting** — register/login/create-watch endpoints are rate-limited
  per IP to blunt brute-forcing and abuse.
- **Input validation** — URLs must be http(s), check intervals have a
  configurable floor (default 5 min) so the tool can't be used to hammer a site.
- **Production guardrail** — the app refuses to start with `ENV=production`
  if the JWT secret is still the development placeholder.

## Architecture notes

- The scheduler is a single in-process APScheduler job that polls the
  database every `SCHEDULER_POLL_SECONDS` for watches that are due, rather
  than one job per watch — adding/editing a watch is just a database write.
  This is simple and reliable for a single instance; a multi-instance
  deployment would need a distributed scheduler (e.g. Celery beat) instead.
- SQLite by default for zero-setup local dev. Swap `DATABASE_URL` to a
  Postgres URL for production — no code changes needed.
- Notifications currently just log; `scheduler.py` has a clear extension
  point (`# Extension point: send an email/webhook/Slack notification here`)
  to wire in real delivery.

## Development

```bash
pytest
ruff check src tests
```

## License

MIT
