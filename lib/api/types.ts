export type HealthResponse = {
  status: string;
  service: string;
};

export type ApiState = "idle" | "loading" | "success" | "error" | "empty";

export type HealthStatus = {
  state: ApiState;
  message?: string;
  data?: HealthResponse;
};
