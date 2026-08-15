"""
API Heist Academy — Intentionally vulnerable educational lab.
OWASP API Top 10 training for classroom use only.
Bind to 127.0.0.1. Do NOT expose to the public internet.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import jwt
from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DVAPI_DB", BASE_DIR / "heist.db"))
STATIC_DIR = BASE_DIR.parent / "frontend"
SECRET = os.environ.get("DVAPI_SECRET", "super-secret-key-change-me")
HOST = os.environ.get("DVAPI_HOST", "127.0.0.1")
PORT = int(os.environ.get("DVAPI_PORT", "5000"))

FLAGS = {
    1: "FLAG{B0L4_G0t_M3_2024}",
    2: "FLAG{4uth_1s_H4rd_Right}",
    3: "FLAG{M4ss_4ss1gn_OhNo}",
    4: "FLAG{R4t3_L1m1t_Byp4ss}",
    5: "FLAG{Adm1n_Funct10n_Oops}",
    6: "FLAG{Fl0w_Abus3_Pr0f1t}",
    7: "FLAG{SSRF_1nt3rn4l_M3t4}",
    8: "FLAG{Debu9_M0d3_Dang3r}",
    9: "FLAG{V3rs10n_Exp0s3d}",
    10: "FLAG{Webh00k_Inj3ct10n}",
    11: "FLAG{Ult1m4te_H31st_C0mpl3te}",
}

CHALLENGES = {
    1: {
        "slug": "bola",
        "title": "Broken Object Level Authorization (BOLA)",
        "codename": "The Locker Room",
        "icon": "",
        "points": 15,
        "endpoint": "GET /api/user/{id}",
        "description": (
            "The API allows users to view their profile at /api/user/{id}. "
            "But can you access someone else's?"
        ),
        "objective": "Find the hidden flag by exploiting the ID parameter.",
        "hints": [
            "Object references in URLs are often trusted more than they should be.",
            "Compare several responses. One profile may differ from the others.",
        ],
    },
    2: {
        "slug": "broken-auth",
        "title": "Broken Authentication",
        "codename": "The Guard Post",
        "icon": "",
        "points": 15,
        "endpoint": "GET /api/admin",
        "description": (
            "The /api/admin endpoint expects a token. "
            "Authentication looks solid — until you look closer."
        ),
        "objective": "Reach the admin area and capture the flag.",
        "hints": [
            "Tokens are data. What happens if you inspect or reshape that data?",
            "Servers sometimes check the claim they care about more carefully than how the token was made.",
        ],
    },
    3: {
        "slug": "mass-assignment",
        "title": "Mass Assignment",
        "codename": "Property Tycoon",
        "icon": "",
        "points": 15,
        "endpoint": "PUT /api/user/update",
        "description": (
            "Users can update their profile through a JSON body. "
            "Ask what the server is willing to accept."
        ),
        "objective": "Escalate privileges through the update flow.",
        "hints": [
            "Update endpoints sometimes honor fields you never see in the UI.",
            "Think about properties that change who you are — not just your name or email.",
        ],
    },
    4: {
        "slug": "resource-consumption",
        "title": "Unrestricted Resource Consumption",
        "codename": "Flood Gate",
        "icon": "",
        "points": 15,
        "endpoint": "GET /api/rate-limited",
        "description": (
            "This endpoint advertises a request limit. "
            "Limits on paper and limits in practice are not always the same."
        ),
        "objective": "Pressure the endpoint until something unexpected appears.",
        "hints": [
            "Watch how the response changes as traffic increases.",
            "Soft limits and hard limits behave differently when you keep going.",
        ],
    },
    5: {
        "slug": "bfla",
        "title": "Broken Function Level Authorization",
        "codename": "The Back Door",
        "icon": "",
        "points": 15,
        "endpoint": "DELETE /api/admin/users",
        "description": (
            "Some routes are meant for administrators only. "
            "Function-level checks are easy to forget."
        ),
        "objective": "Reach a privileged function that should have blocked you.",
        "hints": [
            "Naming and HTTP methods can hint at who a route was built for.",
            "Absence of an error is sometimes the vulnerability.",
        ],
    },
    6: {
        "slug": "business-flow",
        "title": "Unrestricted Access to Sensitive Business Flows",
        "codename": "Money Printer",
        "icon": "",
        "points": 15,
        "endpoint": "POST /api/transfer",
        "description": (
            "A single transfer looks harmless. "
            "Business rules often fail when the happy path is repeated."
        ),
        "objective": "Abuse a legitimate flow until the system gives something up.",
        "hints": [
            "One request is allowed. What about many?",
            "Automation turns a tiny action into a large effect.",
        ],
    },
    7: {
        "slug": "ssrf",
        "title": "Server Side Request Forgery (SSRF)",
        "codename": "The Messenger",
        "icon": "",
        "points": 15,
        "endpoint": "POST /api/fetch-url",
        "description": (
            "This service will fetch a URL on your behalf. "
            "Where it is willing to reach matters more than what you see in the browser."
        ),
        "objective": "Make the server talk to a place clients should not reach directly.",
        "hints": [
            "The interesting destinations are often not on the public internet.",
            "Cloud environments and loopback addresses are classic places to probe carefully.",
        ],
    },
    8: {
        "slug": "misconfig",
        "title": "Security Misconfiguration",
        "codename": "Debug Dump",
        "icon": "",
        "points": 15,
        "endpoint": "GET /api/debug",
        "description": (
            "A diagnostics route is exposed. "
            "Verbose failure modes can say more than success responses."
        ),
        "objective": "Coax the service into revealing more than it should.",
        "hints": [
            "Healthy endpoints sometimes still accept unusual query options.",
            "Error pages and stack traces are part of the attack surface.",
        ],
    },
    9: {
        "slug": "inventory",
        "title": "Improper Inventory Management",
        "codename": "Shadow API",
        "icon": "",
        "points": 15,
        "endpoint": "GET /api/v2/users",
        "description": (
            "Documentation points at the current users API. "
            "Older surfaces are not always retired cleanly."
        ),
        "objective": "Find an overlooked API surface that still answers.",
        "hints": [
            "Version numbers in paths often leave breadcrumbs.",
            "What shipped before the current version may still be listening.",
        ],
    },
    10: {
        "slug": "unsafe-consumption",
        "title": "Unsafe Consumption of APIs",
        "codename": "Webhook Trap",
        "icon": "",
        "points": 15,
        "endpoint": "POST /api/webhook",
        "description": (
            "Inbound webhook events are accepted as JSON. "
            "Consumers of external data need skepticism."
        ),
        "objective": "Craft input the webhook handler handles unsafely.",
        "hints": [
            "Treat every field as untrusted — including ones that look like control signals.",
            "Special names and template-like strings are worth experimenting with.",
        ],
    },
}

DEMO_USERS = [
    {"id": 1, "name": "Alice", "email": "alice@heist.local", "role": "user", "balance": 100},
    {"id": 2, "name": "Bob", "email": "bob@heist.local", "role": "user", "balance": 250},
    {
        "id": 3,
        "name": "Carol",
        "email": "carol@heist.local",
        "role": "user",
        "balance": 999,
        "secret_note": FLAGS[1],
    },
    {"id": 4, "name": "Dave", "email": "dave@heist.local", "role": "user", "balance": 40},
]

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
CORS(app)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            hints_used INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            total_time_seconds INTEGER NOT NULL DEFAULT 0,
            members TEXT NOT NULL DEFAULT '[]',
            assigned_challenge INTEGER
        );
        CREATE TABLE IF NOT EXISTS challenge_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            solved INTEGER NOT NULL DEFAULT 0,
            hints_used INTEGER NOT NULL DEFAULT 0,
            requests INTEGER NOT NULL DEFAULT 0,
            time_seconds INTEGER,
            solved_at TEXT,
            points_earned INTEGER NOT NULL DEFAULT 0,
            UNIQUE(team_id, challenge_id),
            FOREIGN KEY(team_id) REFERENCES teams(id)
        );
        CREATE TABLE IF NOT EXISTS session_challenges (
            challenge_id INTEGER PRIMARY KEY,
            solved INTEGER NOT NULL DEFAULT 0,
            solved_by TEXT,
            points_earned INTEGER NOT NULL DEFAULT 0,
            time_seconds INTEGER
        );
        CREATE TABLE IF NOT EXISTS game_session (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            remaining_seconds INTEGER NOT NULL DEFAULT 6000,
            running INTEGER NOT NULL DEFAULT 0,
            ended INTEGER NOT NULL DEFAULT 0,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rate_counters (
            team_key TEXT PRIMARY KEY,
            count INTEGER NOT NULL DEFAULT 0,
            window_start REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transfer_counters (
            team_key TEXT PRIMARY KEY,
            count INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS users_demo (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            role TEXT,
            balance INTEGER,
            extra TEXT
        );
        """
    )
    # Lightweight migrations for older DBs
    cols = {r[1] for r in db.execute("PRAGMA table_info(teams)").fetchall()}
    if "members" not in cols:
        db.execute("ALTER TABLE teams ADD COLUMN members TEXT NOT NULL DEFAULT '[]'")
    if "assigned_challenge" not in cols:
        db.execute("ALTER TABLE teams ADD COLUMN assigned_challenge INTEGER")

    if db.execute("SELECT COUNT(*) FROM game_session").fetchone()[0] == 0:
        db.execute(
            "INSERT INTO game_session (id, remaining_seconds, running, ended, updated_at) VALUES (1, 6000, 0, 0, ?)",
            (time.time(),),
        )
    if db.execute("SELECT COUNT(*) FROM session_challenges").fetchone()[0] == 0:
        for cid in range(1, 12):
            db.execute(
                "INSERT INTO session_challenges (challenge_id, solved) VALUES (?, 0)",
                (cid,),
            )
    existing = db.execute("SELECT COUNT(*) FROM users_demo").fetchone()[0]
    if existing == 0:
        for u in DEMO_USERS:
            extra = {k: v for k, v in u.items() if k not in ("id", "name", "email", "role", "balance")}
            db.execute(
                "INSERT INTO users_demo (id, name, email, role, balance, extra) VALUES (?,?,?,?,?,?)",
                (u["id"], u["name"], u["email"], u["role"], u["balance"], json.dumps(extra)),
            )
    db.commit()
    db.close()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


