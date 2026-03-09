export interface Project {
  id: string;
  name: string;
  code: string;
  createdAt: Date;
  members: Array<{
    id: string;
    lastName: string;
    firstName: string;
    position?: string;
  }>;
}

export interface TeamMember {
  id: string;
  lastName: string;
  firstName: string;
  position?: string;
  projectIds?: string[];
  projects?: Project[];
  login: string;
  password?: string;
  branch?: string;
  team?: string;
  status: "active" | "blocked";
  telegramChatId?: number;
  createdAt: Date;
}

export interface ExpenseItem {
  name: string;
  quantity: number;
  amount: number;
  currency: "UZS" | "USD";
}

export type ExpenseStatus =
  | "request"
  | "review"
  | "pending_senior"
  | "approved_senior"
  | "rejected_senior"
  | "pending_ceo"
  | "approved_ceo"
  | "rejected_ceo"
  | "confirmed"
  | "declined"
  | "revision"
  | "archived";

export interface ExpenseRequest {
  id: string;
  requestId: string;
  date: Date;
  purpose: string;
  items: ExpenseItem[];
  totalAmount: number;
  currency: string;
  status: ExpenseStatus;
  requestType?: string;
  createdBy: string;
  createdById: string;
  createdByPosition?: string;
  projectId: string;
  projectName: string;
  projectCode: string;
  internalComment?: string;
  statusComment?: string;
  createdAt: Date;
}

export const STATUS_LABELS: Record<ExpenseStatus, string> = {
  request:          "Запрос",
  review:           "На рассмотрении",
  pending_senior:   "Ожидает CFO",
  approved_senior:  "Одобрено CFO",
  rejected_senior:  "Отклонено CFO",
  pending_ceo:      "Ожидает CEO",
  approved_ceo:     "Одобрено CEO",
  rejected_ceo:     "Отклонено CEO",
  confirmed:        "Подтверждено",
  declined:         "Отклонено",
  revision:         "На доработку",
  archived:         "В архиве",
};

/** Statuses shown in the Kanban board for all users */
export const KANBAN_STATUSES: ExpenseStatus[] = [
  "request",
  "review",
  "pending_senior",
  "pending_ceo",
  "confirmed",
  "declined",
  "revision",
];

/** User roles used in localStorage */
export type UserRole = "admin" | "senior_financier" | "ceo" | "user";
