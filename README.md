# Automated Cold-Outreach Pipeline

> One domain in → four stages fire → emails sent. Zero manual steps.

## Architecture

```
[You] stripe.com
        │
        ▼
┌──────────────────┐
│  Stage 1         │  Ocean.io
│  Lookalike cos   │  seed domain → similar company domains
└────────┬─────────┘
         │ [domain list]
         ▼
┌──────────────────┐
│  Stage 2         │  Prospeo
│  Decision-makers │  domains → C-suite/VP + LinkedIn URLs
└────────┬─────────┘
         │ [prospect list]
         ▼
┌──────────────────┐
│  Stage 3         │  Eazyreach
│  Email resolver  │  LinkedIn URLs → verified work emails
└────────┬─────────┘
         │ [contact list]
         ▼
  ⚠  SAFETY CHECKPOINT  (you review before anything fires)
         │
         ▼
┌──────────────────┐
│  Stage 4         │  Brevo
│  Outreach sender │  contacts → personalized emails sent
└──────────────────┘
```

## Quick Start

### 1. Clone / copy the project
```bash
git clone <repo>
cd outreach-pipeline
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API keys
```bash
cp .env.example .env
# Edit .env with your keys from each tool's dashboard
```

### 4. Run the pipeline
```bash
python main.py stripe.com
```

---

## Setup Guide — Getting Your API Keys

### Domain (Required First!)
Get a domain from **Namecheap** (reimbursed) or the GitHub Student Developer Pack.
Use it to create a company email (e.g. `you@yourdomain.com`).

### Ocean.io
1. Sign up at [ocean.io](https://ocean.io) **using your company email**
2. Go to Settings → API → copy your API key → `OCEAN_API_KEY`

### Prospeo
1. Sign up at [app.prospeo.io/api](https://app.prospeo.io/api)
2. Go to API section → copy key → `PROSPEO_API_KEY`

### Eazyreach
1. Sign up at [eazyreach.app](https://eazyreach.app)
2. Send account details to VocaLabs for credit top-up
3. Copy API key from dashboard → `EAZYREACH_API_KEY`

### Brevo
1. Sign up at [app.brevo.com](https://app.brevo.com)
2. Settings → SMTP & API → API Keys → Generate → `BREVO_API_KEY`
3. Set `BREVO_SENDER_EMAIL` to your verified sender address
4. Set `BREVO_SENDER_NAME` to your name

---

## Configuration Options

| Variable | Default | Description |
|---|---|---|
| `OCEAN_MAX_COMPANIES` | `10` | Max lookalike companies to pull |
| `PROSPEO_TITLES` | `CEO,CTO,...` | Title keywords to match decision-makers |
| `EAZYREACH_DELAY_MS` | `500` | Delay between LinkedIn lookups |
| `BREVO_DELAY_MS` | `200` | Delay between email sends |
| `MAX_EMAILS_PER_RUN` | `50` | Hard cap on emails per run |
| `DRY_RUN` | `false` | Set `true` to preview without sending |

---

## Testing Without API Keys

Use **DRY_RUN** mode to see exactly what would be sent:
```bash
DRY_RUN=true python main.py stripe.com
```

---

## Project Structure

```
outreach-pipeline/
├── main.py                   # Entry point — orchestrates all 4 stages
├── .env.example              # Template for your API keys
├── requirements.txt
├── config/
│   └── settings.py           # Config loader + validation
├── stages/
│   ├── stage1_ocean.py       # Ocean.io lookalike finder
│   ├── stage2_prospeo.py     # Prospeo decision-maker finder
│   ├── stage3_eazyreach.py   # Eazyreach email resolver
│   └── stage4_brevo.py       # Brevo email sender + copy
└── utils/
    ├── logger.py             # Logging + CLI pretty-print
    ├── checkpoint.py         # Safety checkpoint before send
    └── retry.py              # Exponential backoff for API calls
```

---

## Interview Notes

### Edge cases handled
- **Rate limits** — exponential backoff retry on 429/5xx; per-stage sleep between calls
- **Missing contacts** — stages gracefully skip null LinkedIn URLs / emails
- **Partial failures** — one failed company doesn't crash the whole run; errors logged
- **Deduplication** — LinkedIn URLs deduped in Stage 2 to prevent double-emailing
- **Safety cap** — `MAX_EMAILS_PER_RUN` prevents accidental mass blast
- **Safety checkpoint** — human approves before a single email fires

### Why each decision was made
- **Modular stages** — each stage is an isolated function; easy to swap any API
- **Retry wrapper** — centralized; all 4 stages share the same backoff logic
- **Config via .env** — no keys in code; easy to rotate without touching logic
- **Structured logging** — `pipeline.log` has full debug trace for post-run review

### Extending a stage (live tweak)
To swap Ocean.io for another data source, only `stages/stage1_ocean.py` changes.
`main.py` only cares that the function returns `list[str]` of domains.