SESSION_DURATION = 100 * 60  # 100 minutes


def ensure_session(db: sqlite3.Connection) -> sqlite3.Row:
    row = db.execute("SELECT * FROM game_session WHERE id = 1").fetchone()
    if not row:
        db.execute(
            "INSERT INTO game_session (id, remaining_seconds, running, ended, updated_at) VALUES (1, ?, 0, 0, ?)",
            (SESSION_DURATION, time.time()),
        )
        db.commit()
        row = db.execute("SELECT * FROM game_session WHERE id = 1").fetchone()
    return row


def read_session(db: sqlite3.Connection) -> dict[str, Any]:
    row = ensure_session(db)
    remaining = int(row["remaining_seconds"])
    running = bool(row["running"])
    ended = bool(row["ended"])
    now = time.time()

    if running and not ended:
        elapsed = now - float(row["updated_at"])
        remaining = max(0, int(remaining - elapsed))
        if remaining <= 0:
            remaining = 0
            ended = True
            running = False
            db.execute(
                "UPDATE game_session SET remaining_seconds = 0, running = 0, ended = 1, updated_at = ? WHERE id = 1",
                (now,),
            )
            db.commit()

    solved_rows = db.execute(
        "SELECT * FROM session_challenges ORDER BY challenge_id"
    ).fetchall()
    challenges = {
        r["challenge_id"]: {
            "solved": bool(r["solved"]),
            "solvedBy": r["solved_by"],
            "pointsEarned": r["points_earned"],
            "time": r["time_seconds"],
        }
        for r in solved_rows
    }
    next_challenge = 1
    for cid in range(1, 11):
        if not challenges.get(cid, {}).get("solved"):
            next_challenge = cid
            break
    else:
        next_challenge = 11 if not challenges.get(11, {}).get("solved") else None

    return {
        "remainingSeconds": remaining,
        "running": running,
        "ended": ended,
        "durationSeconds": SESSION_DURATION,
        "nextChallenge": next_challenge,
        "challenges": challenges,
    }


