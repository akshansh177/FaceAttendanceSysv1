# Testing Guide

## Recognition accuracy protocol

Target: >95% match rate on enrolled employees.

1. Enroll each test subject with 5–10 varied photos (angles, lighting).
2. Capture 20 live kiosk frames per subject across sessions.
3. Record `recognition_score` from API responses.
4. Accuracy = correct matches / total attempts.
5. Tune `MATCH_THRESHOLD` (default 0.70) if false rejects exceed 5%.

## Performance benchmarks

| Metric | Target |
|--------|--------|
| Face recognition (InsightFace) | < 1s |
| Attendance end-to-end | < 3s |
| Report generation (100 employees) | < 10s |
| Dashboard load | < 2s |

## Manual test checklist

- [ ] Login as admin, HR, manager, employee
- [ ] CRUD employees, departments, shifts
- [ ] Enroll face (5+ images)
- [ ] Kiosk check-in and check-out
- [ ] Duplicate blocked within 5 minutes
- [ ] Late/overtime after recompute
- [ ] Export report CSV/PDF/XLSX
- [ ] Dashboard metrics and trends
