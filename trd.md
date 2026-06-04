# Technical Requirements Document

## Technology Stack

Frontend:
- Next.js 15
- TypeScript
- TailwindCSS
- ShadCN UI
- React Query

Backend:
- FastAPI
- Python 3.12

Database:
- MySQL 8.0+

Caching:
- Redis

Recognition:
- InsightFace
- DeepFace

Deployment:
- Docker
- Docker Compose
- NGINX

---

## System Architecture

Frontend
    ↓
FastAPI Gateway
    ↓
Attendance Service
    ↓
Face Recognition Service
    ↓
MySQL + Redis

---

## Database Schema

### employees

id
employee_code
full_name
email
phone
department_id
shift_id
status
created_at

### departments

id
name
created_at

### shifts

id
name
start_time
end_time
grace_minutes

### face_embeddings

id
employee_id
embedding_vector
created_at

### attendance_logs

id
employee_id
timestamp
device_id
recognition_score

### attendance_summary

id
employee_id
date
check_in
check_out
status
late_minutes
overtime_minutes

---

## API Endpoints

### Authentication

POST /api/auth/login

POST /api/auth/logout

POST /api/auth/refresh

---

### Employee

GET /api/employees

POST /api/employees

PUT /api/employees/{id}

DELETE /api/employees/{id}

---

### Face Enrollment

POST /api/faces/enroll

GET /api/faces/{employeeId}

DELETE /api/faces/{employeeId}

---

### Recognition

POST /api/attendance/recognize

POST /api/attendance/checkin

POST /api/attendance/checkout

---

### Reports

GET /api/reports/daily

GET /api/reports/monthly

GET /api/reports/overtime

GET /api/reports/late

---

## Face Recognition Flow

1. Capture image

2. Detect face

3. Generate embedding

4. Compare embedding

5. Match threshold

6. Create attendance record

7. Return result

---

## Matching Strategy

Cosine Similarity

Threshold:
0.65-0.75 configurable

Duplicate Prevention:
No duplicate attendance within 5 minutes

---

## Security

JWT

Refresh Tokens

RBAC

Audit Logs

Encryption At Rest

HTTPS

Rate Limiting

Face Embedding Encryption

---

## Deployment Structure

/apps/frontend

/apps/backend

/apps/recognition-service

/packages/shared

/docker

/docs

---

## Monitoring

Prometheus

Grafana

Structured Logs

Error Tracking

Health Checks

---

## Backup Strategy

Daily Database Backup

Weekly Full Backup

Retention 90 Days