def persist_remaining(db: sqlite3.Connection, remaining: int, running: bool, ended: bool) -> None:
    db.execute(
        """
        UPDATE game_session
        SET remaining_seconds = ?, running = ?, ended = ?, updated_at = ?
        WHERE id = 1
        """,
        (remaining, 1 if running else 0, 1 if ended else 0, time.time()),
    )
    db.commit()


def require_session_active(db: sqlite3.Connection) -> tuple[dict[str, Any] | None, Any]:
    session = read_session(db)
    if session["ended"] or session["remainingSeconds"] <= 0:
        persist_remaining(db, 0, False, True)
        return None, (jsonify({"error": "Session time is over. The game has stopped.", "session": session}), 403)
    return session, None


def team_key_from_request() -> str:
    return (
        request.headers.get("X-Team-Name")
        or request.args.get("team")
        or (request.json or {}).get("team")
        or request.remote_addr
        or "anonymous"
    )


def ok(message: str, flag: str | None = None, **extra: Any):
    payload = {
        "success": bool(flag),
        "message": message,
        "flag": flag,
        "hint_used": False,
    }
    if flag:
        payload["points_earned"] = extra.pop("points_earned", 15)
    payload.update(extra)
    return jsonify(payload)


def fail(message: str = "Try harder!", **extra: Any):
    payload = {
        "success": False,
        "message": message,
        "flag": None,
        "hint_used": False,
    }
    payload.update(extra)
    return jsonify(payload)


def track_request(challenge_id: int) -> None:
    name = request.headers.get("X-Team-Name")
    if not name:
        return
    db = get_db()
    team = db.execute("SELECT id FROM teams WHERE name = ?", (name,)).fetchone()
    if not team:
        return
    db.execute(
        """
        INSERT INTO challenge_progress (team_id, challenge_id, requests)
        VALUES (?, ?, 1)
        ON CONFLICT(team_id, challenge_id) DO UPDATE SET requests = requests + 1
        """,
        (team["id"], challenge_id),
    )
    db.commit()


# ---------------------------------------------------------------------------
# Game management API
# ---------------------------------------------------------------------------


@app.get("/api/challenges")
def list_challenges():
    items = []
    for cid, meta in CHALLENGES.items():
        items.append(
            {
                "id": cid,
                "title": meta["title"],
                "codename": meta["codename"],
                "icon": meta["icon"],
                "points": meta["points"],
                "endpoint": meta["endpoint"],
                "description": meta["description"],
                "objective": meta["objective"],
                "free_hint": meta["hints"][0],
            }
        )
    return jsonify({"challenges": items, "final_boss": True})


