# Instructor Guide — API Heist Academy

**For instructors only.** Do not share full solutions with students before the lab.

## Session flow (≈60–90 min)

1. Intro slides: OWASP API Top 10 overview (10 min)
2. Demo Postman / Burp proxy once (5 min)
3. Team rotation: each team 10 min on one challenge (~100 min)
4. Final Boss + scoreboard (10 min)
5. Debrief: what broke and how to fix it (10 min)

## Flags (answer key)

| # | Vulnerability | Flag | How to solve |
|---|---------------|------|--------------|
| 1 | BOLA | `FLAG{B0L4_G0t_M3_2024}` | `GET /api/user/3` |
| 2 | Broken Auth | `FLAG{4uth_1s_H4rd_Right}` | JWT with `"role":"admin"` (signature not strictly enforced) |
| 3 | Mass Assignment | `FLAG{M4ss_4ss1gn_OhNo}` | `PUT /api/user/update` body includes `"role":"admin"` |
| 4 | Resource Consumption | `FLAG{R4t3_L1m1t_Byp4ss}` | 10× `GET /api/rate-limited` (same `X-Team-Name`) |
| 5 | BFLA | `FLAG{Adm1n_Funct10n_Oops}` | `DELETE /api/admin/users` (no auth) |
| 6 | Business Flow | `FLAG{Fl0w_Abus3_Pr0f1t}` | 100× `POST /api/transfer` |
| 7 | SSRF | `FLAG{SSRF_1nt3rn4l_M3t4}` | `POST /api/fetch-url` with `http://169.254.169.254/...` or localhost internal |
| 8 | Misconfiguration | `FLAG{Debu9_M0d3_Dang3r}` | `GET /api/debug?crash=1` |
| 9 | Inventory | `FLAG{V3rs10n_Exp0s3d}` | `GET /api/v1/users` |
| 10 | Unsafe Consumption | `FLAG{Webh00k_Inj3ct10n}` | `POST /api/webhook` with `event: "__flag__"` |
| 11 | Final Boss | `FLAG{Ult1m4te_H31st_C0mpl3te}` | POST all 10 flags to `/api/ultimate-challenge` |

## Teaching points (fixes)

1. **BOLA** — authorize every object access against the caller’s identity  
2. **Broken Auth** — verify JWT signature, issuer, audience, and role claims  
3. **Mass Assignment** — allowlist updatable fields; never accept `role` from clients  
4. **Resource Consumption** — hard rate limits, quotas, pagination caps  
5. **BFLA** — deny-by-default on admin routes; check permissions per function  
6. **Business Flow** — velocity checks, CAPTCHA, transaction limits  
7. **SSRF** — allowlist outbound hosts; block link-local / loopback  
8. **Misconfig** — disable debug in production; generic error pages  
9. **Inventory** — retire old versions; inventory all endpoints  
10. **Unsafe Consumption** — validate/sanitize third-party webhook payloads  

## Classroom ops

- Run only on instructor laptop / isolated VLAN  
- Firewall: block inbound from WAN  
- After class: delete `backend/heist.db` or full-reset via API  
- Change flags between cohorts if students share answers  

## Scoring reminder

- Each challenge: **15 pts**  
- Free hint: no cost  
- Paid hint: −5 → **10 pts** on that challenge  

