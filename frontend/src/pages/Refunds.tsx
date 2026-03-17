import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { ExpenseRequest, STATUS_LABELS } from "@/lib/types";
import { Loader2, ExternalLink, RefreshCw, Download } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { Button } from "@/components/ui/button";

const Refunds = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  const { data: expensesPage, isLoading, refetch } = useQuery({
    queryKey: ["expenses-refunds"],
    queryFn: () => store.getExpenses({ limit: 1000 }),
    refetchInterval: 15000,
  });
  const expenses = expensesPage?.items ?? [];

  const refunds = expenses.filter(
    (e) => e.requestType === "refund"
  );

  const filtered = refunds.filter((e) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      e.requestId?.toLowerCase().includes(q) ||
      e.createdBy?.toLowerCase().includes(q)
    );
  });

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 animate-slide-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Возвраты инвестиций</h1>
          <p className="text-sm text-muted-foreground mt-1">Управление возвратами средств ученикам</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => store.exportXLSX({ allStatuses: true, project: 'all' })}>
            <Download className="w-4 h-4 mr-2" />
            Скачать XLSX
          </Button>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Обновить
          </Button>
        </div>
      </div>

      <div className="relative">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск по ID или автору..."
          className="w-full max-w-sm px-4 py-2 text-sm rounded-xl border bg-background focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      <div className="glass-card rounded-2xl border overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b bg-muted/30">
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">ID</th>
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Дата</th>
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Автор</th>
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Назначение</th>
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Статус</th>
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider text-right">Сумма</th>
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider text-right">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.map((expense: ExpenseRequest) => (
              <tr key={expense.id} className="hover:bg-muted/10 transition-colors">
                <td className="px-6 py-4 font-display font-bold text-primary text-sm">
                  {expense.requestId}
                </td>
                <td className="px-6 py-4 text-xs text-muted-foreground">
                  {format(new Date(expense.date), "dd.MM.yyyy HH:mm", { locale: ru })}
                </td>
                <td className="px-6 py-4 text-sm">{expense.createdBy}</td>
                <td className="px-6 py-4 text-sm text-muted-foreground max-w-[200px] truncate">
                  {expense.purpose}
                </td>
                <td className="px-6 py-4">
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-muted border">
                    {STATUS_LABELS[expense.status] ?? expense.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right font-display font-bold text-sm">
                  {Number(expense.totalAmount).toLocaleString()} {expense.currency}
                </td>
                <td className="px-6 py-4 text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => navigate(`/dashboard/expense/${expense.id}`)}
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-muted-foreground text-sm italic">
                  Заявок на возврат пока нет
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Refunds;
