import { UserRole } from "./types";

export const getRole = (): UserRole =>
  (localStorage.getItem("safina_role") as UserRole) ?? "user";

export const getUser = (): string =>
  localStorage.getItem("safina_user") ?? "";

export const rbac = {
  isAdmin: () => getRole() === "admin",
  isSeniorFinancier: () => getRole() === "senior_financier",
  isCeo: () => getRole() === "ceo",
  getUser,
  isSafina: () => getUser().toLowerCase() === "safina",
  isFarrukh: () => getUser().toLowerCase() === "farrukh",
  hasWebAccess: () => ["admin", "senior_financier"].includes(getRole()) || getUser().toLowerCase() === "safina",
  canManageTeam: () => ["admin", "senior_financier", "ceo"].includes(getRole()),
};
