export interface Project {
  id: string;
  name: string;
  code: string;
  templates: string[];
  createdAt: Date;
  members: Array<{
    id: string;
    lastName: string;
    firstName: string;
    position?: string;
  }>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
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
  templates: string[];
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

export interface ExpenseStatusHistory {
  status: string;
  comment?: string;
  changed_by_name?: string;
  createdAt: Date;
}

export interface ExpenseRequest {
  id: string;
  requestId: string;
  date: Date;
  purpose: string;
  items: ExpenseItem[];
  totalAmount: number;
  currency: string;
  usdRate?: number;
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

/** Statuses shown in the main Kanban board */
export const KANBAN_STATUSES: ExpenseStatus[] = [
  "request",
  "review",
  "confirmed",
  "declined",
  "revision",
];

/** Statuses shown in the Approval Sidebar (CFO + Ganiev chain) */
export const APPROVAL_STATUSES: ExpenseStatus[] = [
  "pending_senior",
  "approved_senior",
  "rejected_senior",
  "pending_ceo",
  "approved_ceo",
  "rejected_ceo",
];

/** User roles used in localStorage */
export type UserRole = "admin" | "senior_financier" | "ceo" | "user";

export const AVAILABLE_TEMPLATES = [
  { key: "land",       label: "📋 LAND"        },
  { key: "drujba",     label: "📋 ЛС (Дружба)" },
  { key: "management", label: "📋 Management"   },
  { key: "school",     label: "📋 School"       },
] as const;
