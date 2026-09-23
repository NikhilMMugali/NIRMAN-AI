const DEFAULT_TIMEOUT_MS = 10000;

export type ApiErrorShape = {
  success?: boolean;
  error?: {
    code?: number;
    message?: string;
  };
};

class ApiClient {
  private baseUrl: string;
  private timeoutMs: number;

  constructor(baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000", timeoutMs = DEFAULT_TIMEOUT_MS) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.timeoutMs = timeoutMs;
  }


  private async request<T>(path: string): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as ApiErrorShape;
        const message = payload?.error?.message ?? "Request failed";
        throw new Error(message);
      }

      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("Request timeout.");
      }

      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async getHealth(): Promise<{ status: string; service: string }> {
    return this.request<{ status: string; service: string }>("/api/v1/health");
  }

  async getProjects(limit = 100): Promise<{ success: boolean; count: number; data: any[] }> {
    return this.request<{ success: boolean; count: number; data: any[] }>(`/api/v1/projects?limit=${limit}`);
  }

  async getProject(projectId: string): Promise<{ success: boolean; data: any }> {
    return this.request<{ success: boolean; data: any }>(`/api/v1/projects/${encodeURIComponent(projectId)}`);
  }

  async getProjectRisk(projectId: string): Promise<{ success: boolean; data: any }> {
    return this.request<{ success: boolean; data: any }>(`/api/v1/projects/${encodeURIComponent(projectId)}/risk`);
  }

  async getProjectDrivers(projectId: string): Promise<{ success: boolean; count: number; data: any[] }> {
    return this.request<{ success: boolean; count: number; data: any[] }>(`/api/v1/projects/${encodeURIComponent(projectId)}/drivers`);
  }

  async getProjectRecommendations(projectId: string): Promise<{ success: boolean; data: any }> {
    return this.request<{ success: boolean; data: any }>(`/api/v1/projects/${encodeURIComponent(projectId)}/recommendations`);
  }

  async getProjectAssessment(projectId: string): Promise<{ success: boolean; data: any }> {
    return this.request<{ success: boolean; data: any }>(`/api/v1/projects/${encodeURIComponent(projectId)}/assessment`);
  }



  async getAnalyticsSummary(): Promise<{ success: boolean; data: any }> {
    return this.request<{ success: boolean; data: any }>("/api/v1/analytics/summary");
  }

  async getStateIntelligence(): Promise<{ success: boolean; count: number; data: any[] }> {
    return this.request<{ success: boolean; count: number; data: any[] }>("/api/v1/intelligence/states");
  }

  async getSectorIntelligence(): Promise<{ success: boolean; count: number; data: any[] }> {
    return this.request<{ success: boolean; count: number; data: any[] }>("/api/v1/intelligence/sectors");
  }
}

export const apiClient = new ApiClient();
export default ApiClient;

