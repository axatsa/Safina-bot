import { apiFetch } from "../api-client";
import { Project, Branch } from "../types";

const normalizeBranch = (b: any): Branch => {
  if (typeof b === "string") {
    return {
      id: b,
      name: b,
      code: "",
      project_id: ""
    };
  }
  return {
    ...b,
    id: b.id || b.Id || b.ID || b._id || b.project_id || b.name,
    name: b.name || b.Name || b.Name_ || b.branch_name || "Без названия",
    code: b.code || b.Code || b.branch_code || "",
    projectId: b.project_id || b.projectId || b.branch_id || "",
    project_id: b.project_id || b.projectId || b.branch_id || "",
  };
};

const mapProject = (p: any): Project => ({
  ...p,
  createdAt: p.created_at,
  members: (p.members || []).map((m: any) => ({
    id: m.id,
    lastName: m.last_name,
    firstName: m.first_name,
    position: m.position
  })),
  branches: (p.branches || []).map(normalizeBranch)
});

export const projectsService = {
  getProjects: async (category?: string): Promise<Project[]> => {
    const url = category ? `/projects?category=${category}` : "/projects";
    const res = await apiFetch(url);
    const data = await res.json();
    return data.map(mapProject);
  },

  createProject: async (project: { name: string; code: string; category: string }): Promise<Project> => {
    const res = await apiFetch("/projects", {
      method: "POST",
      body: JSON.stringify(project),
    });
    const data = await res.json();
    return mapProject(data);
  },

  deleteProject: async (id: string) => {
    await apiFetch(`/projects/${id}`, { method: "DELETE" });
  },

  // Branches
  getBranches: async (projectId: string): Promise<Branch[]> => {
    const res = await apiFetch(`/projects/${projectId}/branches`);
    const data = await res.json();
    return data.map(normalizeBranch);
  },

  createBranch: async (projectId: string, branch: { name: string }): Promise<Branch> => {
    const res = await apiFetch(`/projects/${projectId}/branches`, {
      method: "POST",
      body: JSON.stringify(branch),
    });
    const data = await res.json();
    return normalizeBranch(data);
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
    return mapProject(await res.json());
  },
};
