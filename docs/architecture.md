# Architecture and execution contract

The repository's existing history and desktop entry point remain. No simulator logic is implemented in TypeScript.

| Location | Responsibility |
| --- | --- |
| `src/marieSimulator/Marie.py` | Existing Python fetch/decode/execute engine; `tick()` is its bounded nonblocking interface |
| `src/marieSimulator/assembler.py` | Shared two-pass source assembler with original line mappings |
| `src/marieSimulator/MarieReader.py` | Retained file-based interface for desktop/CLI |
| `src/marieSimulator/MarieGUI.py`, `main.py` | Retained Qt desktop application |
| `backend/marie_api/` | FastAPI session ownership, commands, resource limits, scheduling |
| `web/` | SvelteKit 2 / Svelte 5 TypeScript UI and CodeMirror editor |
| `deploy/nginx.conf` | Same-origin static UI and private API gateway |

## Why polling and static SvelteKit

FastAPI has good request validation, async scheduling, and a small reproducible dependency set. The engine itself has no third-party dependency. Qt imports are lazy, so no display or Qt installation is required for the API.

SvelteKit prerenders the UI, with browser-only editor/session initialization. Bun installs, checks, tests, and builds it. Nginx serves the result; no separate production JavaScript server is necessary. The single public origin serves the UI and `/api`; Python is private on the Compose network.

The server executes instructions in batches (up to 100 instructions or 3 ms per visitor per turn). A fair rotating scheduler wakes every 20 ms and spends at most 15 ms per cycle on execution. Requested speed is a ceiling: under load the machine can run slower. Running clients fetch a complete bounded snapshot every 200 ms after the previous request completes; idle clients poll every 1.2 seconds. Memory is 4,096 words, output is capped, and Nginx compresses JSON. Polling favors simple reconnection and ordinary HTTP infrastructure over a WebSocket lifecycle. It can add about 200 ms of display latency, but execution commands are separate requests and Pause doesn't wait for polling. At very high speeds intermediate source highlights will be skipped; Step exposes every instruction. If real-time collaboration or history is added later, revisit streaming and delta snapshots.

## Session and command contract

- `GET /api/bootstrap` establishes a random HttpOnly, SameSite=Strict owner cookie (Secure in production). Each browser visitor may own at most four execution sessions; each tab stores its execution ID in sessionStorage. IDs and owner tokens independently contain 256 bits of randomness.
- `POST /api/sessions` assembles source and creates a fresh ready machine. Optional `replace` drops only a session owned by the same cookie, and only after assembly succeeds. Errors include `kind: assembly`, `line`, and `detail`.
- `GET /api/sessions/{id}` returns registers, full memory, source listing, current/last address, inputs, outputs, status, limits, and command revision. Access requires both owner cookie and session ID. Unknown, foreign, and expired sessions return the same 404.
- `POST /api/sessions/{id}/commands` accepts `step`, `run`, `pause`, `reset`, `speed`, and `input`, with the last observed revision. A session lock serializes scheduler work and commands; stale overlapping commands return 409. Frontend commands are serialized and stale polling responses discarded. Revisions track commands, not execution ticks, so polling latency cannot prevent Pause.
- `DELETE /api/sessions/{id}` releases an owned session. Abandoned sessions are automatically removed by the scheduler.
- Reset copies the immutable assembled memory image, restores entry PC and all registers, clears I/O/errors/counters, and returns to ready. Editing source never changes an assembled image until Assemble succeeds. Failed assembly preserves the prior machine.

| State | Meaning / next action |
| --- | --- |
| ready | Freshly assembled or reset; Run or Step |
| running | Scheduled batches; Pause, Reset, or speed change |
| paused | No scheduled execution; Run or Step |
| waiting_for_input | Input has not fetched or advanced PC; supply one numeric word |
| halted | Halt completed; Reset or Assemble |
| failed | Invalid execution or resource limit; Reset or Assemble |

Input never calls Python `input()` in the API and never blocks the worker. Supplying it consumes exactly the pending Input instruction and leaves the machine paused; the visitor explicitly chooses Run or Step. Pausing a running machine is serviced between bounded batches. Output words are numeric; visitor submissions are never evaluated as Python, shell, or subprocess commands.

## Refresh, disconnect, and restart

Source saves to this browser's localStorage and survives refresh; a storage failure is visible. Theme persists as well. Refresh in the same tab reconnects to its session using sessionStorage and the cookie. Other tabs have separate execution IDs (and shared local source storage). Source isn't server-side permanent storage.

A disconnected or closed tab does not silently cancel a running program. It continues within execution limits; idle expiry eventually removes it. After 30 minutes without a successful session request, expiry deletes all execution state. A restart or deployment deletes every session because there is no database. On a missing session the UI shows an expired state, retains the local source, and offers a new session followed by Assemble. A missing cookie requires reconnect/bootstrap. No resumable execution is promised across expiry or restarts.

## Boundaries

| Resource | Initial limit |
| --- | --- |
| Source | 64 KiB UTF-8; at most 4,096 allocated words |
| HTTP mutation body | 70 KiB, measured while streaming; Nginx also limits bodies |
| Input | One word per pending Input, signed decimal −32768…32767 or HEX 0000…FFFF in UI |
| Instructions | 100,000 per assembled/reset run budget, across all resumes and steps |
| Running time | 60 seconds accumulated while scheduled running |
| Engine CPU budget | 2 seconds measured as elapsed engine batch time |
| Output | 1,024 words per reset |
| Active sessions | 100 globally; four per owner cookie |
| Session inactivity | 1,800 seconds by default |
| Gateway requests | 20 API requests/sec per peer IP; 10 assembly requests/minute with burst allowances |

These limits prevent loops from monopolizing the worker. They are not user accounts or a distributed abuse-defense system; owner cookies can be cleared. The global session ceiling, gateway request limits, and container CPU/memory limits bound initial exposure. Nginx sees the upstream proxy's peer IP in Coolify by default; per-client IP limits require configuring `real_ip` for the VPS's specific trusted proxy subnet, never trusting arbitrary forwarded headers. Without that configuration, users may share the gateway rate budget. This must be checked before public launch.

Use exactly one API process/worker and one replica. In-memory sessions cannot be shared across Uvicorn workers or independent containers. `WEB_CONCURRENCY` other than 1 fails startup, and Docker explicitly invokes `--workers 1`. Horizontal scaling requires an external state/coordination design and is intentionally out of initial scope. The public gateway does not publish the API port. No secrets, database, paid API, or AI integration is required.
