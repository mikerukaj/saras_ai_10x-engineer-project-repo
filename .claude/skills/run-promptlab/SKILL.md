---
name: run-promptlab
description: Build, run, and drive the PromptLab full-stack app (FastAPI backend + React/Vite frontend). Use when asked to start PromptLab, run the backend or frontend dev servers, take a screenshot of the UI, or interact with the running app end-to-end.
---

PromptLab is a two-process app: a FastAPI backend (`backend/`) and a
React/Vite frontend (`frontend/`) that calls it over HTTP. There is no
Electron/desktop layer and no `chromium-cli` installed in this
container, so the frontend is driven with a small custom Playwright
REPL at `.claude/skills/run-promptlab/driver.mjs` — same shape as a
`chromium-cli` session (nav/click/fill/screenshot), just self-hosted.

All paths below are relative to the repo root.

## Prerequisites

Node.js and npm (already present — this was verified with Node v24,
npm 11; no separate install needed). Python 3 with the standard
`venv` module (verified with the system's `python3`, 3.12).

**Do not use the system-wide `pytest`/`pip` commands directly** — see
Gotchas. Everything below uses an explicit per-project virtualenv
instead.

## Setup

Backend — create a virtualenv and install its pinned deps (this is the
one thing you cannot skip; the container's global Python has neither
`pip` bootstrapped nor FastAPI/Pydantic installed):

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ..
```

Frontend — install deps (already vendored if `frontend/node_modules`
exists; safe to re-run):

```bash
cd frontend
npm install
cd ..
```

Driver's own dependency (Playwright — deliberately kept out of
`frontend/package.json`; this is agent tooling, not app code) and its
browser binary:

```bash
cd .claude/skills/run-promptlab
npm install
npx playwright install chromium   # ~300MB download, one-time
cd ../../..
```

## Build

No build step needed to run in dev mode (below). For a production
build of the frontend:

```bash
cd frontend && npm run build   # tsc -b && vite build -> frontend/dist/
```

## Run (agent path)

1) Start both dev servers in the background and wait for them to
   actually be serving (poll, don't `sleep`):

```bash
cd backend
nohup .venv/bin/python -m uvicorn app.api:app --host 127.0.0.1 --port 8000 > /tmp/promptlab-backend.log 2>&1 &
timeout 20 bash -c 'until curl -sf http://127.0.0.1:8000/health >/dev/null; do sleep 0.5; done'
cd ../frontend
nohup npm run dev -- --port 5173 --strictPort > /tmp/promptlab-frontend.log 2>&1 &
timeout 30 bash -c 'until curl -sf http://localhost:5173 >/dev/null; do sleep 0.5; done'
cd ..
```

The frontend's API base URL defaults to `http://localhost:8000`
(`frontend/src/api/client.ts`), matching the port above — no env var
needed unless you deliberately run the backend elsewhere (override
with `VITE_API_BASE_URL` before `npm run dev`).

Stop both with (find-by-port, not `pkill -f` — see Gotchas):

```bash
lsof -ti:8000,5173 -sTCP:LISTEN | xargs -r kill
```

2) Drive the frontend via the REPL driver, under tmux so you can send
   one command at a time and read the output back:

```bash
tmux new-session -d -s promptlab -x 200 -y 50
tmux send-keys -t promptlab 'node .claude/skills/run-promptlab/driver.mjs' Enter
timeout 15 bash -c 'until tmux capture-pane -t promptlab -p | grep -q "driver>"; do sleep 0.3; done'
tmux send-keys -t promptlab 'launch' Enter
timeout 15 bash -c 'until tmux capture-pane -t promptlab -p | grep -q "^launched"; do sleep 0.3; done'
tmux send-keys -t promptlab 'nav http://localhost:5173/' Enter
sleep 1
tmux send-keys -t promptlab 'wait-for text=Prompts' Enter
sleep 1
tmux send-keys -t promptlab 'screenshot 01-list' Enter
sleep 1
tmux capture-pane -t promptlab -p
```

Then actually open the screenshot file — `capture-pane` only proves
the driver ran, not that the page rendered correctly.

Screenshots land in `/tmp/promptlab-shots/` (override with
`SCREENSHOT_DIR`). Backend/frontend logs are at
`/tmp/promptlab-backend.log` / `/tmp/promptlab-frontend.log`.

To end the session: `tmux send-keys -t promptlab 'quit' Enter` then
`tmux kill-session -t promptlab`.

### Driver commands

| command | what it does |
|---|---|
| `launch` | launch headless Chromium, start a new page, start collecting console errors |
| `viewport <width> <height>` | resize the page's viewport (e.g. `viewport 375 667` for mobile-width checks) |
| `nav <url>` | navigate, waits for network-idle |
| `wait-for <selector>` | Playwright selector (`text=Foo`, `#id`, `button:has-text("Foo")`, plain CSS, …), 10s timeout |
| `click <selector>` | click, 10s timeout |
| `fill <selector> <text...>` | fill an input/textarea — everything after the selector is the value (spaces allowed) |
| `press <key>` | keyboard press (`Enter`, `Tab`, …) |
| `screenshot [name]` | full-page screenshot → `/tmp/promptlab-shots/<name>.png` |
| `text [selector]` | print `innerText` of a selector (default `body`) |
| `eval <js>` | `page.evaluate(js)`, prints JSON |
| `url` | print current URL |
| `console` | print collected `console.error`/`pageerror` messages as JSON — **check this before declaring success**, a page can render its shell while every fetch fails |
| `quit` | close the browser, exit the driver |

