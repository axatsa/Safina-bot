import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { ExpenseStatus, STATUS_LABELS } from "@/lib/types";
import { Loader2, FileText, Clock, FastForward } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

const ADMIN_COLUMNS = [
  {
    label: "🆕 Новые запросы",
    statuses: ["request"] as ExpenseStatus[],
    headerClass: "bg-indigo-50 border-indigo-200 text-indigo-800",
  },
  {
    label: "⏳ На рассмотрении",
    statuses: ["review"] as ExpenseStatus[],
    headerClass: "bg-blue-50 border-blue-200 text-blue-800",
  },
  {
    label: "🔄 На доработке",
    statuses: ["revision"] as ExpenseStatus[],
    headerClass: "bg-orange-50 border-orange-200 text-orange-800",
  },
];

const AdminApprovals = () => {
  const navigate = useNavigate();
  const isAdmin = store.isAdmin();

  const { data: expensesPage, isLoading } = useQuery({
    queryKey: ["expenses"],
    queryFn: () => store.getExpenses({ limit: 1000 }),
  });
  const expenses = expensesPage?.items ?? [];

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 animate-slide-in">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Очередь обработки</h1>
        <p className="text-sm text-muted-foreground mt-1">Первичная проверка и распределение заявок (Safina)</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {ADMIN_COLUMNS.map((col) => {
          const items = expenses.filter((e) => col.statuses.includes(e.status));
          return (
            <div key={col.label} className="rounded-xl border bg-card overflow-hidden flex flex-col min-h-[400px]">
              <div className={`flex items-center justify-between px-4 py-3 border-b ${col.headerClass}`}>
                <span className="font-display font-semibold text-sm">{col.label}</span>
                <span className="text-xs font-medium bg-foreground/10 px-2 py-0.5 rounded-full">{items.length}</span>
              </div>

              <div className="p-3 space-y-3 flex-1 overflow-y-auto">
                {items.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-40 text-xs text-muted-foreground opacity-60">
                    <FileText className="w-8 h-8 mb-2 opacity-20" />
                    Пусто
                  </div>
                ) : (
                  items.map((e) => (
                    <div
                      key={e.id}
                      onClick={() => navigate(`/dashboard/expense/${e.id}`)}
                      className="group rounded-lg border bg-background p-4 cursor-pointer hover:shadow-md hover:border-primary/30 transition-all"
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <p className="font-mono font-bold text-xs text-primary">{e.requestId}</p>
                        <span className="text-[10px] text-muted-foreground">{new Date(e.date).toLocaleDateString()}</span>
                      </div>
                      <p className="text-sm font-medium text-foreground mb-1 line-clamp-2">{e.purpose}</p>
                      <div className="flex items-center justify-between mt-3 pt-3 border-t">
                        <p className="text-sm font-bold">
                          {Number(e.totalAmount || 0).toLocaleString()} {e.currency}
                        </p>
                        <p className="text-[10px] text-muted-foreground italic">{e.createdBy}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AdminApprovals;
