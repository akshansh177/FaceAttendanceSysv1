export type UserRole = "super_admin" | "hr_manager" | "team_manager" | "employee";

export interface Employee {
  id: string;
  employee_code: string;
  full_name: string;
  email: string;
  phone: string | null;
  department_id: string | null;
  job_role_id: string | null;
  shift_id: string | null;
  manager_id: string | null;
  employment_type: string;
  joining_date: string | null;
  status: string;
  profile_photo_path: string | null;
  location_ids: string[];
  created_at: string;
}

export interface Department {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
}

export interface JobRole {
  id: string;
  name: string;
  description: string | null;
  permission_flags: Record<string, unknown> | null;
  created_at: string;
}

export interface Location {
  id: string;
  name: string;
  address: string | null;
  latitude: number;
  longitude: number;
  radius_meters: number;
  is_active: boolean;
  created_at: string;
}

export interface Shift {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  grace_minutes: number;
  shift_type: string;
  created_at: string;
}

export interface Device {
  id: string;
  device_id: string;
  name: string;
  device_type: string;
  mac_address: string | null;
  location_id: string | null;
  status: string;
  created_at: string;
}

export interface AttendanceSettings {
  attendance_mode: string;
  attendance_method: string;
  gps_enforcement_enabled: boolean;
  device_enforcement_enabled: boolean;
  allowed_ip_cidrs: string[] | null;
  kiosk_checkout_after_checkout: string;
  kiosk_screen_reset_seconds: number;
  voice_feedback_enabled: boolean;
  voice_language: string;
  match_threshold_preset?: string | null;
  match_threshold?: number | null;
  effective_match_threshold?: number;
}

export interface KioskConfig {
  screen_reset_seconds: number;
  voice_feedback_enabled: boolean;
  voice_language: string;
  company_name: string;
}

export interface KioskRecognizeResponse {
  matched: boolean;
  status: string;
  code: string;
  display_message: string;
  employee_id?: string;
  photo_url?: string | null;
  full_name?: string | null;
  employee_code?: string | null;
  department?: string | null;
  job_role?: string | null;
  current_time?: string | null;
  attendance_status?: string | null;
  event?: string | null;
  score?: number | null;
}

export interface Kiosk {
  id: string;
  name: string;
  device_identifier: string;
  location_id: string | null;
  department_id: string | null;
  status: string;
  last_seen: string | null;
  is_online: boolean;
  created_at: string;
  employee_ids: string[];
}

export interface KioskCreateResponse extends Kiosk {
  api_key: string;
}

export interface AttendancePolicy {
  id: string;
  name: string;
  scope_type: string;
  scope_id: string | null;
  priority: number;
  rules_json: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export interface LiveFeedItem {
  id: string;
  employee_name: string;
  employee_code: string | null;
  department: string | null;
  job_role: string | null;
  event_type: string;
  timestamp: string;
  kiosk_name: string | null;
  location: string | null;
}

export interface EmployeeDashboard {
  today_status: string | null;
  workflow_status: string | null;
  monthly_present: number;
  monthly_absent: number;
  leave_balance_placeholder: number;
  check_in: string | null;
  check_out: string | null;
  worked_minutes: number;
  overtime_minutes: number;
  shift_name: string | null;
  attendance_percentage: number;
}

export interface Correction {
  id: string;
  employee_id: string;
  date: string;
  requested_check_in: string | null;
  requested_check_out: string | null;
  reason: string;
  status: string;
  created_at: string;
}

export interface DashboardMetrics {
  present_today: number;
  absent_today: number;
  late_today: number;
  missing_checkout_today: number;
  overtime_today: number;
  total_employees: number;
  active_employees: number;
  department_breakdown: { department: string; present: number; total: number }[];
}

export interface DashboardTrends {
  dates: string[];
  present: number[];
  absent: number[];
  late: number[];
}

export interface RecognizeResponse {
  matched: boolean;
  employee_id?: string;
  employee_name?: string;
  score?: number;
  event?: string;
  message: string;
  duplicate?: boolean;
}

export interface AttendanceSummary {
  id: string;
  employee_id: string;
  date: string;
  check_in: string | null;
  check_out: string | null;
  status: string;
  workflow_status?: string | null;
  late_minutes: number;
  overtime_minutes: number;
  worked_minutes?: number;
  expected_minutes?: number;
}

export interface ReportRow {
  employee_code: string;
  full_name: string;
  department: string | null;
  date?: string | null;
  check_in?: string | null;
  check_out?: string | null;
  status: string;
  late_minutes: number;
  overtime_minutes: number;
}

export interface Holiday {
  id: string;
  name: string;
  date: string;
  scope: string;
  department_id: string | null;
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  start_date: string;
  end_date: string;
  reason: string | null;
  status: string;
  created_at: string;
}
