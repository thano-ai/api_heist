# API Heist Academy

Interactive classroom lab for **OWASP API Top 10** — one shared path, 10 teams, 10 challenges, one scoreboard.

> **Security:** Intentionally vulnerable for education. Bind to `127.0.0.1` only. Do **not** expose this app to the public internet.

---

## Requirements

- **Python 3.10+** ([download](https://www.python.org/downloads/))
- **Git** (to clone this repo)
- A modern browser (Chrome, Edge, or Firefox)
- Optional: [Postman](https://www.postman.com/downloads/), [Burp Suite Community](https://portswigger.net/burp/communitydownload)
- Optional: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (alternative install)

---

## Step-by-step installation (local)

### 1. Clone the repository

```bash
git clone https://github.com/thano-ai/api_heist.git
cd api_heist
```

### 2. Create a virtual environment

**Windows (PowerShell or CMD):**

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
```

**macOS / Linux:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the server

```bash
python app.py
```

You should see something like:

```text
API Heist Academy — EDUCATIONAL LAB ONLY
Serving on http://127.0.0.1:5000
```

Leave this terminal open while the lab is running.

### 5. Open the game

In your browser go to:

**http://127.0.0.1:5000**

(or **http://localhost:5000**)

### 6. Run a session

1. Read the **Session rules** → **Continue to team setup**
2. Enter a **team name** → add **student names** → continue
3. On the shared path, click **Start challenge** for your assigned level
4. Use Postman / Burp against `http://127.0.0.1:5000`
5. Submit the flag in the UI
6. When the challenge is done, the timer **pauses** — next team registers
7. Use **Clear & start over** in the top bar to reset everything

### 7. Stop the server

In the terminal where Flask is running, press **Ctrl+C**.

---

## Alternative: Docker install

### 1. Clone (if you have not already)

```bash
git clone https://github.com/thano-ai/api_heist.git
cd api_heist
```

### 2. Build and run

```bash
docker compose up --build
```

### 3. Open the game

**http://127.0.0.1:5000**

The container binds to localhost only.

### 4. Stop

```bash
docker compose down
```

---

## Postman setup (students)

1. Open Postman → **Import**
2. Select `postman/API-Heist-Academy.postman_collection.json`
3. Set collection variables:
   - `baseUrl` = `http://127.0.0.1:5000/api`
   - `teamName` = your team name (same as in the UI)
4. Send the starter requests and explore — solutions are intentionally omitted

---

## Project layout

| Piece | Path |
|-------|------|
| Flask API + game logic | `backend/app.py` |
| UI | `frontend/` |
| Postman starter kit | `postman/API-Heist-Academy.postman_collection.json` |
| Student cheat sheet | `docs/STUDENT_CHEAT_SHEET.md` |
| Burp setup | `docs/BURP_SETUP.md` |

---

## How the session works

- **One shared path** for the whole class (not 10 separate games)
- **One team per challenge**
- **100-minute** session clock — runs while solving, **pauses** between challenges
- At **0:00** the game locks immediately
- **Clear & start over** resets timer, teams, scores, and progress

## Scoring

- Each challenge: **15 pts**
- Paid hint: **−5** → **10 pts** on that challenge
- Free hint: no deduction

## Reset options

- UI button: **Clear & start over** (top bar)
- API: `POST /api/game/restart` with body `{"fullReset": true}`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Install Python 3.10+ and ensure it is on PATH; try `py -3` on Windows |
| Port 5000 already in use | Stop the other process using 5000, or set `DVAPI_PORT=5001` then open that port |
| `/api/game/session` returns 404 | An old server is running — stop it and start `python app.py` again from `backend/` |
| Page looks outdated | Hard refresh: Ctrl+F5 |
| Dependencies fail to install | Upgrade pip: `python -m pip install --upgrade pip` then retry |

---

## License / classroom use

For isolated lab / lecture use only. Do not deploy publicly.