@app.post("/api/game/register")
def register_team():
    data = request.get_json(silent=True) or {}
    name = (data.get("teamName") or data.get("name") or "").strip()
    members = data.get("members") or []
    if not name:
        return jsonify({"error": "Team name required"}), 400
    if len(name) > 40:
        return jsonify({"error": "Team name too long"}), 400
    if not isinstance(members, list):
        return jsonify({"error": "members must be a list"}), 400
    clean_members = [str(m).strip() for m in members if str(m).strip()]
    if not clean_members:
        return jsonify({"error": "Add at least one student name"}), 400

    db = get_db()
    session, err = require_session_active(db)
    if err:
        return err

    assigned = session["nextChallenge"]
    if assigned is None:
        return jsonify({"error": "All challenges are already complete"}), 400
    if assigned == 11:
        # Final boss — allow a team to register for it
        pass

    existing = db.execute("SELECT * FROM teams WHERE name = ?", (name,)).fetchone()
    if existing:
        db.execute(
            "UPDATE teams SET members = ?, assigned_challenge = ? WHERE id = ?",
            (json.dumps(clean_members), existing["assigned_challenge"] or assigned, existing["id"]),
        )
        db.commit()
        team = db.execute("SELECT * FROM teams WHERE id = ?", (existing["id"],)).fetchone()
        return jsonify(
            {
                "team": {**dict(team), "members": clean_members},
                "assignedChallenge": team["assigned_challenge"] or assigned,
                "resumed": True,
                "session": read_session(db),
                "message": f"Welcome back, Team {name}!",
            }
        )

    cur = db.execute(
        """
        INSERT INTO teams (name, points, hints_used, created_at, members, assigned_challenge)
        VALUES (?, 0, 0, ?, ?, ?)
        """,
        (name, utc_now(), json.dumps(clean_members), assigned),
    )
    team_id = cur.lastrowid
    for cid in CHALLENGES:
        db.execute(
            "INSERT INTO challenge_progress (team_id, challenge_id) VALUES (?, ?)",
            (team_id, cid),
        )
    db.commit()
    team = db.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
    return jsonify(
        {
            "team": {**dict(team), "members": clean_members},
            "assignedChallenge": assigned,
            "resumed": False,
            "session": read_session(db),
            "message": f"Team {name} registered for challenge {assigned}!",
        }
    )


@app.get("/api/game/session")
def get_session():
    db = get_db()
    return jsonify(read_session(db))


@app.post("/api/game/claim")
def claim_challenge():
    """Assign the next open path challenge to a team (fixes null assignments)."""
    data = request.get_json(silent=True) or {}
    name = (data.get("teamName") or "").strip()
    if not name:
        return jsonify({"error": "teamName required"}), 400

    db = get_db()
    session, err = require_session_active(db)
    if err:
        return err

    team = db.execute("SELECT * FROM teams WHERE name = ?", (name,)).fetchone()
    if not team:
        return jsonify({"error": "Team not found"}), 404

    assigned = team["assigned_challenge"]
    shared = session["challenges"].get(int(assigned), {}) if assigned else {}
    if assigned and not shared.get("solved"):
        return jsonify(
            {
                "assignedChallenge": int(assigned),
                "session": session,
                "team": {**dict(team), "members": json.loads(team["members"] or "[]")},
            }
        )

    nxt = session["nextChallenge"]
    if nxt is None:
        return jsonify({"error": "No open challenge left to claim"}), 400

    db.execute(
        "UPDATE teams SET assigned_challenge = ? WHERE id = ?",
        (nxt, team["id"]),
    )
    db.commit()
    team = db.execute("SELECT * FROM teams WHERE id = ?", (team["id"],)).fetchone()
    return jsonify(
        {
            "assignedChallenge": nxt,
            "session": read_session(db),
            "team": {**dict(team), "members": json.loads(team["members"] or "[]")},
            "message": f"Assigned challenge {nxt}",
        }
    )


@app.post("/api/game/session/resume")
def resume_session():
    db = get_db()
    session = read_session(db)
    if session["ended"] or session["remainingSeconds"] <= 0:
        persist_remaining(db, 0, False, True)
        return jsonify({"error": "Session time is over", "session": read_session(db)}), 403
    persist_remaining(db, session["remainingSeconds"], True, False)
    return jsonify(read_session(db))


@app.post("/api/game/session/pause")
def pause_session():
    db = get_db()
    session = read_session(db)
    if session["ended"]:
        return jsonify(session)
    persist_remaining(db, session["remainingSeconds"], False, False)
    return jsonify(read_session(db))