A representative session proving a real user flow (create a prompt,
land on its detail page with the placeholder highlighted and version
history populated) is in this skill's commit history / the session
that authored it — reproduce with `nav` → `wait-for text=Prompts` →
`click text=New prompt` → `wait-for #prompt-title` → `fill #prompt-title …`
→ `fill #prompt-content …` → `click button[type=submit]` →
`wait-for text=Version history` → `screenshot`.

## Run (human path)

```bash
cd backend && .venv/bin/python main.py        # http://localhost:8000, Ctrl-C to stop
cd frontend && npm run dev                     # http://localhost:5173, Ctrl-C to stop
```

Opens nothing by itself (no browser auto-launch) — same URLs as above,
just meant to be opened by a human.

## Test

```bash
cd backend && .venv/bin/python -m pytest tests/ -v
```

Frontend has no test suite yet (Vitest/Playwright-e2e are still
unimplemented — see `specs/001-complete-promptlab-app/tasks.md`
Phase 4); `npm run build` and `npm run lint` (oxlint) are the only
frontend checks that currently exist.

## Gotchas

- **Do not use the bare `pytest` / `pip` commands in this container.**
  `pytest` on `$PATH` resolves to a `python3.6` install with Pydantic
  v1 installed — this whole backend requires Pydantic v2
  (`model_dump()`, `field_validator`, etc.), so importing the app
  under it fails immediately with `ImportError: cannot import name
  'field_validator'`. Meanwhile plain `python3` is 3.12 but has no
  `pip` bootstrapped at all (`python3 -m pip` → `No module named pip`).
  The per-project venv in Setup sidesteps both — always invoke
  `.venv/bin/python` / `.venv/bin/pip` explicitly, never the bare
  commands.
- **A `waitForURL`/`wait-for` check against a loose URL pattern can
  give a false-positive "arrived" signal.** E.g. matching
  `/\/prompts\/[^/]+$/` against `/prompts/new` succeeds trivially
  (`new` satisfies `[^/]+`), so if you're already on the create form
  and wait for that pattern after clicking submit, it can resolve
  before the real navigation happens. Prefer waiting for a
  destination-specific element (`wait-for text=Version history`,
  which only exists on the detail page) over a URL regex.
  `driver.mjs` intentionally has no built-in URL-wait command for this
  reason — use `wait-for <selector>` instead.
- **Playwright module resolution.** `driver.mjs` does
  `import(process.env.PLAYWRIGHT_MODULE || 'playwright')` — Node
  resolves the bare `'playwright'` specifier starting from
  `driver.mjs`'s own directory, so it finds
  `.claude/skills/run-promptlab/node_modules/playwright` regardless of
  your shell's cwd. You only need `PLAYWRIGHT_MODULE` if you installed
  Playwright somewhere else entirely.
- **`kill %1` doesn't work for the frontend.** `npm run dev &`'s `$!`
  is the `npm` wrapper process; npm doesn't forward `SIGTERM` to the
  Vite server it spawns. Stop by port
  (`lsof -ti:5173 -sTCP:LISTEN | xargs -r kill`), not by PID or
  `pkill -f` (too broad — can match the agent's own command line).
- **Checking for mobile horizontal overflow needs real data, not just
  CSS reading.** `viewport 375 667` (or `320 568` for the narrowest
  common width) plus
  `eval ({scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth})`
  catches real overflow that reading Tailwind classes won't — e.g. a
  user-entered title/tag/collection name with no spaces at all
  defeats normal word-wrapping (`overflow-wrap: normal` doesn't break
  within a word) and pushes the whole page wider than the viewport.
  Seed a prompt/tag/collection with one long unbroken "word" via
  `curl` first (real UI typing is slow and the failure only shows up
  with pathological input) and check every page, not just the one
  you changed. When `scrollWidth > innerWidth`, find the specific
  offending element (not just confirm the page overflows) with:
  `eval (() => { const offenders = []; for (const el of document.querySelectorAll('body *')) { const r = el.getBoundingClientRect(); if (r.right > innerWidth + 1 && el.children.length === 0) offenders.push({tag: el.tagName, cls: el.className, right: Math.round(r.right)}); } return offenders; })()`
  — `document.documentElement.scrollWidth` alone only tells you *that*
  something overflows, not *what*.

## Troubleshooting

- **`curl: (7) Failed to connect` polling the backend/frontend port**:
  check `/tmp/promptlab-backend.log` / `/tmp/promptlab-frontend.log` —
  almost always a stale process already holding the port
  (`lsof -ti:8000,5173 -sTCP:LISTEN | xargs -r kill`, then relaunch)
  or the backend venv not actually having `requirements.txt` installed
  (re-run the `pip install` in Setup).
- **`Error: browserType.launch: ...`** from the driver's `launch`
  command: Chromium's browser binary isn't downloaded — re-run
  `npx playwright install chromium` from
  `.claude/skills/run-promptlab/`.
- **`EADDRINUSE`** on port 8000 or 5173: something from a previous run
  is still listening — `lsof -ti:8000,5173 -sTCP:LISTEN | xargs -r kill`
  before relaunching.
