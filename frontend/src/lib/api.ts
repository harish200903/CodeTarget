const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