@app.get("/api/game/state/<team_name>")
def game_state(team_name: str):
    db = get_db()
    team = db.execute("SELECT * FROM teams WHERE name = ?", (team_name,)).fetchone()
    if not team:
        return jsonify({"error": "Team not found"}), 404
    rows = db.execute(
        "SELECT * FROM challenge_progress WHERE team_id = ? ORDER BY challenge_id",
        (team["id"],),
    ).fetchall()
    challenges = {}
    for row in rows:
        challenges[row["challenge_id"]] = {
            "solved": bool(row["solved"]),
            "hintsUsed": row["hints_used"],
            "time": row["time_seconds"],
            "requests": row["requests"],
            "pointsEarned": row["points_earned"],
            "solvedAt": row["solved_at"],
        }
    members = json.loads(team["members"] or "[]")
    return jsonify(
        {
            "team": {**dict(team), "members": members},
            "challenges": challenges,
            "session": read_session(db),
        }
    )


@app.post("/api/game/hint")
def reveal_hint():
    data = request.get_json(silent=True) or {}
    name = (data.get("teamName") or "").strip()
    challenge_id = int(data.get("challengeId") or 0)
    hint_index = int(data.get("hintIndex") or 1)  # 0 = free, 1 = paid

    if challenge_id not in CHALLENGES:
        return jsonify({"error": "Invalid challenge"}), 400
    if hint_index not in (0, 1):
        return jsonify({"error": "Invalid hint index"}), 400

    db = get_db()
    _, err = require_session_active(db)
    if err:
        return err

    team = db.execute("SELECT * FROM teams WHERE name = ?", (name,)).fetchone()
    if not team:
        return jsonify({"error": "Team not found"}), 404

    progress = db.execute(
        "SELECT * FROM challenge_progress WHERE team_id = ? AND challenge_id = ?",
        (team["id"], challenge_id),
    ).fetchone()

    hint_text = CHALLENGES[challenge_id]["hints"][hint_index]
    deducted = 0

    if hint_index == 1 and progress and progress["hints_used"] < 1:
        db.execute(
            "UPDATE challenge_progress SET hints_used = hints_used + 1 WHERE id = ?",
            (progress["id"],),
        )
        db.execute(
            "UPDATE teams SET hints_used = hints_used + 1 WHERE id = ?",
            (team["id"],),
        )
        deducted = 5
        db.commit()

    return jsonify(
        {
            "hint": hint_text,
            "hintIndex": hint_index,
            "pointsDeducted": deducted,
            "hint_used": hint_index == 1,
        }
    )


@app.post("/api/game/submit-flag")
def submit_flag():
    data = request.get_json(silent=True) or {}
    name = (data.get("teamName") or "").strip()
    challenge_id = int(data.get("challengeId") or 0)
    flag = (data.get("flag") or "").strip()
    elapsed = data.get("timeSeconds")

    if challenge_id not in FLAGS:
        return jsonify({"error": "Invalid challenge"}), 400

    expected = FLAGS.get(challenge_id)
    if flag != expected:
        return jsonify({"success": False, "message": "Incorrect flag. Try harder!", "flag": None})

    db = get_db()
    session, err = require_session_active(db)
    if err:
        return err

    team = db.execute("SELECT * FROM teams WHERE name = ?", (name,)).fetchone()
    if not team:
        return jsonify({"error": "Team not found"}), 404

    assigned = team["assigned_challenge"]
    if assigned and int(assigned) != challenge_id and challenge_id != 11:
        return jsonify({"error": f"This team is assigned to challenge {assigned} only"}), 403

    # Shared path: already solved by another team?
    shared = db.execute(
        "SELECT * FROM session_challenges WHERE challenge_id = ?", (challenge_id,)
    ).fetchone()
    if shared and shared["solved"]:
        return jsonify(
            {
                "success": True,
                "message": "Already solved for this session.",
                "flag": expected,
                "points_earned": 0,
                "session": read_session(db),
            }
        )

    if challenge_id == 11:
        db.execute(
            """
            INSERT INTO challenge_progress (team_id, challenge_id, solved, solved_at, points_earned, time_seconds)
            VALUES (?,?,1,?,?,?)
            ON CONFLICT(team_id, challenge_id) DO UPDATE SET
              solved = 1, solved_at = excluded.solved_at, points_earned = excluded.points_earned
            """,
            (team["id"], 11, utc_now(), 15, elapsed),
        )
        db.execute(
            """
            UPDATE session_challenges
            SET solved = 1, solved_by = ?, points_earned = 15, time_seconds = ?
            WHERE challenge_id = 11
            """,
            (name, elapsed),
        )
        db.execute("UPDATE teams SET points = points + 15 WHERE id = ?", (team["id"],))
        session = read_session(db)
        persist_remaining(db, session["remainingSeconds"], False, False)
        return jsonify(
            {
                "success": True,
                "message": "Final Boss defeated!",
                "flag": expected,
                "points_earned": 15,
                "session": read_session(db),
                "paused": True,
            }
        )

    progress = db.execute(
        "SELECT * FROM challenge_progress WHERE team_id = ? AND challenge_id = ?",
        (team["id"], challenge_id),
    ).fetchone()
    if not progress:
        return jsonify({"error": "Progress missing"}), 400

    # 15 pts per challenge; paid hint costs 5 → 10 pts
    earned = 10 if progress["hints_used"] >= 1 else 15
    db.execute(
        """
        UPDATE challenge_progress
        SET solved = 1, solved_at = ?, points_earned = ?, time_seconds = ?
        WHERE id = ?
        """,
        (utc_now(), earned, elapsed, progress["id"]),
    )
    db.execute(
        "UPDATE teams SET points = points + ?, total_time_seconds = total_time_seconds + ? WHERE id = ?",
        (earned, int(elapsed or 0), team["id"]),
    )
    db.execute(
        """
        UPDATE session_challenges
        SET solved = 1, solved_by = ?, points_earned = ?, time_seconds = ?
        WHERE challenge_id = ?
        """,
        (name, earned, elapsed, challenge_id),
    )
    db.commit()

    # Pause session timer between challenges
    session = read_session(db)
    persist_remaining(db, session["remainingSeconds"], False, False)

    return jsonify(
        {
            "success": True,
            "message": "Challenge complete! Timer paused — next team can register.",
            "flag": expected,
            "points_earned": earned,
            "session": read_session(db),
            "paused": True,
        }
    )


