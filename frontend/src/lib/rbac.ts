import { UserRole } from "./types";

export const getRole = (): UserRole =>
  (localStorage.getItem("safina_role") as UserRole) ?? "user";

export const rbac = {
  isAdmin: () => getRole() === "admin",
  isSeniorFinancier: () => getRole() === "senior_financier",
  isCeo: () => getRole() === "ceo",
  hasWebAccess: () => ["admin", "senior_financier"].includes(getRole()),
  canManageTeam: () => ["admin", "senior_financier", "ceo"].includes(getRole()),
};
