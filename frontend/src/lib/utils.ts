import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Форматирует сумму в нужном формате:
 * UZS → "1 000 000 сум"
 * USD → "1 000 000 $"
 */
export function formatCurrency(amount: number, currency: string): string {
  const rounded = Math.round(amount);
  const formatted = rounded.toLocaleString("ru-RU");
  if (currency === "USD") {
    return `${formatted} $`;
  }
  return `${formatted} сум`;
}