@app.get("/api/game/leaderboard")
def leaderboard():
    db = get_db()
    teams = db.execute(
        "SELECT * FROM teams ORDER BY points DESC, total_time_seconds ASC, created_at ASC"
    ).fetchall()
    solved_total = db.execute(
        "SELECT COUNT(*) FROM session_challenges WHERE solved = 1 AND challenge_id BETWEEN 1 AND 10"
    ).fetchone()[0]
    fastest = db.execute(
        """
        SELECT solved_by AS name, time_seconds AS best
        FROM session_challenges
        WHERE solved = 1 AND time_seconds IS NOT NULL AND challenge_id BETWEEN 1 AND 10
        ORDER BY time_seconds ASC
        LIMIT 1
        """
    ).fetchone()
    most_hints = db.execute(
        "SELECT name, hints_used FROM teams ORDER BY hints_used DESC LIMIT 1"
    ).fetchone()

    team_list = []
    for t in teams:
        item = dict(t)
        item["members"] = json.loads(t["members"] or "[]")
        team_list.append(item)

    return jsonify(
        {
            "teams": team_list,
            "session": read_session(db),
            "stats": {
                "challengesSolved": solved_total,
                "challengesTotal": 10,
                "fastestSolve": (
                    {"team": fastest["name"], "seconds": fastest["best"]} if fastest else None
                ),
                "mostHints": (
                    {"team": most_hints["name"], "hints": most_hints["hints_used"]}
                    if most_hints and most_hints["hints_used"]
                    else None
                ),
            },
        }
    )


@app.post("/api/game/restart")
def restart_game():
    data = request.get_json(silent=True) or {}
    full = bool(data.get("fullReset"))
    db = get_db()
    if full:
        db.execute("DELETE FROM challenge_progress")
        db.execute("DELETE FROM teams")
        db.execute("DELETE FROM rate_counters")
        db.execute("DELETE FROM transfer_counters")
        db.execute("DELETE FROM session_challenges")
        for cid in range(1, 12):
            db.execute(
                "INSERT INTO session_challenges (challenge_id, solved) VALUES (?, 0)",
                (cid,),
            )
        db.execute(
            "UPDATE game_session SET remaining_seconds = ?, running = 0, ended = 0, updated_at = ? WHERE id = 1",
            (SESSION_DURATION, time.time()),
        )
        db.commit()
        return jsonify({"message": "Full game reset complete.", "session": read_session(db)})

    name = (data.get("teamName") or "").strip()
    if not name:
        return jsonify({"error": "teamName or fullReset required"}), 400
    team = db.execute("SELECT * FROM teams WHERE name = ?", (name,)).fetchone()
    if not team:
        return jsonify({"error": "Team not found"}), 404
    db.execute("DELETE FROM challenge_progress WHERE team_id = ?", (team["id"],))
    db.execute("DELETE FROM teams WHERE id = ?", (team["id"],))
    db.execute("DELETE FROM rate_counters WHERE team_key = ?", (name,))
    db.execute("DELETE FROM transfer_counters WHERE team_key = ?", (name,))
    db.commit()
    return jsonify({"message": f"Team {name} reset."})


# ---------------------------------------------------------------------------
# Challenge 1 — BOLA
# ---------------------------------------------------------------------------


@app.get("/api/user/<int:user_id>")
def get_user(user_id: int):
    track_request(1)
    db = get_db()
    row = db.execute("SELECT * FROM users_demo WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return fail("User not found", status=404), 404
    user = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "balance": row["balance"],
    }
    extra = json.loads(row["extra"] or "{}")
    user.update(extra)
    if user_id == 3 and "secret_note" in user:
        return ok(
            "Challenge complete! You accessed another user's object.",
            flag=FLAGS[1],
            points_earned=15,
            user=user,
        )
    return fail("Profile loaded. Nothing special here.", user=user)


