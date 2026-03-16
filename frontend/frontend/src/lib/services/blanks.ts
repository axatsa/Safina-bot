import { apiFetch } from "../api-client";

export interface BlankItem {
  name: string;
  qty: number;
  amount: number;
  currency: string;
}

export interface BlankData {
  template: string;
  sender_name?: string;
  sender_position?: string;
  purpose?: string;
  items?: BlankItem[];
  total_amount?: number;
  currency?: string;
  date?: string;
  
  // Refund
  client_name?: string;
  passport_series?: string;
  passport_number?: string;
  passport_issued_by?: string;
  passport_date?: string;
  phone?: string;
  contract_number?: string;
  contract_date?: string;
  reason?: string;
  reason_other?: string;
  amount?: number;
  amount_words?: string;
  card_holder?: string;
  card_number?: string;
  transit_account?: string;
  bank_name?: string;
}

export const generateBlank = async (data: BlankData) => {
  const response = await apiFetch('/blanks/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to generate blank");
  return response.blob();
};
