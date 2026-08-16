const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Company {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
  description?: string;
  tier: string;
}

export interface UserTargetCompany {
  id: string;
  company_id: string;
  priority: number;
  company: Company;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: "USER" | "ADMIN";
  skill_level: "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
  daily_goal_minutes: number;
  preferred_language: "python" | "java" | "cpp";
  onboarding_completed: boolean;
  target_companies: UserTargetCompany[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ServiceHealth {
  status: "healthy" | "degraded" | "unhealthy";
  message: string;
}

export interface HealthCheckResponse {
  status: "ok" | "degraded" | "unhealthy";
  app_name: string;
  environment: string;
  timestamp: string;
  services: {
    database: ServiceHealth;
    redis: ServiceHealth;
  };
}

export interface Topic {
  id: string;
  name: string;
  slug: string;
  description?: string;
}

export interface ProblemCompany {
  id: string;
  company_id: string;
  company: Company;
  frequency_weight: number;
  recency_window: string;
  round_type: string;
  source_classification: string;
}

export interface TestCase {
  id: string;
  input_data: string;
  expected_output: string;
  is_sample: boolean;
}

export interface Hint {
  id: string;
  step_number: number;
  title: string;
  content_markdown: string;
  code_snippet?: string;
}

export interface ProblemListItem {
  id: string;
  title: string;
  slug: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  category: string;
  topics: Topic[];
  companies: ProblemCompany[];
  user_status: "UNATTEMPTED" | "ATTEMPTED" | "SOLVED";
  is_bookmarked: boolean;
}

export interface ProblemPaginatedResponse {
  items: ProblemListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ProblemDetail {
  id: string;
  title: string;
  slug: string;
  description_markdown: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  category: string;
  constraints_text?: string;
  starter_code: Record<string, string>;
  topics: Topic[];
  companies: ProblemCompany[];
  sample_test_cases: TestCase[];
  user_status: "UNATTEMPTED" | "ATTEMPTED" | "SOLVED";
  hints_unlocked: number;
  hints: Hint[];
  is_bookmarked: boolean;
  personal_notes?: string;
}

export interface SingleTestCaseResult {
  passed: boolean;
  input_data: string;
  expected_output: string;
  actual_output: string;
  status: string;
  execution_time_ms?: number;
  memory_kb?: number;
  error_message?: string;
}

export interface BatchExecutionResult {
  overall_status: string;
  passed_test_cases: number;
  total_test_cases: number;
  execution_time_ms?: number;
  memory_kb?: number;
  error_output?: string;
  test_case_results: SingleTestCaseResult[];
}

export interface Submission {
  id: string;
  user_id: string;
  problem_id: string;
  language: string;
  code: string;
  status: string;
  execution_time_ms?: number;
  memory_kb?: number;
  passed_test_cases: number;
  total_test_cases: number;
  error_output?: string;
  created_at: string;
}

export interface SubmissionPaginatedResponse {
  items: Submission[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export async function fetchHealthStatus(): Promise<HealthCheckResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    return {
      status: "degraded",
      app_name: "CodeTarget",
      environment: "development",
      timestamp: new Date().toISOString(),
      services: {
        database: {
          status: "unhealthy",
          message: error instanceof Error ? error.message : "Backend unreachable",
        },
        redis: {
          status: "unhealthy",
          message: "Backend unreachable",
        },
      },
    };
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: "include", // Required for HttpOnly refresh cookies
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "An unexpected error occurred");
  }

  return data as T;
}

export async function fetchCompanies(): Promise<Company[]> {
  return apiRequest<Company[]>("/api/v1/companies");
}

export async function fetchTopics(): Promise<Topic[]> {
  return apiRequest<Topic[]>("/api/v1/problems/topics");
}

export async function fetchProblems(
  params: {
    company?: string;
    difficulty?: string;
    topic?: string;
    status?: string;
    search?: string;
    page?: number;
    page_size?: number;
  } = {},
  token?: string | null
): Promise<ProblemPaginatedResponse> {
  const query = new URLSearchParams();
  if (params.company) query.set("company", params.company);
  if (params.difficulty) query.set("difficulty", params.difficulty);
  if (params.topic) query.set("topic", params.topic);
  if (params.status) query.set("status", params.status);
  if (params.search) query.set("search", params.search);
  if (params.page) query.set("page", params.page.toString());
  if (params.page_size) query.set("page_size", params.page_size.toString());

  return apiRequest<ProblemPaginatedResponse>(`/api/v1/problems?${query.toString()}`, {}, token);
}

export async function fetchProblemBySlug(slug: string, token: string): Promise<ProblemDetail> {
  return apiRequest<ProblemDetail>(`/api/v1/problems/${slug}`, {}, token);
}

export async function runSampleCode(
  token: string,
  data: { problem_id: string; language: string; code: string }
): Promise<BatchExecutionResult> {
  return apiRequest<BatchExecutionResult>(
    "/api/v1/submissions/run-sample",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
    token
  );
}

export async function submitSolution(
  token: string,
  data: { problem_id: string; language: string; code: string }
): Promise<Submission> {
  return apiRequest<Submission>(
    "/api/v1/submissions/submit",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
    token
  );
}

export async function fetchSubmissionsForProblem(
  token: string,
  problemId: string,
  page = 1,
  pageSize = 10
): Promise<SubmissionPaginatedResponse> {
  return apiRequest<SubmissionPaginatedResponse>(
    `/api/v1/submissions/problem/${problemId}?page=${page}&page_size=${pageSize}`,
    {},
    token
  );
}

export async function unlockNextHint(token: string, problemId: string): Promise<Hint> {
  return apiRequest<Hint>(`/api/v1/problems/${problemId}/hints/unlock`, { method: "POST" }, token);
}

export async function toggleBookmark(
  token: string,
  problemId: string,
  isBookmarked: boolean
): Promise<{ message: string; is_bookmarked: boolean }> {
  return apiRequest(
    `/api/v1/problems/${problemId}/bookmark`,
    {
      method: "PATCH",
      body: JSON.stringify({ is_bookmarked: isBookmarked }),
    },
    token
  );
}

export async function updateNotes(
  token: string,
  problemId: string,
  notes: string
): Promise<{ message: string; personal_notes: string }> {
  return apiRequest(
    `/api/v1/problems/${problemId}/notes`,
    {
      method: "PATCH",
      body: JSON.stringify({ personal_notes: notes }),
    },
    token
  );
}

export async function completeOnboarding(
  token: string,
  data: {
    target_company_ids: string[];
    primary_company_id: string;
    preferred_language: string;
    skill_level: string;
    daily_goal_minutes: number;
  }
): Promise<User> {
  return apiRequest<User>(
    "/api/v1/users/onboarding",
    {
      method: "PATCH",
      body: JSON.stringify(data),
    },
    token
  );
}
