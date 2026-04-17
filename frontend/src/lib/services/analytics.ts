import { apiFetch } from "../api-client";

export const analyticsService = {
  getAnalytics: async ({ period = "1m", segment = "global", type = "all", branch = undefined, branchNames = [] as string[], projectIds = [] as string[] } = {}) => {
    const params = new URLSearchParams({ period, segment, type });
    if (branch) params.append("branch", branch);
    if (branchNames && branchNames.length > 0) {
      branchNames.forEach(name => params.append("branch_names", name));
    }
    if (projectIds && projectIds.length > 0) {
      projectIds.forEach(id => params.append("project_ids", id));
    }
    const res = await apiFetch(`/analytics?${params.toString()}`);
    return await res.json();
  },
  getAnalyticsBranches: async () => {
    const res = await apiFetch("/analytics/branches");
    return await res.json();
  },
};
