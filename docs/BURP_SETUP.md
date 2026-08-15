# Burp Suite Setup — API Heist Academy

## Proxy

1. Burp Proxy listen on `127.0.0.1:8080`
2. Browser / system proxy → `127.0.0.1:8080`
3. Install Burp CA if testing HTTPS (this lab is HTTP)

## Scope

Add to target scope:

```
http://127.0.0.1:5000
```

## Suggested Repeater tabs

| Tab | Method | URL | Notes |
|-----|--------|-----|-------|
| C1 BOLA | GET | `/api/user/1` | Intruder on `id` 1–10 |
| C2 Auth | GET | `/api/admin` | Tamper `Authorization` |
| C3 Mass | PUT | `/api/user/update` | JSON `role` |
| C4 Rate | GET | `/api/rate-limited` | Intruder null payloads ×15 |
| C5 BFLA | DELETE | `/api/admin/users` | No token |
| C6 Flow | POST | `/api/transfer` | Intruder ×100 |
| C7 SSRF | POST | `/api/fetch-url` | Intruder `url` |
| C8 Debug | GET | `/api/debug?crash=1` | Read error body |
| C9 Inv | GET | `/api/v1/users` | Compare to `/v2` |
| C10 Hook | POST | `/api/webhook` | Unusual events |

## Intruder positions (quick)

- **C1:** `/api/user/§1§` numbers 1–10  
- **C2:** `Authorization: Bearer §token§`  
- **C3:** `"role": "§admin§"`  
- **C4 / C6:** sniper with empty payload list, 10–100 requests  
- **C7:** `"url": "§http://169.254.169.254/§"`

## Header for scoring counters

```
X-Team-Name: Alpha
```

Rate-limit and transfer counters key off this header (or IP if missing).
