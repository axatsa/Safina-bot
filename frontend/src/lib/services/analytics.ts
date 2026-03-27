import { apiFetch } from "../api-client";

export const analyticsService = {
  getAnalytics: async ({ period = "1m", segment = "global", type = "all" } = {}) => {
    const res = await apiFetch(`/analytics?period=${period}&segment=${segment}&type=${type}`);
    return await res.json();
  },
};
