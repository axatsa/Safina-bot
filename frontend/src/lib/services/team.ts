import { apiFetch } from "../api-client";
import { TeamMember } from "../types";

export const teamService = {
  getTeam: async (): Promise<TeamMember[]> => {
    const res = await apiFetch("/team");
    const data = await res.json();
    if (!Array.isArray(data)) {
      console.error("Expected array from /api/team, got:", data);
      return [];
    }
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
    const res = await apiFetch("/team", {
      method: "POST",
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

  deleteTeamMember: async (id: string) => {
    await apiFetch(`/team/${id}`, { method: "DELETE" });
  },

  updateTeamMemberTemplates: async (memberId: string, templates: string[]) => {
    const res = await apiFetch(`/team/${memberId}/templates`, {
      method: "PATCH",
      body: JSON.stringify({ templates }),
    });
    return await res.json();
  },
};
