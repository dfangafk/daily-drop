# Daily Drop

A self-hosted pipeline that monitors RSS/Atom feeds and delivers a daily email digest. Configure your sources, set your credentials, and get a curated inbox drop every morning.

## Quick start

```bash
git clone https://github.com/dfangafk/daily-drop.git
cd daily-drop
uv sync
cp sources.example.yaml sources.yaml
cp .env.example .env   # then fill in your credentials
uv run python -m dailydrop.pipeline
```

## Add your sources

Edit `sources.yaml` (example):

```yaml
sources:
  - name: "Lex Fridman Podcast"
    url: "https://lexfridman.com/feed/podcast"

  - name: "OpenAI News"
    url: "https://openai.com/news/rss.xml"

  - name: "Y Combinator"
    url: "https://www.youtube.com/feeds/videos.xml?channel_id=UCcefcZRL2oaA_uBNeo5UOWg"
```

Each entry needs a `name` and a feed `url`. Both RSS and Atom formats work.

**Finding a feed URL:** paste any website into [rss.com/tools/find-my-feed/](https://rss.com/tools/find-my-feed/) — it will locate the feed URL for you.

## Configure credentials

Create a `.env` file in the project root:

```
SENDER_EMAIL=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
RECEIVER_EMAIL=you@gmail.com
```

SMTP settings are auto-detected from your sender domain (Gmail, Outlook, Yahoo, iCloud, Fastmail). No extra config needed for those providers.

### Getting a Gmail app password

Gmail requires an app password instead of your regular password.

1. Enable 2-Step Verification on your Google account if you haven't already.
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Click **Create app password**, give it a name (e.g. "daily-drop"), and click **Create**.
4. Copy the 16-character password and paste it as `SMTP_PASSWORD` in your `.env`.

For other providers, check your provider's documentation on how to generate an app password or allow SMTP access.

### Optional settings

| Variable | Default | Description |
|---|---|---|
| `NOTIFY__TIMEZONE` | `America/New_York` | Timezone for email timestamps |
| `PIPELINE__LOG_LEVEL` | `INFO` | Log verbosity (`DEBUG`, `INFO`, `WARNING`) |
| `NOTIFY__SMTP_HOST` | auto | Override SMTP host |
| `NOTIFY__SMTP_PORT` | auto | Override SMTP port |

## Run manually

```bash
uv run python -m dailydrop.pipeline
```

Flags:

| Flag | Default | Description |
|---|---|---|
| `--lookback-hours N` | `24` | Look-back window in hours |
| `--reference-time DATETIME` | now | Treat this time as "now" (ISO 8601) |
| `--skip-email` | — | Run the pipeline without sending email |

## Automate with GitHub Actions

The included workflow (`.github/workflows/daily_drop.yml`) runs the pipeline daily at 12:00 UTC (7 AM ET).

Add these three secrets to your repository under **Settings → Secrets and variables → Actions**:

- `SENDER_EMAIL`
- `SMTP_PASSWORD`
- `RECEIVER_EMAIL`

The workflow runs tests first and only sends the email if they pass. You can also trigger it manually from the Actions tab.

## Known limitations

- **Email providers:** Only Gmail has been tested. Other providers' SMTP setup (Outlook, Yahoo, iCloud, Fastmail) may require additional configuration or may not work as expected.
- **Large digests:** There is no pagination or truncation — if a lookback window captures a large number of items, the email may be too long to render or deliver reliably. A fallback delivery method (e.g. a hosted page or attachment) has not been implemented yet.
- **Stateless deduplication:** The pipeline uses a lookback window rather than a persistent seen-items store. If a run fails or is skipped, items from that window are silently dropped and will not be surfaced in a later run. A persistent store tracking seen item IDs is a likely future improvement.
- **RSS-only ingestion:** Sources must expose an RSS or Atom feed. Pages without a feed (e.g. social media profiles, paywalled sites) cannot be monitored yet. Future work may explore scraping or other retrieval approaches.