# ---------------------------------------------------------------------------
# Challenge 2 — Broken Authentication
# ---------------------------------------------------------------------------


@app.get("/api/admin")
def admin_panel():
    track_request(2)
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if not token:
        sample = jwt.encode({"sub": "guest", "role": "user"}, SECRET, algorithm="HS256")
        return fail(
            "Admin area requires Authorization: Bearer <jwt>",
            sample_token=sample,
            tip="Decode the JWT and inspect claims.",
        )

    # Intentionally weak: accept tokens with role=admin even if signature is wrong
    try:
        claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        try:
            claims = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        except Exception:
            return fail("Malformed token.")

    if str(claims.get("role", "")).lower() == "admin":
        return ok(
            "Challenge complete! Broken auth let you in.",
            flag=FLAGS[2],
            points_earned=15,
            claims=claims,
        )
    return fail("Authenticated, but not an admin.", claims=claims)


# ---------------------------------------------------------------------------
# Challenge 3 — Mass Assignment
# ---------------------------------------------------------------------------


@app.put("/api/user/update")
def update_user():
    track_request(3)
    data = request.get_json(silent=True) or {}
    # Intentionally vulnerable: merges entire body
    user = {
        "id": 1,
        "name": data.get("name", "Alice"),
        "email": data.get("email", "alice@heist.local"),
        "role": "user",
        "balance": 100,
    }
    user.update(data)
    if str(user.get("role", "")).lower() == "admin":
        return ok(
            "Challenge complete! Mass assignment elevated your role.",
            flag=FLAGS[3],
            points_earned=15,
            user=user,
        )
    return fail("Profile updated.", user=user)


# ---------------------------------------------------------------------------
# Challenge 4 — Resource Consumption / Rate Limit
# ---------------------------------------------------------------------------


@app.get("/api/rate-limited")
def rate_limited():
    track_request(4)
    key = team_key_from_request()
    db = get_db()
    now = time.time()
    row = db.execute("SELECT * FROM rate_counters WHERE team_key = ?", (key,)).fetchone()
    if not row:
        db.execute(
            "INSERT INTO rate_counters (team_key, count, window_start) VALUES (?, 1, ?)",
            (key, now),
        )
        db.commit()
        count = 1
    else:
        # Soft rate limit messaging, but still increments (intentionally bypassable)
        count = row["count"] + 1
        db.execute(
            "UPDATE rate_counters SET count = ? WHERE team_key = ?",
            (count, key),
        )
        db.commit()
        if count > 5 and (now - row["window_start"]) < 60 and count < 10:
            return fail(
                "Rate limit: 5 req/min (soft). Keep going...",
                request_count=count,
                remaining_soft=max(0, 5 - count),
            ), 429

    if count >= 10:
        return ok(
            "Challenge complete! You exhausted the soft limit.",
            flag=FLAGS[4],
            points_earned=15,
            request_count=count,
        )
    return fail(
        f"Request accepted ({count}/10 toward flag).",
        request_count=count,
        tip="Soft limit is 5/min — automation helps.",
    )


# ---------------------------------------------------------------------------
# Challenge 5 — Broken Function Level Authorization
# ---------------------------------------------------------------------------


@app.delete("/api/admin/users")
def delete_users():
    track_request(5)
    # No auth check on purpose
    return ok(
        "Challenge complete! Anyone could call this admin function.",
        flag=FLAGS[5],
        points_earned=15,
        deleted=["demo-user-shadow"],
    )


# ---------------------------------------------------------------------------
# Challenge 6 — Business Flow Abuse
# ---------------------------------------------------------------------------


@app.post("/api/transfer")
def transfer():
    track_request(6)
    data = request.get_json(silent=True) or {}
    amount = data.get("amount", 1)
    key = team_key_from_request()
    db = get_db()
    row = db.execute("SELECT * FROM transfer_counters WHERE team_key = ?", (key,)).fetchone()
    if not row:
        db.execute("INSERT INTO transfer_counters (team_key, count) VALUES (?, 1)", (key,))
        count = 1
    else:
        count = row["count"] + 1
        db.execute("UPDATE transfer_counters SET count = ? WHERE team_key = ?", (count, key))
    db.commit()

    if count >= 100:
        return ok(
            "Challenge complete! Business flow abused.",
            flag=FLAGS[6],
            points_earned=15,
            transfers=count,
            amount=amount,
        )
    return fail(
        f"Transfer OK. Progress {count}/100.",
        transfers=count,
        amount=amount,
    )


# ---------------------------------------------------------------------------
# Challenge 7 — SSRF
# ---------------------------------------------------------------------------


@app.get("/api/internal/flag")
def internal_flag():
    # Only meaningful when fetched via SSRF / loopback
    return jsonify({"metadata": "heist-internal", "flag": FLAGS[7]})


