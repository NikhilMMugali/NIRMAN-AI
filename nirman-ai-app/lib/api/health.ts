import { apiClient } from "./client";
import type { HealthResponse } from "./types";

export async function getHealthCheck(): Promise<HealthResponse> {
  return apiClient.getHealth();
}
