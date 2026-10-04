# Local verification — 2026-10-04

## Completed

- **68 Python tests passed**, including the Qt desktop smoke test. Coverage includes instruction encodings, word wrapping, signed Skipcond, addressing, indirect operations, subroutines, input yielding, assembly diagnostics, invalid execution, reset, concurrent commands, isolation, expiry/restart, and resource limits.
- Original `trial` executes successfully through the retained file/engine interface; it updates X to 1 without changing the reader's initial memory image.
- `bun run check`: **zero errors and zero warnings**.
- `bun run build`: successful SvelteKit prerender/static production build.
- `bun install --frozen-lockfile --offline`: passed against the checked-in Bun lockfile.
- `pip check`: no broken Python dependencies.
- Both Compose YAML files parsed successfully. Python and Nginx base image tags were verified to exist in the upstream Docker registry.
- `git diff --check`: clean.
- Local API and development/production frontend servers were launched. All changed files are in the MARIE repository; no production deployment was performed.

- **12 browser tests passed against the final production build**, across desktop Chromium and an emulated iPhone viewport. They cover assembly, Step/Run/Reset, memory selection, input pauses, examples, source/session persistence, disconnect/reconnect, expired running sessions, mobile navigation, and visible execution controls.
- Automated WCAG A/AA checks passed for the workspace in both themes and the dark instruction guide. Light-theme orange text was darkened where needed for contrast while the bright shared orange remains on button backgrounds and in dark mode.
- Final desktop/mobile screenshots were inspected. The header contains the existing AD logo and only `marie.`; the UI uses the apps collection's Figtree, pill header, warm surfaces, and default dark palette.

## Local review URLs

- Production frontend: **http://127.0.0.1:4173**
- Development frontend: **http://127.0.0.1:5175**
- API health: **http://127.0.0.1:8000/api/health**

Port 5173 was already occupied, so it was left alone. The UI now uses the source of `../apps.aaryandehade.com` as its primary visual reference. That repo was only read; its existing logo/favicon/font were copied into this repository. No portfolio or other app files were edited.

## Remaining limits and launch checks

- Docker is not installed in this local environment. Actual container builds, Nginx configuration validation inside its image, and Coolify/VPS integration remain unverified. Run the documented Compose local review before public deployment.
- The deployment must keep one API worker and replica. Sessions disappear on restart and expire after inactivity; local source survives. In-memory state is intentionally not horizontally shared.
- Configure trusted proxy IP handling on the actual VPS before relying on per-client IP gateway limits. As supplied, requests through Coolify may share one proxy-IP rate budget.
- Python tests emit one upstream Starlette TestClient deprecation warning about httpx. It does not affect production requests or test outcomes.
- Browser verification uses Chromium and an emulated iPhone viewport; real-device Safari/Firefox and a manual screen-reader audit were not performed.
- The desktop's original Edit/Save menu placeholders remain. No package distribution was rebuilt or published.
- Breakpoints, sharing, import/export, guided lessons, and history remain future work, as requested.
