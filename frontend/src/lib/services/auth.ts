import { apiFetch } from "../api-client";

export const authService = {
  login: async (login: string, password: string): Promise<boolean> => {
    try {
      const res = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ login, password }),
      });
      const data = await res.json();
      localStorage.setItem("safina_token", data.access_token);
      localStorage.setItem("safina_role", data.role ?? "user");
      localStorage.setItem("safina_user", login);
      localStorage.setItem("safina_team", data.team ?? "");
      if (data.projectId) localStorage.setItem("safina_projectId", data.projectId);
      return true;
    } catch {
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem("safina_token");
    localStorage.removeItem("safina_role");
    localStorage.removeItem("safina_user");
    localStorage.removeItem("safina_team");
    localStorage.removeItem("safina_projectId");
  },
};
