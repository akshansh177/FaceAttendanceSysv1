# Face Attendance V2 Upgrade Specification

## Overview

V2 moves the platform to **MySQL 8**, extends HR/org data, adds configurable attendance validation (face, GPS, network, device), correction workflows, audit hardening, email notifications, and role-specific dashboards.

## In scope

- MySQL 8 database (fresh install; no PostgreSQL data migration)
- Job roles, locations, employee–location assignments
- Employee fields: employment type, joining date, manager reporting line
- Organization attendance settings (modes 1–4)
- Device registry with approval workflow
- Attendance summary: workflow status, worked/expected minutes, missing checkout detection
- Two-step attendance corrections (manager → HR)
- Audit logging on sensitive operations (read-only API for super admin)
- SMTP notifications (late, missing checkout, correction status)
- HR / manager / employee dashboard APIs and UI

## Out of scope (future)

- Mobile app, visitor management, payroll
- Full leave suite, AI insights, self-service portal
- Biometric hardware SDK, WhatsApp, multi-tenant

## Attendance modes

| Mode | Validation |
|------|------------|
| `face_only` | Face match only |
| `face_gps` | Face + within assigned location radius |
| `face_network` | Face + client IP in allowed CIDRs |
| `face_gps_device` | Face + GPS + approved registered device |

## Correction workflow

1. Employee submits correction with date, optional check-in/out, reason.
2. Team manager approves → `pending_hr`.
3. HR approves → updates `attendance_summary`, audit log, optional email.

## Roles

- **super_admin** — full access, audit logs
- **hr_manager** — HR entities, settings, final correction approval
- **team_manager** — team dashboard, first correction approval
- **employee** — kiosk, my attendance, correction requests
