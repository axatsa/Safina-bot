import { apiFetch } from "../api-client";

export const analyticsService = {
  getAnalytics: async ({ period = "1m", segment = "global", type = "all", branch = undefined } = {}) => {
    const params = new URLSearchParams({ period, segment, type });
    if (branch) params.append("branch", branch);
    const res = await apiFetch(`/analytics?${params.toString()}`);
    return await res.json();
  },
  getBranches: async () => {
    const res = await apiFetch("/analytics/branches");
    return await res.json();
  },
};
