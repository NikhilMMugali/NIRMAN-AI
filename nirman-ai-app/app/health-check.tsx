"use client";

import { useEffect, useState } from "react";
import { getHealthCheck } from "@/lib/api/health";
import type { HealthStatus } from "@/lib/api/types";

export function HealthCheck() {
  const [state, setState] = useState<HealthStatus>({ state: "idle" });

  useEffect(() => {
    let isMounted = true;

    async function fetchHealth() {
      setState({ state: "loading", message: "Checking API connection..." });

      try {
        const data = await getHealthCheck();
        if (!isMounted) return;
        setState({ state: "success", data, message: "API is reachable." });
      } catch (error) {
        if (!isMounted) return;
        setState({
          state: "error",
          message: error instanceof Error ? error.message : "API unavailable.",
        });
      }
    }

    fetchHealth();
    return () => {
      isMounted = false;
    };
  }, []);

  if (state.state === "loading") {
    return <div className="health-status loading">Checking API connection…</div>;
  }

  if (state.state === "error") {
    return <div className="health-status error">API unavailable: {state.message}</div>;
  }

  if (state.state === "success" && state.data) {
    return (
      <div className="health-status success">
        API status: {state.data.status} — {state.data.service}
      </div>
    );
  }

  return <div className="health-status idle">API status pending.</div>;
}
