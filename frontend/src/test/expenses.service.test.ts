import { describe, it, expect, vi, beforeEach } from 'vitest';
import { expensesService } from '../lib/services/expenses';

// Mock the apiFetch module
vi.mock('../lib/api-client', () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../lib/api-client';

describe('Expenses Service Frontend Mapping', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

  it('correctly maps a backend expense response to the frontend interface', async () => {
    const mockBackendExpense = {
        id: "exp_test_123",
        request_id: "REQ-001",
        purpose: "Buy servers",
        items: [{name: "Server", quantity: 1, amount: 5000, currency: "USD"}],
        total_amount: 5000,
        currency: "USD",
        project_id: "proj_1",
        project_name: "IT Infrastructure",
        project_code: "IT",
        status: "pending_ceo",
        status_comment: "Looks good to me",
        internal_comment: "Urgent",
        created_by: "John Doe",
        created_by_id: "user_1",
        request_type: "expense",
        refund_data: null,
        receipt_photo_file_id: null,
        branch_id: "branch_1",
        branch_name: "HQ",
        branch_code: "HQ01",
        date: "2023-11-20T10:00:00Z",
        created_at: "2023-11-20T09:30:00Z"
    };

    (apiFetch as any).mockResolvedValueOnce({
        json: async () => mockBackendExpense
    });

    const result = await expensesService.getExpenseById("exp_test_123");

    expect(apiFetch).toHaveBeenCalledWith('/expenses/exp_test_123');
    
    // Check mapping transformations
    expect(result.id).toBe(mockBackendExpense.id);
    expect(result.requestId).toBe(mockBackendExpense.request_id);
    expect(result.totalAmount).toBe(mockBackendExpense.total_amount);
    expect(result.projectName).toBe(mockBackendExpense.project_name);
    expect(result.statusComment).toBe(mockBackendExpense.status_comment);
    expect(result.requestType).toBe(mockBackendExpense.request_type);
    
    // Date conversions
    expect(result.date).toBeInstanceOf(Date);
    expect(result.createdAt).toBeInstanceOf(Date);
  });

  it('correctly builds search parameters for pagination and filtering', async () => {
     (apiFetch as any).mockResolvedValueOnce({
         json: async () => ({
             items: [],
             total: 0,
             skip: 10,
             limit: 20,
             has_more: false
         })
     });

     await expensesService.getExpenses({
         status: "approved_ceo",
         project: "proj_1",
         skip: 10,
         limit: 20
     });

     expect(apiFetch).toHaveBeenCalledWith('/expenses?project=proj_1&status=approved_ceo&skip=10&limit=20');
  });
  
  it('correctly maps the update status payload and response', async () => {
    const mockBackendResponse = {
        id: "exp_test_123",
        status: "approved_ceo",
        status_comment: "CEO Approved",
        date: "2023-11-20T10:00:00Z",
        created_at: "2023-11-20T09:30:00Z"
    };

    (apiFetch as any).mockResolvedValueOnce({
        json: async () => mockBackendResponse
    });

    const result = await expensesService.updateExpenseStatus("exp_test_123", "approved_ceo", "CEO Approved");

    expect(apiFetch).toHaveBeenCalledWith('/expenses/exp_test_123/status', {
        method: "PATCH",
        body: JSON.stringify({ status: "approved_ceo", comment: "CEO Approved" })
    });
    
    expect(result.status).toBe("approved_ceo");
    expect(result.statusComment).toBe("CEO Approved");
  });
});
