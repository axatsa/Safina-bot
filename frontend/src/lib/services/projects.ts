import { apiFetch } from "../api-client";
import { Project, Branch } from "../types";

export const projectsService = {
  getProjects: async (category?: string): Promise<Project[]> => {
    const url = category ? `/projects?category=${category}` : "/projects";
    const res = await apiFetch(url);
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

  createProject: async (project: { name: string; code: string; category: string }): Promise<Project> => {
    const res = await apiFetch("/projects", {
      method: "POST",
      body: JSON.stringify(project),
    });
    const data = await res.json();
    return {
      ...data,
      createdAt: data.created_at
    };
  },

  deleteProject: async (id: string) => {
    await apiFetch(`/projects/${id}`, { method: "DELETE" });
  },

  // Branches
  getBranches: async (projectId: string): Promise<Branch[]> => {
    const res = await apiFetch(`/projects/${projectId}/branches`);
    return await res.json();
  },

  createBranch: async (projectId: string, branch: { name: string }): Promise<Branch> => {
    const res = await apiFetch(`/projects/${projectId}/branches`, {
      method: "POST",
      body: JSON.stringify(branch),
    });
    return await res.json();
  },

  deleteBranch: async (branchId: string) => {
    await apiFetch(`/projects/branches/${branchId}`, { method: "DELETE" });
  },

  addProjectMember: async (projectId: string, memberId: string) => {
    await apiFetch(`/projects/${projectId}/members/${memberId}`, { method: "POST" });
  },

  removeProjectMember: async (projectId: string, memberId: string) => {
    await apiFetch(`/projects/${projectId}/members/${memberId}`, { method: "DELETE" });
  },

  getProjectsByChatId: async (chatId: string) => {
    const res = await apiFetch(`/projects/by-chat-id/${chatId}`);
    return await res.json();
  },
  
  updateProjectTemplates: async (projectId: string, templates: string[]) => {
    const res = await apiFetch(`/projects/${projectId}/templates`, {
      method: "PATCH",
      body: JSON.stringify({ templates }),
    });
    return await res.json();
  },
};
