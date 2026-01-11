# Tasks: KVM-as-a-Service UI

## Preparation
- [ ] Create `static/` directory in the project root.
- [ ] Update `requirements.txt` to include `aiofiles` (often needed for FastAPI StaticFiles, though `requests` or `httpx` might be there, standard library usually suffices, but FastAPI `StaticFiles` requires it). *Correction: `aiofiles` is only needed if we want async file serving, which FastAPI often prefers. Standard setup usually just needs `pip install aiofiles`.*
- [ ] Add `aiofiles` to `requirements.txt`.

## Frontend Implementation
- [ ] Create `static/index.html`.
  - [ ] Implement basic HTML5 boilerplate.
  - [ ] Add Pico.css CDN link.
  - [ ] Structure the layout (Header, Status, Inputs, Settings).
- [ ] Create `static/app.js`.
  - [ ] Implement `checkStatus` function to poll `/api/v1/status`.
  - [ ] Implement `switchPort` function.
  - [ ] Implement `toggleBuzzer` function.
  - [ ] Bind event listeners to UI elements.
- [ ] Create `static/style.css` (optional) for minor tweaks.

## Backend Integration
- [ ] Edit `src/main.py`.
  - [ ] Import `StaticFiles` from `fastapi.staticfiles`.
  - [ ] Mount the `static/` directory to `/` (or `/ui` if preferred, but root is simpler for standalone feel).
  - [ ] Ensure API routes take precedence or are strictly namespaced (they are already under `/api/v1`).

## Verification
- [ ] Start the server.
- [ ] Open browser to `http://localhost:8000`.
- [ ] Verify UI loads.
- [ ] Verify Status indicators update.
- [ ] Verify clicking "Port X" sends the correct API request (check Network tab or server logs).
- [ ] Verify Buzzer toggle works.
