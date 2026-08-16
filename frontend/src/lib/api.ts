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

export interface AIHintResponse {
  hint_text: string;
  hint_level: number;
  should_reveal_solution: boolean;
  focus_concept?: string;
}

export interface UserAIHintItem {
  id: string;
  hint_level: number;
  language: string;
  hint_text: string;
  focus_concept?: string;
  created_at: string;
}

export interface UserAIHintHistoryResponse {
  items: UserAIHintItem[];
  hints_unlocked: number;
  max_hints: number;
}

export interface AICodeReviewResponse {
  summary: string;
  correctness_assessment: string;
  time_complexity: string;
  space_complexity: string;
  strengths: string[];
  improvements: string[];
  bugs: string[];
  suggestions: string[];
  judge0_status?: string;
}

export interface UserAICodeReviewDetailResponse {
  id: string;
  problem_id: string;
  language: string;
  summary: string;
  correctness_assessment: string;
  time_complexity: string;
  space_complexity: string;
  strengths: string[];
  improvements: string[];
  bugs: string[];
  suggestions: string[];
  judge0_status?: string;
  created_at: string;
}

export interface TopicBreakdownItem {
  topic_id: string;
  topic_name: string;
  available: number;
  attempted: number;
  solved: number;
  solve_rate: number;
  coverage_pct: number;
  status: "NOT_STARTED" | "NEEDS_PRACTICE" | "DEVELOPING" | "STRONG";
}

export interface DifficultyBreakdownItem {
  difficulty: "EASY" | "MEDIUM" | "HARD";
  available: number;
  attempted: number;
  solved: number;
  solve_rate: number;
}

export interface CoverageMetrics {
  overall: number;
  topics: number;
  difficulty: number;
}

export interface ProblemCounts {
  available: number;
  attempted: number;
  solved: number;
}

export interface CompanyInfo {
  id: string;
  name: string;
  slug: string;
}

