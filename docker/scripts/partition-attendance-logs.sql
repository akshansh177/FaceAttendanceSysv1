-- Ops runbook: monthly RANGE partitioning for attendance_logs (MySQL 8).
-- Run during a maintenance window after backing up the table.

-- 1) Verify row counts and disk space.
-- SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM attendance_logs;

-- 2) Example: recreate table with partitioning (adjust dates to your retention plan).
/*
CREATE TABLE attendance_logs_new LIKE attendance_logs;
ALTER TABLE attendance_logs_new
  PARTITION BY RANGE (TO_DAYS(timestamp)) (
    PARTITION p202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    PARTITION pmax VALUES LESS THAN MAXVALUE
  );
INSERT INTO attendance_logs_new SELECT * FROM attendance_logs;
RENAME TABLE attendance_logs TO attendance_logs_old, attendance_logs_new TO attendance_logs;
DROP TABLE attendance_logs_old;
*/

-- 3) Add future partitions monthly:
-- ALTER TABLE attendance_logs REORGANIZE PARTITION pmax INTO (
--   PARTITION p202606 VALUES LESS THAN (TO_DAYS('2025-07-01')),
--   PARTITION pmax VALUES LESS THAN MAXVALUE
-- );
