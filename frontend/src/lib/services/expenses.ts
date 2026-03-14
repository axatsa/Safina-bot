import { apiFetch } from "../api-client";
import { ExpenseRequest, ExpenseStatus } from "../types";

export const expensesService = {
  getExpenses: async (params?: { project?: string; status?: string }): Promise<ExpenseRequest[]> => {
    const searchParams = new URLSearchParams();
    if (params?.project) searchParams.append("project", params.project);
    if (params?.status) searchParams.append("status", params.status);
    
    const endpoint = `/expenses${searchParams.toString() ? "?" + searchParams.toString() : ""}`;
    const res = await apiFetch(endpoint);
    const data = await res.json();
    
    return data.map((e: any) => ({
      id: e.id,
      requestId: e.request_id,
      purpose: e.purpose,
      items: e.items,
      totalAmount: e.total_amount,
      currency: e.currency,
      projectId: e.project_id,
      projectName: e.project_name,
      projectCode: e.project_code,
      status: e.status,
      statusComment: e.status_comment,
      internalComment: e.internal_comment,
      createdBy: e.created_by,
      createdById: e.created_by_id,
      requestType: e.request_type,
      refundData: e.refund_data,
      receiptPhotoFileId: e.receipt_photo_file_id,
      date: new Date(e.date),
      createdAt: new Date(e.created_at),
    }));
  },

  updateExpenseStatus: async (expenseId: string, status: ExpenseStatus, comment?: string): Promise<ExpenseRequest> => {
    const res = await apiFetch(`/expenses/${expenseId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, comment }),
    });
    return res.json();
  },

  updateInternalComment: async (expenseId: string, internalComment: string): Promise<void> => {
    await apiFetch(`/expenses/${expenseId}/comment`, {
      method: "PUT",
      body: JSON.stringify({ internal_comment: internalComment }),
    });
  },

  forwardToSenior: async (expenseId: string): Promise<ExpenseRequest> => {
    const res = await apiFetch(`/expenses/${expenseId}/forward_senior`, { method: "POST" });
    return res.json();
  },

  forwardToCeo: async (expenseId: string): Promise<ExpenseRequest> => {
    const res = await apiFetch(`/expenses/${expenseId}/forward_ceo`, { method: "POST" });
    return res.json();
  },

  submitExpenseFromWeb: async (data: any) => {
    const res = await apiFetch("/expenses/web-submit", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return await res.json();
  },

  createExpenseRequest: async (data: any) => {
    const res = await apiFetch("/expenses", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return await res.json();
  },

  exportXLSX: async (params: { project?: string; user?: string; from?: string; to?: string; allStatuses?: boolean }): Promise<void> => {
    const searchParams = new URLSearchParams();
    if (params.project && params.project !== "all") searchParams.append("project", params.project);
    if (params.user && params.user !== "all") searchParams.append("user_id", params.user);
    if (params.from) searchParams.append("from_date", params.from);
    if (params.to) searchParams.append("to_date", params.to);
    if (params.allStatuses) searchParams.append("allStatuses", "true");

    const res = await apiFetch(`/expenses/export-xlsx?${searchParams.toString()}`);
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', `expenses_report_${new Date().toISOString().split('T')[0]}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  exportDocx: async (expenseId: string) => {
    const res = await apiFetch(`/expenses/${expenseId}/export-docx`);
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', `smeta_${expenseId}.docx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  exportRefundApplication: async (expenseId: string): Promise<void> => {
    const res = await apiFetch(`/expenses/refund/${expenseId}/export-application-docx`);
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', `заявление_${expenseId}.docx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};
