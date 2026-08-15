# Instructor Solutions — Full Step-by-Step Walkthrough

**Instructors only.** Do not give this to students during the lab.

---

## Before you start (tools)

You only need these:

| Tool | What for | Get it |
|------|----------|--------|
| Browser | Game UI + flag submit | Chrome / Edge / Firefox |
| Postman | Send API requests | https://www.postman.com/downloads/ |
| jwt.io (website) | Decode / forge JWTs | https://jwt.io |
| (Optional) Burp Suite Community | Intruder / Repeater for loops | https://portswigger.net/burp/communitydownload |

### Lab setup checklist

1. Server running: `python app.py` in `backend` → **http://127.0.0.1:5000**
2. Open the UI in the browser and register a team (e.g. `Instructor`).
3. In Postman: **Import** → `postman/API-Heist-Academy.postman_collection.json`
4. In the collection variables, set:
   - `baseUrl` = `http://127.0.0.1:5000/api`
   - `teamName` = same name you registered in the UI
5. Always keep header **`X-Team-Name: {{teamName}}`** on challenge requests (starter kit already has this).

### How scoring works in the UI

1. Use Postman/Burp to find the flag in a JSON response (`"flag": "FLAG{...}"`).
2. Copy that string.
3. In the UI, open the matching level → **Submit flag** → paste → submit.
4. Roadmap unlocks the next level after a correct submit.

---

## Challenge 1 — BOLA (IDOR)

**Vulnerability:** Changing the user ID in the URL returns other people’s data.

### Tools
Postman (or browser address bar).

### Steps

1. Open Postman → folder **01 Profiles** → request **Get my profile**.
2. Click **Send**.
3. You should see Alice’s profile for `/user/1`. Note there is no flag.
4. In the URL bar of Postman, change:
   - `{{baseUrl}}/user/1` → `{{baseUrl}}/user/2`
5. **Send** again — Bob’s profile, still no flag.
6. Change to `{{baseUrl}}/user/3` → **Send**.
7. In the JSON response, find:
   - `"success": true`
   - `"flag": "FLAG{B0L4_G0t_M3_2024}"`
   - often also `"secret_note"` with the same value.
8. Copy the flag → UI Level 1 → **Submit flag**.

**Flag:** `FLAG{B0L4_G0t_M3_2024}`

**Teaching line:** “Never trust a client-supplied object ID without an ownership check.”

---

## Challenge 2 — Broken Authentication (JWT)

**Vulnerability:** Admin check trusts the `role` claim; signature verification is weak.

### Tools
Postman + **https://jwt.io**

### Steps

#### A. Get a sample token from the API

1. Postman → **02 Admin area** → **Open admin panel**.
2. Make sure `Authorization` is empty or `Bearer` with empty `{{token}}`.
3. **Send**.
4. Response should say you need auth and include something like:
   ```json
   "sample_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...."
   ```
5. Copy the **entire** `sample_token` string (three parts separated by dots: `header.payload.signature`).

#### B. Decode it on jwt.io

1. Open https://jwt.io
2. Paste the token into the **Encoded** box on the left.
3. On the right, under **PAYLOAD**, you will see JSON similar to:
   ```json
   {
     "sub": "guest",
     "role": "user"
   }
   ```
4. There is **no secret you must “steal”** for this lab. The weakness is: if `role` becomes `admin`, access is granted even when the signature is wrong / missing.

#### C. Forge an admin token

**Option 1 — easiest (jwt.io):**

1. In jwt.io **PAYLOAD**, change `"role": "user"` to `"role": "admin"`.
2. In **Verify Signature**, you can leave the default secret or type anything (e.g. `secret`).
3. jwt.io will rebuild a new token on the left — copy that full encoded token.

**Option 2 — alg:none style (advanced demo):**

Header: `{"alg":"none","typ":"JWT"}`  
Payload: `{"sub":"hacker","role":"admin"}`  
Signature: empty  
(Students can build this with jwt.io by selecting algorithm none if available, or use any online/none encoder.)

#### D. Call admin with the forged token

1. Back in Postman, set collection variable `token` to your forged JWT  
   **or** edit the request header to:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   (paste your forged token after `Bearer ` — note the space)
2. **Send** `GET {{baseUrl}}/admin` again.
3. Response includes `"flag": "FLAG{4uth_1s_H4rd_Right}"`.
4. Submit in the UI.

**Flag:** `FLAG{4uth_1s_H4rd_Right}`

**Where does the “signature” come from?**  
JWTs have three parts. The third part is the signature. In a secure app you need the server secret to make a valid signature. **In this lab you do not need the real server secret** — the app accepts an admin `role` even if the signature does not verify. That is the lesson.

**Teaching line:** “Always verify signature, algorithm, and claims server-side — never trust a client-edited JWT.”

---

## Challenge 3 — Mass Assignment

**Vulnerability:** Update endpoint accepts extra JSON fields like `role`.

### Tools
Postman.

### Steps

