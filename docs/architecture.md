# Architecture

A daily content curation pipeline that ingests RSS/Atom feeds, normalizes the results, and delivers a digest via email.

---

## High-Level Flow

```
Sources (RSS/Atom feeds)
      │
      ▼
  Fetcher                 ← feedparser; one call per configured URL
      │
      ▼
  Time-window filter      ← keep items published within last N hours (default 24)
      │
      ▼
  Normalize               ← strip HTML, unescape entities, convert to local timezone
      │
      ▼
  Daily Email             ← HTML + plain-text digest via SMTP
```

---

## Components

### 1. Sources
| Source | Method |
|---|---|
| YouTube channels | Atom |
| Podcasts | RSS/Atom |
| Tech company blogs | RSS/Atom |

Sources are listed in `sources.yaml` with `name` and `url` fields. Adding a new feed requires only editing that file.

### 2. Fetcher (`dailydrop/fetch.py`)
- `fetch_all_sources(urls)` — fetches all configured feeds in sequence, returns items sorted newest-first.
- `filter_recent_items(items, lookback_hours, reference_time)` — drops items outside the lookback window.
- Uses `feedparser` to handle both RSS and Atom formats.
- Normalizes each entry into an `Item`:
  `{ id, title, url, published_at, description, source_name, source_url }`
- Feed errors are logged as warnings and skipped; they never fail the pipeline.

### 3. Time-Window Filter
- Items are included only if `published_at` falls within the configured lookback (default: 24 h).
- No cross-run state file — each run fetches fresh and applies the time window.

### 4. Normalize (`dailydrop/normalize.py`)
- `normalize_items(items)` modifies items in-place:
  - **Description**: strips HTML tags, unescapes entities, collapses whitespace, truncates to 300 chars.
  - **Timestamp**: converts UTC → configured local timezone (default `America/New_York`).

### 5. Digest Email (`dailydrop/notify.py`)
- Sends HTML + plain-text email via SMTP.
- **SMTP provider auto-detection**: infers host/port/security from the sender's domain.
  Supported: Gmail, Outlook, Yahoo, iCloud, Fastmail.
  Manual override via `NOTIFY__SMTP_HOST` + `NOTIFY__SMTP_PORT` env vars.
- Port 465 → `SMTP_SSL`; ports 587/25/2525 → `SMTP` + STARTTLS.
- **Templates** (Jinja2, in `dailydrop/templates/`):
  - `drop.subject.jinja2` — "Daily Drop — YYYY-MM-DD (N new finds)"
  - `drop.html.jinja2` — styled card layout; YouTube items include a thumbnail.
  - `drop.txt.jinja2` — plain-text fallback.
- Email credentials not set → notification skipped silently (pipeline still succeeds).

### 6. Item Model (`dailydrop/models.py`)
- `Item` dataclass.
- `youtube_id` property — extracts YouTube video ID from the URL via regex; used by the HTML template for thumbnail embedding.

### 7. Config (`dailydrop/config.py`)
- Pydantic-settings backed by environment variables and an optional `.env` file.
- Key settings: `SENDER_EMAIL`, `SMTP_PASSWORD`, `RECEIVER_EMAIL`, `NOTIFY__TIMEZONE`, `PIPELINE__LOG_LEVEL`.

---

## Runtime

**GitHub Actions** runs the full pipeline on a daily schedule (`cron`).

```
.github/workflows/daily_ingest.yml
  - schedule: "0 12 * * *"  (12:00 UTC = 7 AM EST / 8 AM EDT)
  - jobs:
      test   — always: checkout → uv sync → pytest
      ingest — schedule/dispatch only, needs: test
               checkout → uv sync → python -m dailydrop.pipeline
```

Secrets required: `SENDER_EMAIL`, `SMTP_PASSWORD`, `RECEIVER_EMAIL`.

---

## Repository Layout

```
daily-drop/
├── .github/
│   └── workflows/
│       └── daily_ingest.yml
├── dailydrop/
│   ├── config.py          # pydantic-settings, SMTP provider registry
│   ├── fetch.py           # RSS/Atom fetching and time-window filter
│   ├── models.py          # Item dataclass
│   ├── normalize.py       # HTML cleaning, timezone conversion
│   ├── notify.py          # email rendering and SMTP delivery
│   ├── pipeline.py        # CLI entry point, orchestration
│   └── templates/
│       ├── drop.subject.jinja2
│       ├── drop.html.jinja2
│       └── drop.txt.jinja2
├── tests/
├── docs/
│   └── architecture.md
├── sources.yaml           # list of RSS/Atom URLs to watch
├── pyproject.toml
└── uv.lock
```

---

## Key Design Decisions

- **RSS-first**: avoids fragile scraping; feedparser handles both RSS and Atom uniformly.
- **Time-window instead of state file**: each run is fully self-contained; no persistent deduplication cache needed given a 24 h schedule.
- **Config-driven sources**: adding a feed requires only editing `sources.yaml`.
- **SMTP auto-detection**: provider inferred from sender domain so users don't need to look up server settings.
- **Fail-soft fetching**: individual feed errors are logged and skipped rather than aborting the pipeline.
- **No LLM ranking (yet)**: all items within the time window are included in the digest. LLM-based enrichment and ranking is a planned future addition.
