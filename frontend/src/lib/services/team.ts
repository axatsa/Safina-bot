import { apiFetch } from "../api-client";
import { TeamMember } from "../types";

function mapMember(m: any): TeamMember {
  return {
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
    branch: m.branch,
    team: m.team,
    status: m.status,
    telegramChatId: m.telegram_chat_id,
    templates: m.templates || [],
    createdAt: m.created_at
  };
}

export const teamService = {
  getTeam: async (): Promise<TeamMember[]> => {
    const res = await apiFetch("/team");
    const data = await res.json();
    if (!Array.isArray(data)) {
      console.error("Expected array from /api/team, got:", data);
      return [];
    }
    return data.map(mapMember);
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
        position: member.position,
        branch: member.branch,
        team: member.team
      }),
    });
    const data = await res.json();
    return mapMember(data);
  },

  deleteTeamMember: async (id: string) => {
    await apiFetch(`/team/${id}`, { method: "DELETE" });
  },

  updateTeamMemberTemplates: async (memberId: string, templates: string[]) => {
    const res = await apiFetch(`/team/${memberId}/templates`, {
      method: "PATCH",
      body: JSON.stringify({ templates }),
    });
    return mapMember(await res.json());
  },

  updateTeamMember: async (memberId: string, data: {
    lastName?: string;
    firstName?: string;
    position?: string;
    branch?: string;
    team?: string;
    login?: string;
    password?: string;
    projectIds?: string[];
    templates?: string[];
  }): Promise<TeamMember> => {
    const body: any = {};
    if (data.lastName   !== undefined) body.last_name   = data.lastName;
    if (data.firstName  !== undefined) body.first_name  = data.firstName;
    if (data.position   !== undefined) body.position     = data.position;
    if (data.branch     !== undefined) body.branch       = data.branch;
    if (data.team       !== undefined) body.team         = data.team;
    if (data.login      !== undefined) body.login        = data.login;
    if (data.password   !== undefined) body.password     = data.password;
    if (data.projectIds !== undefined) body.project_ids  = data.projectIds;
    if (data.templates  !== undefined) body.templates    = data.templates;
    const res = await apiFetch(`/team/${memberId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    return mapMember(await res.json());
  },
};