export interface CompanyPreparationResponse {
  company: CompanyInfo;
  preparation_score?: number | null;
  status: "INSUFFICIENT_DATA" | "STARTING" | "DEVELOPING" | "WELL_PREPARED";
  confidence_message: string;
  coverage: CoverageMetrics;
  problems: ProblemCounts;
  topic_breakdown: TopicBreakdownItem[];
  difficulty_breakdown: DifficultyBreakdownItem[];
  strengths: string[];
  focus_areas: string[];
  recommended_next_steps: string[];
  ai_explanation?: string | null;
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

export interface RecommendationItem {
  problem: ProblemListItem;
  reason: string;
  reason_type: string;
  score: number;
}

export interface RecommendationListResponse {
  items: RecommendationItem[];
  focus_topics: string[];
  source: string;
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

// Mock Test Types
export interface MockTestCatalogItem {
  id: string;
  company_id: string;
  company_name: string;
  company_slug: string;
  title: string;
  description?: string;
  duration_minutes: number;
  problem_count: number;
  total_points: number;
  user_last_status?: string;
  user_last_score?: number;
}

export interface MockTestProblemItem {
  problem_id: string;
  title: string;
  slug: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  category: string;
  order_index: number;
  weight_score: number;
  user_status: "UNATTEMPTED" | "ATTEMPTED" | "SOLVED";
  score_obtained: number;
  code_draft?: string;
}

export interface UserMockTestSessionResponse {
  session_id: string;
  mock_test_id: string;
  title: string;
  company_name: string;
  company_slug: string;
  duration_minutes: number;
  started_at: string;
  expires_at: string;
  remaining_seconds: number;
  status: "IN_PROGRESS" | "SUBMITTED" | "AUTO_SUBMITTED" | "TIMED_OUT" | "COMPLETED";
  total_score: number;
  max_possible_score: number;
  problems: MockTestProblemItem[];
}

export interface SubmitMockProblemResponse {
  submission_id: string;
  status: string;
  passed_test_cases: number;
  total_test_cases: number;
  score_obtained: number;
  execution_time_ms?: number;
  memory_kb?: number;
  error_output?: string;
}

export interface MockTestResultProblemDetail {
  problem_id: string;
  title: string;
  slug: string;
  difficulty: string;
  order_index: number;
  weight_score: number;
  score_obtained: number;
  status: string;
  passed_test_cases: number;
  total_test_cases: number;
}

export interface MockTestTopicPerformance {
  topic_id: string;
  topic_name: string;
  problems_count: number;
  solved_count: number;
  status: "STRONG" | "NEEDS_PRACTICE";
}

export interface MockTestDifficultyPerformance {
  difficulty: string;
  problems_count: number;
  solved_count: number;
}

export interface MockTestResultResponse {
  session_id: string;
  mock_test_id: string;
  title: string;
  company_name: string;
  status: string;
  score: number;
  total_points: number;
  percentage: number;
  time_taken_seconds: number;
  started_at: string;
  completed_at?: string;
  problems: MockTestResultProblemDetail[];
  topic_breakdown: MockTestTopicPerformance[];
  difficulty_breakdown: MockTestDifficultyPerformance[];
  recommended_next_steps: string[];
  ai_explanation?: string;
}

export interface MockTestHistoryItem {
  session_id: string;
  mock_test_id: string;
  title: string;
  company_name: string;
  company_slug: string;
  status: string;
  score: number;
  total_points: number;
  percentage: number;
  completed_at?: string;
}

// Admin Schemas
export interface AdminDashboardSummary {
  companies_count: number;
  topics_count: number;
  problems_count: number;
  active_problems_count: number;
  mock_tests_count: number;
  total_test_cases: number;
  total_hints: number;
}

export interface AuditLogItem {
  id: string;
  user_id?: string;
  user_email?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface AuditLogPaginatedResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Gamification Schemas
export interface DailyActivityResponse {
  activity_date: string;
  minutes_practiced: number;
  problems_attempted: number;
  problems_solved: number;
  mock_tests_completed: number;
  xp_earned: number;
  goal_minutes: number;
  goal_completed: boolean;
}

export interface UserGamificationResponse {
  user_id: string;
  total_xp: number;
  current_level: number;
  xp_for_current_level: number;
  xp_for_next_level: number;
  level_progress_pct: number;
  current_streak: number;
  longest_streak: number;
  last_activity_date?: string;
  leaderboard_opt_in: boolean;
  display_name?: string;
  today_activity?: DailyActivityResponse;
  total_badges: number;
  unlocked_badges_count: number;
}

export interface BadgeItem {
  id: string;
  slug: string;
  name: string;
  description: string;
  category: string;
  icon_name: string;
  xp_reward: number;
  is_unlocked: boolean;
  awarded_at?: string;
}


export interface XPTransactionItem {
  id: string;
  amount: number;
  reason: string;
  reference_type: string;
  reference_id: string;
  created_at: string;
}

export interface XPTransactionPaginatedResponse {
  items: XPTransactionItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LeaderboardItem {
  rank: number;
  user_id: string;
  display_name: string;
  level: number;
  weekly_xp: number;
  total_xp: number;
  is_current_user: boolean;
}

export interface LeaderboardResponse {
  items: LeaderboardItem[];
  user_rank?: number;
  period: string;
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
    credentials: "include",
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

export async function fetchRecommendations(
  token: string,
  limit = 5
): Promise<RecommendationListResponse> {
  return apiRequest<RecommendationListResponse>(`/api/v1/recommendations?limit=${limit}`, {}, token);
}

export async function fetchCompanyPreparation(
  token: string,
  companyId: string
): Promise<CompanyPreparationResponse> {
  return apiRequest<CompanyPreparationResponse>(`/api/v1/companies/${companyId}/preparation`, {}, token);
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

// Mock Test Client API Functions
export async function fetchMockTestCatalog(token: string): Promise<MockTestCatalogItem[]> {
  return apiRequest<MockTestCatalogItem[]>("/api/v1/mock-tests", {}, token);
}

export async function startMockTestSession(token: string, mockTestId: string): Promise<UserMockTestSessionResponse> {
  return apiRequest<UserMockTestSessionResponse>(`/api/v1/mock-tests/${mockTestId}/start`, { method: "POST" }, token);
}

export async function fetchActiveMockTestSession(token: string, sessionId: string): Promise<UserMockTestSessionResponse> {
  return apiRequest<UserMockTestSessionResponse>(`/api/v1/mock-tests/sessions/${sessionId}`, {}, token);
}

export async function runMockProblemSample(
  token: string,
  sessionId: string,
  problemId: string,
  language: string,
  code: string
): Promise<BatchExecutionResult> {
  return apiRequest<BatchExecutionResult>(
    `/api/v1/mock-tests/sessions/${sessionId}/problems/${problemId}/run-sample`,
    {
      method: "POST",
      body: JSON.stringify({ language, code }),
    },
    token
  );
}

export async function submitMockProblemSolution(
  token: string,
  sessionId: string,
  problemId: string,
  language: string,
  code: string
): Promise<SubmitMockProblemResponse> {
  return apiRequest<SubmitMockProblemResponse>(
    `/api/v1/mock-tests/sessions/${sessionId}/problems/${problemId}/submit`,
    {
      method: "POST",
      body: JSON.stringify({ language, code }),
    },
    token
  );
}

export async function submitCompleteMockTest(token: string, sessionId: string): Promise<MockTestResultResponse> {
  return apiRequest<MockTestResultResponse>(`/api/v1/mock-tests/sessions/${sessionId}/submit`, { method: "POST" }, token);
}

export async function fetchMockTestResult(token: string, sessionId: string): Promise<MockTestResultResponse> {
  return apiRequest<MockTestResultResponse>(`/api/v1/mock-tests/sessions/${sessionId}/result`, {}, token);
}

export async function fetchMockTestHistory(token: string): Promise<MockTestHistoryItem[]> {
  return apiRequest<MockTestHistoryItem[]>("/api/v1/mock-tests/history", {}, token);
}

// Admin API Functions
export async function fetchAdminDashboardSummary(token: string): Promise<AdminDashboardSummary> {
  return apiRequest<AdminDashboardSummary>("/api/v1/admin/dashboard", {}, token);
}

export async function fetchAdminCompanies(token: string): Promise<any[]> {
  return apiRequest<any[]>("/api/v1/admin/companies", {}, token);
}

export async function createAdminCompany(token: string, data: any): Promise<any> {
  return apiRequest<any>("/api/v1/admin/companies", { method: "POST", body: JSON.stringify(data) }, token);
}

export async function updateAdminCompany(token: string, id: string, data: any): Promise<any> {
  return apiRequest<any>(`/api/v1/admin/companies/${id}`, { method: "PATCH", body: JSON.stringify(data) }, token);
}

export async function fetchAdminTopics(token: string): Promise<any[]> {
  return apiRequest<any[]>("/api/v1/admin/topics", {}, token);
}

export async function createAdminTopic(token: string, data: any): Promise<any> {
  return apiRequest<any>("/api/v1/admin/topics", { method: "POST", body: JSON.stringify(data) }, token);
}

export async function updateAdminTopic(token: string, id: string, data: any): Promise<any> {
  return apiRequest<any>(`/api/v1/admin/topics/${id}`, { method: "PATCH", body: JSON.stringify(data) }, token);
}

export async function fetchAdminProblems(token: string, params: { page?: number; page_size?: number; search?: string; difficulty?: string } = {}): Promise<any> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", params.page.toString());
  if (params.page_size) query.set("page_size", params.page_size.toString());
  if (params.search) query.set("search", params.search);
  if (params.difficulty) query.set("difficulty", params.difficulty);

  return apiRequest<any>(`/api/v1/admin/problems?${query.toString()}`, {}, token);
}

export async function createAdminProblem(token: string, data: any): Promise<any> {
  return apiRequest<any>("/api/v1/admin/problems", { method: "POST", body: JSON.stringify(data) }, token);
}

export async function fetchAdminProblemDetail(token: string, id: string): Promise<any> {
  return apiRequest<any>(`/api/v1/admin/problems/${id}`, {}, token);
}

export async function updateAdminProblem(token: string, id: string, data: any): Promise<any> {
  return apiRequest<any>(`/api/v1/admin/problems/${id}`, { method: "PATCH", body: JSON.stringify(data) }, token);
}

export async function deactivateAdminProblem(token: string, id: string): Promise<any> {
  return apiRequest<any>(`/api/v1/admin/problems/${id}`, { method: "DELETE" }, token);
}

export async function createAdminTestCase(token: string, problemId: string, data: any): Promise<any> {
  return apiRequest<any>(`/api/v1/admin/problems/${problemId}/test-cases`, { method: "POST", body: JSON.stringify(data) }, token);
}

export async function deleteAdminTestCase(token: string, testCaseId: string): Promise<any> {
  return apiRequest<any>(`/api/v1/admin/test-cases/${testCaseId}`, { method: "DELETE" }, token);
}

export async function createAdminHint(token: string, problemId: string, data: any): Promise<any> {
  return apiRequest<any>(`/api/v1/admin/problems/${problemId}/hints`, { method: "POST", body: JSON.stringify(data) }, token);
}

export async function deleteAdminHint(token: string, hintId: string): Promise<any> {
  return apiRequest<any>(`/api/v1/admin/hints/${hintId}`, { method: "DELETE" }, token);
}

export async function fetchAdminMockTests(token: string): Promise<any[]> {
  return apiRequest<any[]>("/api/v1/admin/mock-tests", {}, token);
}

export async function createAdminMockTest(token: string, data: any): Promise<any> {
  return apiRequest<any>("/api/v1/admin/mock-tests", { method: "POST", body: JSON.stringify(data) }, token);
}

export async function fetchAdminAuditLogs(token: string, page = 1, pageSize = 20): Promise<AuditLogPaginatedResponse> {
  return apiRequest<AuditLogPaginatedResponse>(`/api/v1/admin/audit-logs?page=${page}&page_size=${pageSize}`, {}, token);
}

// Gamification API Functions
export async function fetchMyGamification(token: string): Promise<UserGamificationResponse> {
  return apiRequest<UserGamificationResponse>("/api/v1/gamification/me", {}, token);
}

export async function updateGamificationPreferences(
  token: string,
  data: { leaderboard_opt_in?: boolean; display_name?: string }
): Promise<any> {
  return apiRequest<any>("/api/v1/gamification/preferences", { method: "PATCH", body: JSON.stringify(data) }, token);
}

export async function fetchBadges(token: string): Promise<BadgeItem[]> {
  return apiRequest<BadgeItem[]>("/api/v1/gamification/badges", {}, token);
}

export async function fetchXPHistory(token: string, page = 1, pageSize = 20): Promise<XPTransactionPaginatedResponse> {
  return apiRequest<XPTransactionPaginatedResponse>(`/api/v1/gamification/xp-history?page=${page}&page_size=${pageSize}`, {}, token);
}

export async function fetchLeaderboard(token: string, limit = 50): Promise<LeaderboardResponse> {
  return apiRequest<LeaderboardResponse>(`/api/v1/leaderboard?limit=${limit}`, {}, token);
}

export async function unlockNextHint(token: string, problemId: string): Promise<Hint> {
  return apiRequest<Hint>(`/api/v1/problems/${problemId}/hints/unlock`, { method: "POST" }, token);
}

export async function fetchAIHintsHistory(
  token: string,
  problemId: string
): Promise<UserAIHintHistoryResponse> {
  return apiRequest<UserAIHintHistoryResponse>(`/api/v1/ai/hints/${problemId}`, {}, token);
}

export async function generateAIHint(
  token: string,
  data: { problem_id: string; language: string; source_code?: string }
): Promise<AIHintResponse> {
  return apiRequest<AIHintResponse>(
    "/api/v1/ai/hints",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
    token
  );
}

export async function fetchLatestAICodeReview(
  token: string,
  problemId: string
): Promise<UserAICodeReviewDetailResponse | null> {
  return apiRequest<UserAICodeReviewDetailResponse | null>(
    `/api/v1/ai/code-review/${problemId}`,
    {},
    token
  );
}

export async function generateAICodeReview(
  token: string,
  data: { problem_id: string; language: string; source_code: string }
): Promise<AICodeReviewResponse> {
  return apiRequest<AICodeReviewResponse>(
    "/api/v1/ai/code-review",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
    token
  );
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
