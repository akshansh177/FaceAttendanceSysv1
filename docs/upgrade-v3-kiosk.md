# Face Attendance V3 — Public Kiosk & Employee Portal

## Highlights

- Public fullscreen kiosk at `/kiosk` (no login)
- Multi-frame liveness (blink, head movement, anti-static)
- `attendance_kiosks` registry with API keys and `last_seen`
- Attendance methods: kiosk_only, portal_only, kiosk_portal, mobile_app (API only), any
- Scoped attendance policies (employee, department, job role, location, shift)
- HR live attendance feed (Redis + polling)
- Employee portal: profile, password, calendar, CSV export, enhanced dashboard
- Login with email or employee code

## Kiosk setup

1. HR creates kiosk at `/kiosks` — save the one-time API key.
2. On the kiosk device, open `/kiosk` and enter device ID + API key (stored in localStorage).
3. Or set `NEXT_PUBLIC_KIOSK_DEVICE_ID` and `NEXT_PUBLIC_KIOSK_API_KEY` in frontend env.

## API

| Endpoint | Auth |
|----------|------|
| `GET /api/kiosk/config` | Public |
| `POST /api/kiosk/recognize` | `X-Kiosk-Key` + `device_identifier` |
| `POST /api/kiosk/heartbeat` | Same |

## Migration

```bash
cd apps/backend && alembic upgrade head
python -m app.seed_v3   # existing DBs
```

Fresh installs: `python -m app.seed` includes sample kiosk.
