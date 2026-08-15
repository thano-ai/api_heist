# Student Cheat Sheet — Attack Patterns

Use with **Postman** or **Burp**. Base URL: `http://127.0.0.1:5000/api`  
Always send header: `X-Team-Name: YourTeam`

Submit flags in the UI. Pattern reference only — discover the exact payloads yourself.

---

### 1. BOLA — IDOR
Change resource IDs in the path/query. Ask: *Can I read objects that are not mine?*

### 2. Broken Authentication
Inspect tokens (JWT). Tamper with claims (`role`, `admin`, `sub`). Check whether the server verifies signatures.

### 3. Mass Assignment
Add unexpected JSON fields when updating a profile (`role`, `isAdmin`, `balance`).

### 4. Unrestricted Resource Consumption
Automate repeated requests. Watch counters and soft limits. Collection Runner / Intruder help.

### 5. Broken Function Level Authorization
Call admin verbs/paths (`DELETE`, `/admin/...`) as a normal user.

### 6. Business Flow Abuse
Legitimate action, illegitimate volume — script the happy path hundreds of times.

### 7. SSRF
Point URL-fetch features at internal targets (link-local metadata, localhost services).

### 8. Security Misconfiguration
Force errors/debug modes. Read stack traces and verbose responses carefully.

### 9. Improper Inventory Management
Try older versions (`/v1/`, `/internal/`, undocumented paths) even if docs show `/v2/`.

### 10. Unsafe Consumption of APIs
Treat inbound webhooks as untrusted. Probe unusual `event` / payload values.

---

## Flag format

`FLAG{ChallengeName_SomeString}`

## Hot seat rules

- 100-minute session clock for the whole class (pauses between challenges)  
- Free hint OK  
- Second hint costs points  
- Pass the keyboard when time is up  
