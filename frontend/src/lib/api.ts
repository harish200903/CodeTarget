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
