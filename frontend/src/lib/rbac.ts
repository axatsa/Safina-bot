import { UserRole } from "./types";

export const getRole = (): UserRole =>
  (localStorage.getItem("safina_role") as UserRole) ?? "user";

export const getUser = (): string =>
  localStorage.getItem("safina_user") ?? "";

export const rbac = {
  isAdmin: () => !!localStorage.getItem("safina_token"),
  isSeniorFinancier: () => !!localStorage.getItem("safina_token"),
  isCeo: () => !!localStorage.getItem("safina_token"),
  getUser,
  isSafina: () => getUser().toLowerCase() === "safina",
  isFarrukh: () => getUser().toLowerCase() === "farrukh",
  hasWebAccess: () => !!localStorage.getItem("safina_token"),
  canDownload: () => !!localStorage.getItem("safina_token"),
  canManageTeam: () => !!localStorage.getItem("safina_token"),
};
