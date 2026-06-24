# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TrueShotOdds is a sports betting arbitrage platform. Scrapers push odds to Redis → the engine detects arbitrage/EV bets and publishes results to Redis → the FastAPI backend streams results to the React frontend via WebSocket.

**Deployment:** Frontend on Cloudflare Pages, backend + scrapers + Redis on EC2 via Docker Compose. Cloudflare tunnel (`cloudflared`) exposes the backend.

**Repo structure:** Two Git submodules — `tso_client` (React frontend) and `tso_server` (FastAPI backend + webscraper + Docker Compose). Work in the submodule directories; after pushing a submodule, update the root repo to point to the new commit.

## Commands

### Frontend (`cd tso_client`)
```bash
npm run dev        # Dev server on :5173
npm run build      # TypeScript check + Vite production build
npm run lint       # ESLint
```

### Backend (`cd tso_server/backend`)
```bash
uv run fastapi dev    # Dev server on :8000 with auto-reload
uv run pytest        # Run all tests
uv run pytest tests/test_filter_utils.py  # Run a single test file
uv run ruff check .  # Lint
uv run ruff format . # Format
```

### Webscraper (`cd tso_server/webscraper`)
```bash
uv run python main.py   # Run aggregation engine
uv run python -m odds_scraper.worker.generic_worker --sportsbook fliff --interval 10
uv run ruff check .
```

### Docker (from `tso_server/`)
```bash
docker compose up -d           # Start all services
docker compose up --build      # Rebuild and start
docker compose logs -f backend # Tail logs for a service
docker compose --profile mock up worker-mock redis engine  # Dev with mock data
```

## Architecture

### Data Flow
```
Workers (per sportsbook) → Redis Pub/Sub (sportsbook:*:bets)
→ Engine (main.py) detects arbs/EV → Redis keys (trueshot:arbs:premium, trueshot:ev:free, etc.)
→ Backend broadcasts via WebSocket → Frontend DataContext
```

Each worker publishes to `sportsbook:{name}:bets`. The engine (`tso_server/webscraper/main.py`) subscribes to that pattern, merges all sportsbook data, and calls `OddsEngine.process_events()`. Results are written to Redis keys and published on `:{key}:updates` channels. Workers publish with a 60s TTL — if a worker dies, its data automatically expires.

Line movement history is stored in **TimescaleDB** (`line_movements` table). The `odds:latest:{league}` Redis hash gives a fast initial snapshot; the `/api/terminal/lines/{event_id}` endpoint fetches full history from TimescaleDB.

### Tier System
Two tiers (`free` / `premium`) determined by Firebase custom claim `stripeRole`:
- **Free:** max 5 arbs/EVs, NBA/NFL/MLB only, updates delayed 60s, rate-limited 60 req/min
- **Premium:** unlimited, all leagues, real-time 5s updates, 5 req/min rate limit

Tier enforcement happens in `app/dependencies/authentication.py` (`get_user_with_tier`) and `app/filter_utils.py`. The WebSocket manager (`app/websocket_manager.py`) applies filters server-side before sending data to each client.

### WebSocket Protocol
1. Client connects to `WS /api/ws`
2. Must send `authenticate` message with Firebase token within 10s or connection drops
3. Client sends `subscribe` with stream name (`arbs`, `ev`, `terminal`) and filter params
4. Server broadcasts filtered data from Redis Pub/Sub; `arbs`/`ev` streams send initial cached data on subscribe, `terminal` does not (frontend loads initial data via REST then receives incremental `LineUpdate[]`)
5. Client can send `update_filters` to re-filter without reconnecting
6. 90s receive timeout (= 3× client ping interval)

### Backend Structure (`tso_server/backend/app/`)
- `main.py` — FastAPI app, lifespan (Redis + TimescaleDB pool init), CORS, Firebase SDK init
- `router.py` — HTTP endpoints: health, products, config, terminal odds, line history, account management, Stripe portal, bug reports
- `websocket_router.py` — `WS /api/ws` endpoint; delegates auth and message dispatch
- `websocket_manager.py` — `WebSocketManager` singleton; one `SubscriptionState` (with dedicated Redis conn + asyncio task) per stream per connection
- `filter_utils.py` — `apply_arb_filters`, `apply_ev_filters`, `apply_terminal_tier_filters`
- `dependencies/authentication.py` — Firebase token verification; `get_user_with_tier` injects tier from `stripeRole` claim
- `config.py` — `Settings` (pydantic-settings), `SPORTSBOOKS` dict, tier limits
- `redis.py` — shared async Redis client singleton
- `timescale.py` — asyncpg connection pool

### Frontend State (`tso_client/src/`)
All real-time data lives in `DataContext`. Key contexts:
- `AuthContext` — Firebase auth + tier (`stripeRole` custom claim)
- `DataContext` — WebSocket connection, arbs/EV/terminal data, all client-side filters, pinned bets
- `StripeContext` — products and subscription state
- `SettingsContext` — user preferences

API calls use `services/api.ts` (singleton). Protected endpoints auto-attach `Authorization: Bearer {firebase_id_token}`.

### Redis Key Structure
- `trueshot:arbs:premium` / `trueshot:arbs:free` — latest arb results (JSON)
- `trueshot:ev:premium` / `trueshot:ev:free` — EV bets
- `trueshot:arbs:premium:updates` / etc. — Pub/Sub channels for real-time pushes
- `odds:latest:{league}` — hash of current odds per game (fast snapshot)
- `lines:{league}:{market_type}:{event_id}:{outcome_name}` — sorted-set of historical line data (4hr TTL)
- `event:{league}:{event_id}` — event metadata (home/away teams, start time)
- `sportsbook:{name}:bets` — per-worker publish channel (60s TTL data)

## Key Constraints
- Frontend env vars (`VITE_*`) are baked in at **build time** — changing them requires a redeploy on Cloudflare Pages.
- The frontend `public/_redirects` (`/* /index.html 200`) is required for SPA routing on Cloudflare Pages — do not remove it.
- BetMGM worker uses Playwright (browser automation) and needs 512MB+ memory; other workers are lightweight.
- Docs (`/docs`, `/redoc`) are disabled in production; enabled when `ENV=development` or `DOCS_ENABLED=true`.
- Backend tests use a fake env (no real Redis/Firebase) set up in `tso_server/backend/tests/conftest.py`.
- Docker Compose lives in `tso_server/` (not the repo root). Run all `docker compose` commands from there.
- The engine depends on TimescaleDB being healthy at startup, but will log a warning (not crash) if it's unavailable.

## SEO
- Brand name is **TrueShotOdds** — used consistently in all titles, meta tags, and UI copy.
- Per-page meta tags use `react-helmet-async` with `<HelmetProvider>` wrapping `App.tsx`.
- Public pages (crawlable): `/`, `/pricing`, `/arbitrage-betting`, `/ev-betting`, `/faq`. All others are disallowed in `robots.txt`.
- FAQ data lives in `tso_client/src/data/faqs.ts` — edit there, not in the page files.
- Sitemap: `tso_client/public/sitemap.xml` — update when adding new public pages.