@app.post("/api/fetch-url")
def fetch_url():
    track_request(7)
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return fail("Provide JSON body: {\"url\": \"https://example.com\"}")

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    internal_hosts = {
        "169.254.169.254",
        "metadata.google.internal",
        "127.0.0.1",
        "localhost",
        "0.0.0.0",
    }

    # Simulated cloud metadata without real network call
    if host in {"169.254.169.254", "metadata.google.internal"} or "latest/meta-data" in url:
        return ok(
            "Challenge complete! SSRF hit internal metadata.",
            flag=FLAGS[7],
            points_earned=15,
            fetched={
                "url": url,
                "body": {"ami-id": "ami-heist", "flag": FLAGS[7]},
            },
        )

    if host in internal_hosts or host.startswith("127."):
        return ok(
            "Challenge complete! SSRF reached an internal service.",
            flag=FLAGS[7],
            points_earned=15,
            fetched={"url": url, "note": "internal"},
        )

    try:
        req = Request(url, headers={"User-Agent": "API-Heist-Academy/1.0"})
        with urlopen(req, timeout=3) as resp:
            body = resp.read(500).decode("utf-8", errors="replace")
        return fail("Fetched external URL.", fetched={"url": url, "snippet": body[:200]})
    except Exception as exc:
        return fail(f"Fetch failed: {exc}", url=url)


# ---------------------------------------------------------------------------
# Challenge 8 — Misconfiguration
# ---------------------------------------------------------------------------


@app.get("/api/debug")
def debug_endpoint():
    track_request(8)
    if request.args.get("crash") == "1":
        # Intentionally leak flag in error payload
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Internal Server Error",
                    "error": "ZeroDivisionError: division by zero",
                    "traceback": [
                        'File "app.py", line 418, in debug_endpoint',
                        "  secret = CONFIG['DEBUG_FLAG']",
                        f"  DEBUG_FLAG = '{FLAGS[8]}'",
                    ],
                    "flag": FLAGS[8],
                    "hint_used": False,
                }
            ),
            500,
        )
    return fail("Debug endpoint healthy. Try forcing an error.", tip="?crash=1")


# ---------------------------------------------------------------------------
# Challenge 9 — Improper Inventory / deprecated API
# ---------------------------------------------------------------------------


@app.get("/api/v2/users")
def users_v2():
    return jsonify(
        {
            "version": "v2",
            "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "note": "Current API. Old versions may still exist.",
        }
    )


@app.get("/api/v1/users")
def users_v1():
    track_request(9)
    return ok(
        "Challenge complete! Deprecated inventory still exposed.",
        flag=FLAGS[9],
        points_earned=15,
        version="v1-DEPRECATED",
        users=DEMO_USERS,
    )


# ---------------------------------------------------------------------------
# Challenge 10 — Unsafe Consumption of APIs / Webhook
# ---------------------------------------------------------------------------


@app.post("/api/webhook")
def webhook():
    track_request(10)
    data = request.get_json(silent=True) or {}
    event = str(data.get("event", "ping"))
    payload = data.get("payload", data.get("body", ""))

    dangerous = {
        "__flag__",
        "{{FLAG}}",
        "${FLAG}",
        "FLAG",
        "eval",
        "__import__",
    }
    blob = f"{event} {payload}".upper()
    if event in {"__flag__", "inject", "eval"} or any(d.upper() in blob for d in dangerous):
        return ok(
            "Challenge complete! Unsafe webhook consumption.",
            flag=FLAGS[10],
            points_earned=15,
            processed=True,
        )
    return fail("Webhook accepted.", event=event, processed=True)


# ---------------------------------------------------------------------------
# Final Boss
# ---------------------------------------------------------------------------


@app.post("/api/ultimate-challenge")
def ultimate_challenge():
    data = request.get_json(silent=True) or {}
    answers = data.get("flags") or data.get("answers") or []
    if isinstance(answers, dict):
        answers = list(answers.values())
    needed = [FLAGS[i] for i in range(1, 11)]
    matched = sum(1 for f in needed if f in answers)
    if matched >= 10:
        return ok(
            "FINAL BOSS CLEAR — the heist is complete!",
            flag=FLAGS[11],
            points_earned=15,
            matched=matched,
        )
    return fail(
        f"Need all 10 challenge flags. Matched {matched}/10.",
        matched=matched,
        tip='POST {"flags": ["FLAG{...}", ...]} with all ten flags.',
    )


# ---------------------------------------------------------------------------
# Frontend + health
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "API Heist Academy", "bind": f"{HOST}:{PORT}"})


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/<path:path>")
def static_proxy(path: str):
    target = STATIC_DIR / path
    if target.is_file():
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, "index.html")


init_db()


if __name__ == "__main__":
    print("=" * 60)
    print("API Heist Academy — EDUCATIONAL LAB ONLY")
    print(f"Serving on http://{HOST}:{PORT}")
    print("Do NOT expose this service to the public internet.")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=False)
