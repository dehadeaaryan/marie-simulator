# Local operation and Coolify deployment

## Local development (no Docker)

Requirements: Python 3.12, Bun 1.3.11. Use two terminals from this repository.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=src:backend .venv/bin/python -m uvicorn marie_api.app:app --host 127.0.0.1 --port 8000 --workers 1
```

```sh
cd web
bun install --frozen-lockfile
bun run dev
```

Visit `http://127.0.0.1:5175`. Vite proxies `/api` to `127.0.0.1:8000`; use the frontend origin so its owner cookie is sent correctly. Local cookies are not Secure by default. API health is `http://127.0.0.1:8000/api/health`. API docs are intentionally not exposed. Both servers bind only loopback locally.

```sh
.venv/bin/python -m pytest -q
cd web
bun run check
bun run build
bunx playwright install chromium
bun run test:ui
```

Browser tests use the running servers. Set `WEB_URL` to test another frontend origin. Build output is `web/build/`; `bun run preview` serves it on port 4173 and proxies the API. Backend requirements files pin the resolved transitive dependencies; `.in` files identify top-level dependencies. Update both deliberately and rerun tests. Bun's version and `web/bun.lock` are checked in.

## Desktop

The desktop is separate from the API dependencies:

```sh
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python main.py
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_desktop.py -q
```

Programmatic usage remains `Marie(MarieReader('trial')).run()` after setting `PYTHONPATH=src` or installing this package. Numeric terminal input is hexadecimal. Qt Run is timer-driven; Step/Reset uses the desktop's retained controls. Desktop edit/save menu placeholders are documented legacy limitations.

## Docker local review

```sh
docker compose -f compose.yaml -f compose.local.yaml up --build
```

Visit `http://127.0.0.1:8080`. The local override exposes only the gateway on loopback and disables Secure cookies for HTTP. Build contexts are repository root. The frontend build stage uses Bun 1.3.11 with a frozen lockfile; production serves static files from Nginx. The backend uses Python 3.12.12, installs only pinned headless dependencies, and runs as a non-root user with a read-only filesystem. No volume or database is needed.

## Coolify on the KVM VPS (when deployment is requested)

1. Add an application sourced from this existing GitHub repository; select **Docker Compose** and `compose.yaml` at repository root. Use its existing branch/history; no new repository is needed.
2. Configure a domain on the **web** service with the container port: `https://marie.aaryandehade.com:8080`. The `:8080` tells Coolify which internal service port to route to; visitors use the normal HTTPS domain. The API has no domain or host port.
3. Set `COOKIE_SECURE=true`, `SESSION_TTL_SECONDS=1800`, `MAX_SESSIONS=100`. There are no required secrets. Optional `.env` must stay untracked. `WEB_CONCURRENCY` is fixed at 1.
4. Point the hostname's DNS record to the VPS and let Coolify provide HTTPS. Do not publish port 8000. Keep API replicas and workers at **one**. The default stack has no host-published ports; Coolify's proxy routes the public domain to web:8080.
5. Check the health endpoints and the full browser path after rollout. API Docker health uses Python urllib against `/api/health` on 8000; gateway health uses wget through `/api/health` on 8080. `depends_on` waits for API health before starting the gateway. Both checks run every 30 seconds with 3-second timeouts and three retries.
6. Verify the proxy's trusted IP subnet before enabling per-client Nginx `real_ip` handling. As supplied, Nginx limits based on the direct peer, which may be Coolify's shared proxy address. Set trusted `set_real_ip_from` and `real_ip_header X-Forwarded-For` only for that confirmed subnet. This deployment-specific configuration cannot safely be guessed from this repo.
7. Verify cookie Secure/HttpOnly/SameSite attributes and no public API port, then exercise Input, Pause, Reset, expiry, and a loop limit. Opening the gateway health URL should show `{"status":"ok"}`. Coolify deployments restart the backend and invalidate all live sessions; saved browser source survives.

| Service | Build/start | Internal port | Published port |
| --- | --- | --- | --- |
| API | `backend/Dockerfile`; `python -m uvicorn marie_api.app:app --workers 1` | 8000 | None |
| Web/gateway | `web/Dockerfile`; Bun build, Nginx runtime | 8080 | Coolify HTTPS routing only |

The Compose stack sets CPU, memory, and process limits. Scale the VPS limits after observing memory and concurrency; do not scale API replicas with in-memory sessions. Nginx may return a gateway timeout/rate-limit HTML response; the UI treats that as disconnected and preserves source. Reset does not reassemble edited source: Assemble applies edits. No apps/portfolio repository or showcase link has been modified, and production deployment is a separate step.

Reference documentation used: [SvelteKit static adapter](https://svelte.dev/docs/kit/adapter-static), [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/), [Coolify Docker Compose](https://coolify.io/docs/knowledge-base/docker/compose), [Coolify service networking](https://coolify.io/docs/services/configuration/networking).
