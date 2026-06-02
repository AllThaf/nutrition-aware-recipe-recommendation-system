# Frontend Structure

The frontend is a static dashboard implemented with HTML/CSS/vanilla JavaScript.

## Frontend layout

- `frontend/index.html`
  - Landing/home page.

- `frontend/dashboard.html`
  - Main UI.
  - Contains multiple logical sections (tabs) such as:
    - statistics/dashboard overview
    - recommendations UI
    - evaluation metrics UI
    - recipe browsing UI

- `frontend/static/styles.css`
  - Responsive styling.

- `frontend/static/dashboard.js`
  - Client-side logic:
    - Fetches data from backend endpoints.
    - Renders results and charts (Chart.js, if included in the HTML).
    - Handles user inputs and error display.

## Backend integration

The frontend calls API endpoints under `/api`.
Because the FastAPI app mounts static files and serves pages from the same server, you typically use relative paths such as:
- `/api/recipes`
- `/api/recommendations`
- `/api/evaluation/metrics`

## Authentication note (header-based)

The UI may set `X-Username` for `/api/me*` endpoints, depending on how `dashboard.js` is implemented.
This repository does not implement JWT/session-based auth.

> Documentation limitation: this file set was not opened during this cleanup pass; authentication header usage in the UI should be verified if needed.

