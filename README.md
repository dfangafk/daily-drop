# dailydrop

Daily content curation pipeline: fetch RSS feeds → LLM picks top items matching your interests → email digest + static archive.

## How it works

1. Fetches new items from all configured RSS sources (YouTube, podcasts, tech blogs)
2. Deduplicates against previously-seen items
3. Sends new items to an LLM (Gemini by default) scored against your interest profile
4. Emails a daily digest via Gmail SMTP
5. Publishes a browsable HTML archive to GitHub Pages

## Setup

```bash
uv sync
cp .env.example .env
# fill in .env with your API keys and email credentials
```

## Configuration

### Sources (`sources.yaml`)

```yaml
sources:
  - name: "Lex Fridman Podcast"
    url: "https://lexfridman.com/feed/podcast/"
  - name: "Hacker News"
    url: "https://news.ycombinator.com/rss"
```

YouTube channels expose RSS at:
`https://www.youtube.com/feeds/videos.xml?channel_id=<CHANNEL_ID>`

### Interests (`config/interests.txt`)

Plain text file — one interest per line. The LLM uses this to pick your top items.

```
machine learning and AI research
startups and product thinking
```

### Environment variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Gemini API key (primary LLM) |
| `SENDER_GMAIL` | Gmail address to send from |
| `GMAIL_APP_PASSWORD` | Gmail [app password](https://support.google.com/accounts/answer/185833) |
| `RECEIVER_EMAIL` | Address to receive the digest |
| `LLM__PROVIDER` | `auto` (default), `api`, `claude_code_cli`, `codex_cli` |
| `LLM__TOP_N` | Number of items to recommend (default: `5`) |
| `PIPELINE__ENABLE_LLM` | `true`/`false` |
| `PIPELINE__ENABLE_NOTIFY` | `true`/`false` |
| `PIPELINE__ENABLE_ARCHIVE` | `true`/`false` |

## Run locally

```bash
uv run python -m dailydrop.pipeline
```

## Run tests

```bash
uv run pytest
```

## GitHub Actions setup

1. Push this repo to GitHub
2. Go to **Settings → Secrets and variables → Actions** and add:
   - `GEMINI_API_KEY`
   - `SENDER_GMAIL`, `GMAIL_APP_PASSWORD`, `RECEIVER_EMAIL`
3. Go to **Settings → Pages** and set Source to **GitHub Actions**
4. The workflow runs daily at 12:00 UTC and publishes `docs/archive.html` to Pages
