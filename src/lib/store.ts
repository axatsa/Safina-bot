import { ExpenseRequest, ExpenseStatus, Project, TeamMember } from "./types";

const API_BASE_URL = import.meta.env.VITE_APP_API_URL || "/api";

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
    const data = await res.json();
    return data.map((p: any) => ({
      ...p,
      createdAt: p.created_at,
      members: (p.members || []).map((m: any) => ({
        id: m.id,
        lastName: m.last_name,
        firstName: m.first_name,
        position: m.position
      }))
    }));
  },

  createProject: async (project: { name: string; code: string }): Promise<Project> => {
    const res = await fetch(`${API_BASE_URL}/projects`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(project),
    });
    const data = await res.json();
    return {
      ...data,
      createdAt: data.created_at
    };
  },

  // Team
  getTeam: async (): Promise<TeamMember[]> => {
    const res = await fetch(`${API_BASE_URL}/team`, { headers: getHeaders() });
    const data = await res.json();
    return data.map((m: any) => ({
      id: m.id,
      lastName: m.last_name,
      firstName: m.first_name,
      projectIds: (m.projects || []).map((p: any) => p.id),
      projects: (m.projects || []).map((p: any) => ({
        ...p,
        createdAt: new Date(p.created_at)
      })),
      login: m.login,
      position: m.position,
      status: m.status,
      telegramChatId: m.telegram_chat_id,
      createdAt: m.created_at
    }));
  },

  createTeamMember: async (member: any): Promise<TeamMember> => {
    const res = await fetch(`${API_BASE_URL}/team`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        last_name: member.lastName,
        first_name: member.firstName,
        project_ids: member.projectIds,
        login: member.login,
        password: member.password,
        position: member.position
      }),
    });
    const data = await res.json();
    return {
      id: data.id,
      lastName: data.last_name,
      firstName: data.first_name,
      projectIds: (data.projects || []).map((p: any) => p.id),
      projects: (data.projects || []).map((p: any) => ({
        ...p,
        createdAt: new Date(p.created_at)
      })),
      login: data.login,
      position: data.position,
      status: data.status,
      telegramChatId: data.telegram_chat_id,
      createdAt: data.created_at
    };
  },

  async deleteTeamMember(id: string) {
    await fetch(`${API_BASE_URL}/team/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
  },

  async deleteProject(id: string) {
    await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
  },

  async getProjectsByChatId(chatId: string) {
    const res = await fetch(`${API_BASE_URL}/projects/by-chat-id/${chatId}`);
    if (!res.ok) throw new Error("Failed to load projects");
    return await res.json();
  },

  async submitExpenseFromWeb(data: any) {
    const res = await fetch(`${API_BASE_URL}/expenses/web-submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Submission failed");
    return await res.json();
  },

  async createExpenseRequest(data: any) {
    const res = await fetch(`${API_BASE_URL}/expenses`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Submission failed");
    return await res.json();
  },

  // Expenses
  getExpenses: async (params?: { project?: string; status?: string }): Promise<ExpenseRequest[]> => {
    const url = new URL(`${API_BASE_URL}/expenses`, window.location.origin);
    if (params?.project) url.searchParams.append("project", params.project);
    if (params?.status) url.searchParams.append("status", params.status);

    const res = await fetch(url.toString(), { headers: getHeaders() });
    const data = await res.json();
    return data.map((e: any) => ({
      id: e.id,
      requestId: e.request_id,
      purpose: e.purpose,
      items: e.items,
      totalAmount: e.total_amount,
      currency: e.currency,
      projectId: e.project_id,
      projectName: e.project_name,
      projectCode: e.project_code,
      status: e.status,
      statusComment: e.status_comment,
      internalComment: e.internal_comment,
      createdBy: e.created_by,
      createdById: e.created_by_id,
      date: new Date(e.date),
      createdAt: new Date(e.created_at),
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
    const url = new URL(`${API_BASE_URL}/expenses/export`, window.location.origin);
    if (params.project && params.project !== "all") url.searchParams.append("project", params.project);
    if (params.from) url.searchParams.append("from_date", params.from);
    if (params.to) url.searchParams.append("to_date", params.to);
    if (params.allStatuses) url.searchParams.append("allStatuses", "true");

    const res = await fetch(url.toString(), { headers: getHeaders() });
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', 'expenses_export.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  async addProjectMember(projectId: string, memberId: string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/members/${memberId}`, {
      method: "POST",
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to add member");
  },

  async removeProjectMember(projectId: string, memberId: string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/members/${memberId}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to remove member");
  },

  exportDocx: async (expenseId: string) => {
    const res = await fetch(`${API_BASE_URL}/expenses/${expenseId}/export-docx`, { headers: getHeaders() });
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', `smeta_${expenseId}.docx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
};
