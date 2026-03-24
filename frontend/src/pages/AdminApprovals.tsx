import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { ExpenseStatus, STATUS_LABELS } from "@/lib/types";
import { Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";


const AdminApprovals = () => {
  const navigate = useNavigate();
  const isFarrukh = store.isFarrukh();

  const activeColumns = isFarrukh ? [
    {
      label: "⏳ На согласовании CEO",
      statuses: ["pending_ceo", "approved_ceo", "rejected_ceo"] as ExpenseStatus[],
      headerClass: "bg-gradient-to-br from-emerald-500 to-teal-600 text-white border-transparent shadow-sm",
    }
  ] : [
    {
      label: "⏳ На согласовании CFO",
      statuses: ["pending_senior", "approved_senior", "rejected_senior"] as ExpenseStatus[],
      headerClass: "bg-gradient-to-br from-blue-600 to-indigo-600 text-white border-transparent shadow-sm",
    },
    {
      label: "⏳ На согласовании CEO",
      statuses: ["pending_ceo", "approved_ceo", "rejected_ceo"] as ExpenseStatus[],
      headerClass: "bg-gradient-to-br from-emerald-500 to-teal-600 text-white border-transparent shadow-sm",
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

  const getCardAccent = (status: ExpenseStatus) => {
    if (["approved_senior", "approved_ceo", "confirmed"].includes(status))
      return "border-l-4 border-l-emerald-500 bg-emerald-50/60";
    if (["rejected_senior", "rejected_ceo", "declined"].includes(status))
      return "border-l-4 border-l-red-500 bg-red-50/60";
    if (status === "revision")
      return "border-l-4 border-l-orange-500 bg-orange-50/60";
    return "";
  };

  const getCardBadge = (status: ExpenseStatus) => {
    if (["approved_senior", "approved_ceo", "confirmed"].includes(status))
      return <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded-full">✅ Одобрено</span>;
    if (["rejected_senior", "rejected_ceo", "declined"].includes(status))
      return <span className="text-[10px] font-bold text-red-700 bg-red-100 px-1.5 py-0.5 rounded-full">❌ Отклонено</span>;
    return <span className="text-[10px] font-bold text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">{STATUS_LABELS[status]}</span>;
  };

  return (
    <div className="p-6 space-y-6 animate-slide-in">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Очередь обработки</h1>
        <p className="text-sm text-muted-foreground mt-1">Управление всеми этапами согласования</p>
      </div>

      <div className="overflow-x-auto pb-4 -mx-6 px-6">
        <div className={`flex lg:grid lg:grid-cols-${activeColumns.length} md:grid-cols-2 gap-4 min-w-max lg:min-w-0`}>
          {activeColumns.map((col) => {
            const items = expenses.filter((e) => col.statuses.includes(e.status));
            return (
              <div key={col.label} className="rounded-xl border bg-card overflow-hidden flex flex-col w-[280px] lg:w-auto shrink-0 lg:shrink">
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
                      <div
                        key={e.id}
                        onClick={() => navigate(`/dashboard/expense/${e.id}`)}
                        className={`rounded-lg border bg-background p-3 cursor-pointer hover:shadow-md transition-all ${getCardAccent(e.status)}`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-1.5">
                          <p className="font-mono font-bold text-xs text-primary">{e.requestId}</p>
                          {getCardBadge(e.status)}
                        </div>
                        <p className="text-xs text-muted-foreground truncate mb-1">{e.purpose}</p>
                        <div className="flex justify-between items-end">
                          <div>
                            <p className="text-xs font-semibold">
                              {Number(e.totalAmount).toLocaleString()} {e.currency}
                            </p>
                            <p className="text-[10px] text-muted-foreground mt-1">{e.createdBy}</p>
                          </div>
                          <p className="text-[10px] font-bold text-primary/70">{e.projectName}</p>
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
    </div>
  );
};

export default AdminApprovals;
