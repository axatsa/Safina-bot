import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { ExpenseStatus } from "@/lib/types";
import ExpenseCard from "@/components/ExpenseCard";
import { Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";


const AdminApprovals = () => {
  const navigate = useNavigate();
  const isFarrukh = store.isFarrukh();

  const activeColumns = [
    {
      label: "⏳ Ожидает CFO",
      statuses: ["pending_senior"] as ExpenseStatus[],
      headerClass: "bg-gradient-to-br from-blue-600 to-indigo-600 text-white border-transparent shadow-sm",
    },
    {
      label: "📊 Результат CFO",
      statuses: ["approved_senior", "rejected_senior"] as ExpenseStatus[],
      headerClass: "bg-slate-100 dark:bg-slate-800 text-foreground border-transparent shadow-sm",
    },
    {
      label: "⏳ Ожидает CEO",
      statuses: ["pending_ceo"] as ExpenseStatus[],
      headerClass: "bg-gradient-to-br from-emerald-500 to-teal-600 text-white border-transparent shadow-sm",
    },
    {
      label: "📊 Результат CEO",
      statuses: ["approved_ceo", "rejected_ceo"] as ExpenseStatus[],
      headerClass: "bg-slate-100 dark:bg-slate-800 text-foreground border-transparent shadow-sm",
    }
  ];

  const { data: expensesPage, isLoading } = useQuery({
    queryKey: ["admin-expenses-approvals", isFarrukh],
    queryFn: () => store.getExpenses({ 
      limit: 100, 
      status: activeColumns.flatMap(c => c.statuses).join(',') as ExpenseStatus 
    }),
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
        <p className="text-sm text-muted-foreground mt-1">Управление всеми этапами согласования</p>
      </div>

      <div className="overflow-x-auto pb-4 -mx-6 px-6">
        <div className="flex flex-col lg:flex-row gap-4 min-w-max lg:min-w-0">
          {activeColumns.map((col) => {
            const items = expenses.filter((e) => col.statuses.includes(e.status));
            return (
              <div key={col.label} className="rounded-xl border bg-card overflow-hidden flex flex-col shrink-0 transition-all duration-300 w-full lg:w-auto lg:flex-1 lg:min-w-[280px]">
                <div className={`flex items-center justify-between px-4 py-3 border-b border-transparent ${col.headerClass}`}>
                  <span className="font-display font-semibold text-sm">{col.label}</span>
                  <span className="text-xs font-medium bg-white/20 px-2 py-0.5 rounded-full">{items.length}</span>
                </div>

                <div className="p-2 space-y-2 flex-1">
                  {items.length === 0 ? (
                    <div className="flex items-center justify-center h-20 text-xs text-muted-foreground">
                      Нет заявок
                    </div>
                  ) : (
                    items.map((e) => (
                      <ExpenseCard key={e.id} expense={e} />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AdminApprovals;
