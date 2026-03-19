import { UserRole } from "./types";

export const getRole = (): UserRole =>
  (localStorage.getItem("safina_role") as UserRole) ?? "user";

export const getUser = (): string =>
  localStorage.getItem("safina_user") ?? "";

export const getTeam = (): string =>
    localStorage.getItem("safina_team") ?? "";

export const rbac = {
  isAdmin: () => {
    const token = localStorage.getItem("safina_token");
    if (!token) return false;
    const team = getTeam();
    const login = getUser().toLowerCase();
    return login === "safina" || login === "farrukh" || team === "Финансисты";
  },
  isSeniorFinancier: () => {
    const role = localStorage.getItem("safina_role");
    return role === "senior_financier" || rbac.isAdmin();
  },
  isCeo: () => {
    const role = localStorage.getItem("safina_role");
    return role === "ceo" || rbac.isAdmin();
  },
  getUser,
  getTeam,
  isSafina: () => getUser().toLowerCase() === "safina",
  isFarrukh: () => getUser().toLowerCase() === "farrukh",
  hasWebAccess: () => !!localStorage.getItem("safina_token"),
  canDownload: () => rbac.isSeniorFinancier() || rbac.isCeo(),
  canManageTeam: () => rbac.isAdmin(),
};