1. Postman → **03 Profile update** → **Update profile**.
2. Body is already something like:
   ```json
   {
     "name": "Alice",
     "email": "alice@heist.local"
   }
   ```
3. **Send** — profile updates, no flag.
4. Edit the body to add a privilege field:
   ```json
   {
     "name": "Alice",
     "email": "alice@heist.local",
     "role": "admin"
   }
   ```
5. **Send** again.
6. Response includes `"flag": "FLAG{M4ss_4ss1gn_OhNo}"`.
7. Submit in the UI.

**Flag:** `FLAG{M4ss_4ss1gn_OhNo}`

**Teaching line:** “Allowlist writable fields; never bind `role` / `isAdmin` from client input.”

---

## Challenge 4 — Resource Consumption (soft rate limit)

**Vulnerability:** Soft limit can be exceeded; flag appears at request #10.

### Tools
Postman **Collection Runner** (or Burp Intruder).

### Steps (Postman Runner)

1. Open request **04 Busy endpoint → Call rate-limited route**.
2. **Send** once — note `"request_count": 1` (or similar).
3. Click the **...** menu on that request (or the folder) → **Run** / open **Collection Runner**.
4. Set **Iterations** to `10` (or `15`).
5. Delay optional (0–100 ms is fine).
6. Click **Run**.
7. Watch responses in the run results. Around iteration 10 you should see `"success": true` and the flag.
8. If you already burned counts for this team, register a new team name (UI + Postman `teamName`) and rerun.

**Burp alternative:** Send once to Repeater → Intruder → null payloads × 10–15 → Start attack → sort by response length / look for `FLAG{`.

**Flag:** `FLAG{R4t3_L1m1t_Byp4ss}`

**Teaching line:** “Enforce hard quotas server-side; soft messages are not controls.”

---

## Challenge 5 — Broken Function Level Authorization

**Vulnerability:** Admin DELETE works with no auth.

### Tools
Postman.

### Steps

1. Postman → **05 Admin users** → **Admin users action**.
2. Method should be **DELETE**, URL `{{baseUrl}}/admin/users`.
3. No Authorization header needed.
4. **Send**.
5. Flag appears immediately: `FLAG{Adm1n_Funct10n_Oops}`.
6. Submit in the UI.

**Flag:** `FLAG{Adm1n_Funct10n_Oops}`

**Teaching line:** “Authorize every function, not just ‘looks like admin in the path’.”

---

## Challenge 6 — Business Flow Abuse

**Vulnerability:** Transfer is allowed unbounded times.

### Tools
Postman Collection Runner (or Burp Intruder).

### Steps

1. Postman → **06 Transfers** → **Send transfer**.
2. Body:
   ```json
   { "to": "bob", "amount": 1 }
   ```
3. **Send** once — response shows progress like `1/100`.
4. Run the request with **Collection Runner**:
   - Iterations = **100**
   - Same `teamName`
5. On the 100th success, response includes the flag.
6. Submit in the UI.

**Tip:** If you stop halfway, continuing with the same team name resumes the counter.

**Flag:** `FLAG{Fl0w_Abus3_Pr0f1t}`

**Teaching line:** “Sensitive flows need velocity limits, fraud checks, and step-up auth.”

---

## Challenge 7 — SSRF

**Vulnerability:** Server fetches any URL, including internal ones.

### Tools
Postman.

### Steps

1. Postman → **07 URL fetch** → **Fetch a URL**.
2. First send the safe baseline body:
   ```json
   { "url": "https://example.com" }
   ```
3. You get an external fetch / snippet — no flag.
4. Change `url` to an internal target, for example:
   ```json
   { "url": "http://169.254.169.254/latest/meta-data/" }
   ```
   or:
   ```json
   { "url": "http://127.0.0.1:5000/api/internal/flag" }
   ```
5. **Send**.
6. Response includes `"flag": "FLAG{SSRF_1nt3rn4l_M3t4}"`.
7. Submit in the UI.

**What is 169.254.169.254?**  
Classic cloud “instance metadata” address. Real clouds host secrets there; this lab simulates that hit.

**Flag:** `FLAG{SSRF_1nt3rn4l_M3t4}`

**Teaching line:** “Allowlist outbound hosts; block link-local, localhost, and private ranges.”

---

## Challenge 8 — Security Misconfiguration

**Vulnerability:** Debug/error mode leaks secrets.

### Tools
Postman (or browser).

### Steps

1. Postman → **08 Diagnostics** → **Debug endpoint**.
2. **Send** `GET {{baseUrl}}/debug` — healthy, tip about forcing an error.
3. Add a query parameter that breaks it:
   - Change URL to: `{{baseUrl}}/debug?crash=1`
4. **Send**.
5. You get HTTP **500**. In the JSON body look for `"flag"` or `DEBUG_FLAG` in the traceback.
6. Copy `FLAG{Debu9_M0d3_Dang3r}` → submit in UI.

