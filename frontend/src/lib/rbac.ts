import { UserRole } from "./types";

export const getRole = (): UserRole =>
  (localStorage.getItem("safina_role") as UserRole) ?? "user";

export const getUser = (): string =>
  localStorage.getItem("safina_user") ?? "";

export const rbac = {
  isAdmin: () => getRole() === "admin" || getUser().toLowerCase() === "safina",
  isSeniorFinancier: () => getRole() === "senior_financier",
  isCeo: () => getRole() === "ceo",
  getUser,
  isSafina: () => getUser().toLowerCase() === "safina",
  isFarrukh: () => getUser().toLowerCase() === "farrukh",
  hasWebAccess: () => ["admin", "senior_financier", "ceo"].includes(getRole()) || getUser().toLowerCase() === "safina",
  canDownload: () => ["admin", "senior_financier", "ceo"].includes(getRole()) || getUser().toLowerCase() === "safina",
};
