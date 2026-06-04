export type UserRole = "super_admin" | "hr_manager" | "team_manager" | "employee";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: UserRole;
}

export interface Employee {
  id: string;
  employee_code: string;
  full_name: string;
  email: string;
  phone: string | null;
  department_id: string | null;
  shift_id: string | null;
  status: string;
  profile_photo_path: string | null;
  created_at: string;
}

export interface Department {
  id: string;
  name: string;
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

export interface DashboardMetrics {
  present_today: number;
  absent_today: number;
  late_today: number;
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
  late_minutes: number;
  overtime_minutes: number;
}