**Browser path:** open  
`http://127.0.0.1:5000/api/debug?crash=1`

**Flag:** `FLAG{Debu9_M0d3_Dang3r}`

**Teaching line:** “Never ship debug mode; return generic errors to clients.”

---

## Challenge 9 — Improper Inventory Management

**Vulnerability:** Old API version still live.

### Tools
Postman.

### Steps

1. Postman → **09 User listing** → **List users (current)**.
2. **Send** `GET {{baseUrl}}/v2/users`.
3. Read the note that older versions may still exist.
4. Duplicate the request (or edit URL) and change **`v2` → `v1`**:
   - `GET {{baseUrl}}/v1/users`
5. **Send**.
6. Deprecated endpoint returns the flag.
7. Submit in the UI.

**Flag:** `FLAG{V3rs10n_Exp0s3d}`

**Teaching line:** “Inventory and retire old APIs; shadow endpoints stay in scope for attackers.”

---

## Challenge 10 — Unsafe Consumption (webhooks)

**Vulnerability:** Webhook handler trusts weird event/payload values.

### Tools
Postman.

### Steps

1. Postman → **10 Webhooks** → **Send webhook event**.
2. Baseline body:
   ```json
   { "event": "ping", "payload": "hello" }
   ```
3. **Send** — accepted, no flag.
4. Change to a malicious-looking control event, e.g.:
   ```json
   {
     "event": "__flag__",
     "payload": "{{FLAG}}"
   }
   ```
5. **Send**.
6. Flag returned: `FLAG{Webh00k_Inj3ct10n}`.
7. Submit in the UI.

**Other payloads that also work in this lab:**  
`event` = `inject` or `eval`, or a payload string containing `FLAG` / `{{FLAG}}` / `${FLAG}`.

**Note on `{{FLAG}}` in Postman:**  
Postman treats `{{...}}` as variables. If it substitutes unexpectedly, send raw JSON with event `__flag__` only, or escape by using a body that does not rely on Postman variables (e.g. `"payload": "__FLAG__"` still matches because it contains `FLAG`).

**Flag:** `FLAG{Webh00k_Inj3ct10n}`

**Teaching line:** “Validate and sanitize all inbound third-party/webhook data.”

---

## Final Boss

### Tools
Postman.

### Steps

1. Collect all 10 flags (from responses or your notes).
2. Postman → **11 Endgame** → **Ultimate challenge**.
3. Body:
   ```json
   {
     "flags": [
       "FLAG{B0L4_G0t_M3_2024}",
       "FLAG{4uth_1s_H4rd_Right}",
       "FLAG{M4ss_4ss1gn_OhNo}",
       "FLAG{R4t3_L1m1t_Byp4ss}",
       "FLAG{Adm1n_Funct10n_Oops}",
       "FLAG{Fl0w_Abus3_Pr0f1t}",
       "FLAG{SSRF_1nt3rn4l_M3t4}",
       "FLAG{Debu9_M0d3_Dang3r}",
       "FLAG{V3rs10n_Exp0s3d}",
       "FLAG{Webh00k_Inj3ct10n}"
     ]
   }
   ```
4. **Send** → receive final flag `FLAG{Ult1m4te_H31st_C0mpl3te}`.
5. In the UI, open **Final boss** → paste that final flag → submit  
   (or use game submit-flag with `challengeId: 11`).

---

## Quick reference — tools per challenge

| # | Primary tool | Key action |
|---|--------------|------------|
| 1 | Postman | Change `/user/1` → `/user/3` |
| 2 | Postman + jwt.io | Forge JWT `role=admin` |
| 3 | Postman | Add `"role":"admin"` to JSON body |
| 4 | Postman Runner | Repeat GET 10× |
| 5 | Postman | DELETE with no auth |
| 6 | Postman Runner | POST transfer 100× |
| 7 | Postman | Point `url` at metadata / localhost |
| 8 | Postman / browser | `?crash=1` |
| 9 | Postman | Try `/v1/users` instead of `/v2` |
| 10 | Postman | Weird `event` / payload |
| 11 | Postman | POST all 10 flags |

---

## Flag table

| # | Flag |
|---|------|
| 1 | `FLAG{B0L4_G0t_M3_2024}` |
| 2 | `FLAG{4uth_1s_H4rd_Right}` |
| 3 | `FLAG{M4ss_4ss1gn_OhNo}` |
| 4 | `FLAG{R4t3_L1m1t_Byp4ss}` |
| 5 | `FLAG{Adm1n_Funct10n_Oops}` |
| 6 | `FLAG{Fl0w_Abus3_Pr0f1t}` |
| 7 | `FLAG{SSRF_1nt3rn4l_M3t4}` |
| 8 | `FLAG{Debu9_M0d3_Dang3r}` |
| 9 | `FLAG{V3rs10n_Exp0s3d}` |
| 10 | `FLAG{Webh00k_Inj3ct10n}` |
| 11 | `FLAG{Ult1m4te_H31st_C0mpl3te}` |
