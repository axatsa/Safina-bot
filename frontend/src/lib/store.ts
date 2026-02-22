import { ExpenseRequest, ExpenseStatus, Project, TeamMember } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

const getHeaders = () => {
  const token = localStorage.getItem("safina_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export const store = {
  // Auth
  login: async (login: string, password: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login, password }),
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("safina_token", data.access_token);
        localStorage.setItem("safina_role", data.role);
        if (data.projectId) localStorage.setItem("safina_projectId", data.projectId);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem("safina_token");
    localStorage.removeItem("safina_role");
    localStorage.removeItem("safina_projectId");
  },

  isAdmin: (): boolean => localStorage.getItem("safina_role") === "admin",

  // Projects
  getProjects: async (): Promise<Project[]> => {
    const res = await fetch(`${API_BASE_URL}/projects`, { headers: getHeaders() });
    return res.json();
  },

  createProject: async (project: { name: string; code: string }): Promise<Project> => {
    const res = await fetch(`${API_BASE_URL}/projects`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(project),
    });
    return res.json();
  },

  // Team
  getTeam: async (): Promise<TeamMember[]> => {
    const res = await fetch(`${API_BASE_URL}/team`, { headers: getHeaders() });
    return res.json();
  },

  createTeamMember: async (member: any): Promise<TeamMember> => {
    const res = await fetch(`${API_BASE_URL}/team`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        last_name: member.lastName,
        first_name: member.firstName,
        project_id: member.projectId,
        login: member.login,
        password: member.password
      }),
    });
    return res.json();
  },

  // Expenses
  getExpenses: async (params?: { project?: string; status?: string }): Promise<ExpenseRequest[]> => {
    const url = new URL(`${API_BASE_URL}/expenses`);
    if (params?.project) url.searchParams.append("project", params.project);
    if (params?.status) url.searchParams.append("status", params.status);

    const res = await fetch(url.toString(), { headers: getHeaders() });
    const data = await res.json();
    return data.map((e: any) => ({
      ...e,
      date: new Date(e.date),
      createdAt: new Date(e.createdAt),
    }));
  },

  updateExpenseStatus: async (expenseId: string, status: ExpenseStatus, comment?: string): Promise<ExpenseRequest> => {
    const res = await fetch(`${API_BASE_URL}/expenses/${expenseId}/status`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify({ status, comment }),
    });
    return res.json();
  },

  updateInternalComment: async (expenseId: string, internalComment: string): Promise<void> => {
    await fetch(`${API_BASE_URL}/expenses/${expenseId}/comment`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify({ internal_comment: internalComment }),
    });
  },

  exportCSV: async (params: { project?: string; from?: string; to?: string; allStatuses?: boolean }): Promise<void> => {
    const url = new URL(`${API_BASE_URL}/expenses/export`);
    if (params.project && params.project !== "all") url.searchParams.append("project", params.project);
    if (params.from) url.searchParams.append("from_date", params.from);
    if (params.to) url.searchParams.append("to_date", params.to);
    if (params.allStatuses) url.searchParams.append("allStatuses", "true");

    window.open(url.toString(), "_blank");
  }
};
