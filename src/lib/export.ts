import { ExpenseRequest, STATUS_LABELS } from "./types";
import { format } from "date-fns";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export function generateExpenseCSV(
  expenses: ExpenseRequest[],
  filename: string,
  options?: { allStatuses?: boolean }
) {
  const BOM = "\uFEFF";
  const headers = [
    "Request ID", "Дата/время", "Код проекта", "Проект", "Ответственный",
    "Статус", "Наименование расхода", "Кол-во", "Сумма", "Валюта", "Итог по заявке",
  ];

  let data = expenses;
  if (!options?.allStatuses) {
    data = expenses.filter((e) => e.status === "confirmed");
  }

  const rows: string[][] = [];
  for (const e of data) {
    for (const item of e.items) {
      rows.push([
        e.requestId,
        format(e.date, "yyyy-MM-dd HH:mm"),
        e.projectCode,
        e.projectName,
        e.createdBy,
        STATUS_LABELS[e.status] || e.status,
        item.name,
        String(item.quantity),
        String(item.amount),
        item.currency,
        `${e.totalAmount} ${e.currency}`,
      ]);
    }
  }

  const csv = BOM + [headers, ...rows].map((r) => r.map((c) => `"${c}"`).join(";")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  downloadBlob(blob, `${filename}.csv`);
}

export function generateExpensePDF(expense: ExpenseRequest) {
  const doc = new jsPDF();

  doc.setFontSize(16);
  doc.text("Смета расходов", 14, 20);

  doc.setFontSize(10);
  const info = [
    `Request ID: ${expense.requestId}`,
    `Дата: ${format(expense.date, "yyyy-MM-dd HH:mm")}`,
    `Проект: ${expense.projectName} (${expense.projectCode})`,
    `Ответственный: ${expense.createdBy}`,
    `Статус: ${STATUS_LABELS[expense.status]}`,
  ];
  info.forEach((line, i) => doc.text(line, 14, 32 + i * 6));

  autoTable(doc, {
    startY: 65,
    head: [["Наименование", "Кол-во", "Сумма", "Валюта"]],
    body: expense.items.map((item) => [
      item.name,
      String(item.quantity),
      item.amount.toLocaleString(),
      item.currency,
    ]),
    foot: [["Итого", "", expense.totalAmount.toLocaleString(), expense.currency]],
    styles: { fontSize: 9 },
    headStyles: { fillColor: [45, 80, 65] },
    footStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0], fontStyle: "bold" },
  });

  doc.save(`smeta_${expense.requestId}.pdf`);
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
