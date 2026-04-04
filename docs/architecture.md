# Architecture

A daily content curation pipeline that ingests content from multiple sources, uses an LLM to surface items matching the user's interests, and delivers a digest via email with a browsable HTML archive.

---

## High-Level Flow

```
Sources (RSS/API)
      │
      ▼
  Fetcher Layer          ← one fetcher per source type
      │
      ▼
  Deduplication          ← skip already-seen items (persisted state)
      │
      ▼
  LLM Ranking            ← score/select items against user interest prompt
      │
      ├──► Daily Email   ← highlighted picks via Gmail SMTP
      │
      └──► HTML Archive  ← all new items, published to GitHub Pages
```

---

## Components

### 1. Sources
| Source | Method |
|---|---|
| YouTube channels | RSS (`/feeds/videos.xml`) |
| Apple Podcasts / RSS feeds | RSS |
| Tech company product blogs | RSS or HTML scrape |

X (Twitter) is deferred. New sources can be added by implementing the fetcher interface.

### 2. Fetcher Layer
- Each source has a small fetcher module that returns a normalized `Item` schema:
  `{ id, source, title, url, published_at, description }`
- Fetchers are configured via a YAML/JSON file listing source URLs and types.

### 3. Deduplication
- A lightweight JSON state file tracks seen item IDs.
- Persisted across runs via GitHub Actions cache or a file committed to a dedicated branch.

### 4. LLM Ranking
- User defines their interests in a plain-text prompt (e.g., `interests.txt`).
- New items are passed to the LLM with the interest prompt; it selects and ranks the top picks.
- LLM provider is abstracted behind a simple interface — defaults to Gemini, swappable via config.

### 5. Digest Email
- Sends a daily HTML email via Gmail SMTP.
- Top section: LLM-recommended picks with a brief reason for each.
- Bottom section: link to the full HTML archive for that day.

### 6. HTML Archive
- A static `index.html` is generated listing all new items grouped by source.
- Published to GitHub Pages so it's browsable at a stable URL.

---

## Runtime

**GitHub Actions** runs the full pipeline on a daily schedule (`cron`).

```
.github/workflows/daily-digest.yml
  - schedule: daily (e.g., 7 AM UTC)
  - steps:
      1. Checkout repo + restore state cache
      2. Install dependencies
      3. Run fetchers
      4. Run LLM ranking
      5. Generate HTML archive → commit/push to gh-pages
      6. Send email
      7. Save updated state cache
```

Secrets (Gemini API key, Gmail credentials) are stored as GitHub Actions secrets.

---

## Repository Layout (proposed)

```
name-tbd/
├── docs/
│   └── architecture.md
├── src/
│   ├── fetchers/          # one module per source type (youtube.py, rss.py, ...)
│   ├── llm/               # LLM abstraction + Gemini implementation
│   ├── digest/            # email renderer + HTML archive generator
│   └── main.py            # pipeline entry point
├── config/
│   ├── sources.yaml       # list of feeds/channels to watch
│   └── interests.txt      # user interest prompt for LLM
├── state/
│   └── seen.json          # persisted deduplication state
└── .github/
    └── workflows/
        └── daily-digest.yml
```

---

## Key Design Decisions

- **RSS-first**: Avoids fragile scraping where possible; most sources expose RSS.
- **Stateless pipeline**: Each run is self-contained; state is minimal (seen IDs only).
- **Config-driven sources**: Adding a new feed requires only editing `sources.yaml`, no code change.
- **Pluggable LLM**: Provider is injected at runtime via an env var / config flag so Gemini can be swapped for Claude, OpenAI, or a local model without touching pipeline logic.
- **GitHub Pages for archive**: Zero infrastructure — the HTML is just a committed artifact.
