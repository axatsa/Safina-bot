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

  // Custom font registration would go here
  // doc.addFileToVFS('Roboto-Regular.ttf', ROBOTO_REGULAR_BASE64);
  // doc.addFont('Roboto-Regular.ttf', 'Roboto', 'normal');
  // doc.setFont('Roboto');

  // Title
  doc.setFontSize(22);
  doc.text("СМЕТА", 105, 25, { align: "center" });

  // Header Info
  doc.setFontSize(10);
  doc.text(`Проект: ${expense.projectName}`, 14, 40);
  doc.text(`Дата: ${format(expense.date, "dd.MM.yyyy")}`, 14, 46);
  doc.text(`Назначение: ${expense.purpose}`, 14, 52);

  // Table
  autoTable(doc, {
    startY: 60,
    head: [["№", "Наименование", "Кол-во", "Сумма", "Итого"]],
    body: expense.items.map((item, index) => [
      index + 1,
      item.name,
      String(item.quantity),
      item.amount.toLocaleString(),
      (item.quantity * item.amount).toLocaleString(),
    ]),
    foot: [["", "ИТОГО", "", "", `${expense.totalAmount.toLocaleString()} ${expense.currency}`]],
    styles: { fontSize: 10, cellPadding: 3 },
    headStyles: { fillColor: [40, 40, 40], textColor: [255, 255, 255] },
    footStyles: { fillColor: [245, 245, 245], textColor: [0, 0, 0], fontStyle: "bold" },
    columnStyles: {
      0: { cellWidth: 10 },
      1: { cellWidth: "auto" },
      2: { cellWidth: 20, halign: "center" },
      3: { cellWidth: 30, halign: "right" },
      4: { cellWidth: 40, halign: "right" },
    },
  });

  // Footer / Signatures
  const finalY = (doc as any).lastAutoTable.finalY + 30;

  doc.setFontSize(10);
  doc.text("Заявитель:", 14, finalY);
  doc.setFont("", "bold");
  doc.text(`${expense.createdBy}`, 14, finalY + 6);
  doc.setFont("", "normal");
  doc.text(`${expense.createdByPosition || "Сотрудник"}`, 14, finalY + 12);

  doc.text("________________ / signature /", 140, finalY + 6);
  doc.text(`Дата: ${format(new Date(), "dd.MM.yyyy")}`, 140, finalY + 12);

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
