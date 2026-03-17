import { apiFetch } from "../api-client";

export const analyticsService = {
  getAnalytics: async ({ period = "1m", segment = "global" } = {}) => {
    const res = await apiFetch(`/analytics?period=${period}&segment=${segment}`);
    return await res.json();
  },
};
