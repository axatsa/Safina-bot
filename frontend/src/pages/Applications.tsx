import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { ExpenseRequest, ExpenseStatus, KANBAN_STATUSES, APPROVAL_STATUSES, STATUS_LABELS } from "@/lib/types";
import ExpenseCard from "@/components/ExpenseCard";
import CompactExpenseCard from "@/components/CompactExpenseCard";
import FilterBar from "@/components/FilterBar";
import { ChevronDown, ChevronRight, Loader2, DollarSign, FileText, Clock, CheckCircle, UserCheck, ExternalLink } from "lucide-react";
import { DragDropContext, Droppable, Draggable, DropResult } from "@hello-pangea/dnd";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const APPROVAL_STATUS_GROUPS = [
  { label: "📋 Ожидает CFO",      statuses: ["pending_senior"]  as ExpenseStatus[] },
  { label: "✅ Одобрено CFO",      statuses: ["approved_senior"] as ExpenseStatus[] },
  { label: "❌ Отклонено CFO",    statuses: ["rejected_senior"] as ExpenseStatus[] },
  { label: "👤 Ожидает Ganiev",   statuses: ["pending_ceo"]    as ExpenseStatus[] },
  { label: "✅ Одобрено Ganiev",   statuses: ["approved_ceo"]   as ExpenseStatus[] },
  { label: "❌ Отклонено Ganiev", statuses: ["rejected_ceo"]   as ExpenseStatus[] },
];

const kanbanColors: Record<string, string> = {
  request:        "kanban-request",
  review:         "kanban-review",
  confirmed:      "kanban-confirmed",
  declined:       "kanban-declined",
  revision:       "kanban-revision",
  pending_senior: "kanban-review",
  pending_ceo:    "kanban-review",
};

const Applications = () => {
  const queryClient = useQueryClient();
  const [selectedProject, setSelectedProject] = useState("all");
  const [selectedUser, setSelectedUser] = useState("all");
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [collapsedColumns, setCollapsedColumns] = useState<Record<string, boolean>>({});

  // Fecthing expenses via React Query
  const { data: expenses = [], isLoading } = useQuery({
    queryKey: ["expenses"],
    queryFn: () => store.getExpenses(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Fetching projects
  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: () => store.getProjects(),
  });

  // Fetching team
  const { data: team = [] } = useQuery({
    queryKey: ["team"],
    queryFn: () => store.getTeam(),
  });

  // Mutation for status update (Drag & Drop)
  const mutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ExpenseStatus }) =>
      store.updateExpenseStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
    onError: () => {
      toast.error("Не удалось обновить статус");
    }
  });

  const filtered = useMemo(() => {
    return expenses.filter((e) => {
      // Basic Status Filter (Archive is separate)
      if (e.status === "archived") return false;

      // Project Filter
      if (selectedProject !== "all" && e.projectId !== selectedProject) return false;

      // User Filter
      if (selectedUser !== "all" && e.createdById !== selectedUser) return false;

      // Date Range Filter (Granular)
      if (dateRange.from) {
        const start = new Date(dateRange.from);
        start.setHours(0, 0, 0, 0);
        if (new Date(e.date) < start) return false;
      }
      if (dateRange.to) {
        const end = new Date(dateRange.to);
        end.setHours(23, 59, 59, 999);
        if (new Date(e.date) > end) return false;
      }

      // Search Filter (ID or Item Names)
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesId = e.requestId.toLowerCase().includes(query);
        const matchesItems = e.items?.some(item => item.name.toLowerCase().includes(query));
        if (!matchesId && !matchesItems) return false;
      }

      return true;
    });
  }, [expenses, selectedProject, selectedUser, dateRange, searchQuery]);

  const toggleColumn = (status: string) => {
    setCollapsedColumns((prev) => ({ ...prev, [status]: !prev[status] }));
  };

  const handleDragEnd = (result: DropResult) => {
    const { draggableId, destination } = result;
    if (!destination) return;

    const newStatus = destination.droppableId as ExpenseStatus;
    const item = expenses.find(e => e.id === draggableId);

    if (item && item.status !== newStatus) {
      if (newStatus === "declined" || newStatus === "revision") {
        toast.info("Для этого статуса требуется комментарий. Откройте детали заявки.");
        return;
      }
      mutation.mutate({ id: draggableId, status: newStatus });
    }
  };

  const handleExport = (allStatuses: boolean) => {
    store.exportXLSX({
      project: selectedProject,
      user: selectedUser,
      from: dateRange.from?.toISOString(),
      to: dateRange.to?.toISOString(),
      allStatuses
    });
  };


  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  // Calculate Dashboard Statistics
  const totalRequests = filtered.length;
  const totalAmountUZS = filtered
    .filter(e => e.currency === 'UZS' && !['declined', 'archived', 'rejected_senior'].includes(e.status))
    .reduce((sum, e) => sum + Number(e.totalAmount || 0), 0);
  const pendingCount = filtered.filter(e => ['review', 'pending_senior'].includes(e.status)).length;
  const approvedCount = filtered.filter(e => ['confirmed', 'approved_senior'].includes(e.status)).length;

  const isAdmin = store.isAdmin();
  const isCFO = store.isSeniorFinancier();
  const isCEO = store.isCeo();
  const navigate = useNavigate();

  // ── CFO / CEO approval kanban columns ─────────────────────────────────────
  const CFO_COLUMNS = [
    {
      label: "📋 Ожидает CFO",
      statuses: ["pending_senior"] as ExpenseStatus[],
      headerClass: "bg-amber-50 border-amber-200 text-amber-800",
      neutral: true,
    },
    {
      label: "Решение CFO",
      statuses: ["approved_senior", "rejected_senior"] as ExpenseStatus[],
      headerClass: "bg-slate-50 border-slate-200 text-slate-700",
      neutral: false,
    },
    {
      label: "👤 Ожидает CEO",
      statuses: ["pending_ceo"] as ExpenseStatus[],
      headerClass: "bg-violet-50 border-violet-200 text-violet-800",
      neutral: true,
    },
    {
      label: "Решение CEO",
      statuses: ["approved_ceo", "rejected_ceo"] as ExpenseStatus[],
      headerClass: "bg-slate-50 border-slate-200 text-slate-700",
      neutral: false,
    },
  ];

  const getCardAccent = (status: ExpenseStatus) => {
    if (["approved_senior", "approved_ceo"].includes(status))
      return "border-l-4 border-l-emerald-500 bg-emerald-50/60";
    if (["rejected_senior", "rejected_ceo"].includes(status))
      return "border-l-4 border-l-red-500 bg-red-50/60";
    return "";
  };

  const getCardBadge = (status: ExpenseStatus) => {
    if (["approved_senior", "approved_ceo"].includes(status))
      return <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded-full">✅ Одобрено</span>;
    if (["rejected_senior", "rejected_ceo"].includes(status))
      return <span className="text-[10px] font-bold text-red-700 bg-red-100 px-1.5 py-0.5 rounded-full">❌ Отклонено</span>;
    return null;
  };

  // ── JSX: approval kanban for CFO / CEO ────────────────────────────────────
  if (isCFO || isCEO) {
    return (
      <div className="p-6 space-y-6 animate-slide-in">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Согласования</h1>
          <p className="text-sm text-muted-foreground mt-1">Заявки в цепочке утверждения CFO / CEO</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {CFO_COLUMNS.map((col) => {
            const items = expenses.filter((e) => col.statuses.includes(e.status));
            return (
              <div key={col.label} className="rounded-xl border bg-card overflow-hidden flex flex-col">
                {/* Column header */}
                <div className={`flex items-center justify-between px-4 py-3 border-b ${col.headerClass}`}>
                  <span className="font-display font-semibold text-sm">{col.label}</span>
                  <span className="text-xs font-medium bg-foreground/10 px-2 py-0.5 rounded-full">{items.length}</span>
                </div>

                {/* Cards */}
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
                        <p className="text-xs font-semibold">
                          {Number(e.totalAmount).toLocaleString()} {e.currency}
                        </p>
                        <p className="text-[10px] text-muted-foreground mt-1">{e.createdBy}</p>
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
  }

  // ── JSX: standard kanban for admin / user ─────────────────────────────────
  return (
    <div className="p-6 space-y-6 animate-slide-in">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Заявки</h1>
        <p className="text-sm text-muted-foreground mt-1">Управление заявками на расход</p>
      </div>

      <FilterBar
        projects={projects}
        selectedProject={selectedProject}
        onProjectChange={setSelectedProject}
        team={team}
        selectedUser={selectedUser}
        onUserChange={setSelectedUser}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        onExport={handleExport}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="glass-card rounded-xl p-4 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 bg-blue-100 text-blue-600 rounded-lg"><FileText className="w-4 h-4" /></div>
            <p className="text-sm font-medium text-muted-foreground">Всего заявок</p>
          </div>
          <h3 className="text-2xl font-bold">{totalRequests}</h3>
        </div>
        <div className="glass-card rounded-xl p-4 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 bg-amber-100 text-amber-600 rounded-lg"><Clock className="w-4 h-4" /></div>
            <p className="text-sm font-medium text-muted-foreground">На рассмотрении</p>
          </div>
          <h3 className="text-2xl font-bold">{pendingCount}</h3>
        </div>
        <div className="glass-card rounded-xl p-4 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg"><CheckCircle className="w-4 h-4" /></div>
            <p className="text-sm font-medium text-muted-foreground">Утверждено</p>
          </div>
          <h3 className="text-2xl font-bold">{approvedCount}</h3>
        </div>
        <div className="glass-card rounded-xl p-4 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg"><DollarSign className="w-4 h-4" /></div>
            <p className="text-sm font-medium text-muted-foreground">Сумма (UZS к оплате)</p>
          </div>
          <h3 className="text-xl font-bold truncate" title={totalAmountUZS.toLocaleString()}>{totalAmountUZS.toLocaleString()}</h3>
        </div>
      </div>

      {/* Main area: kanban + optional sidebar */}
      <div className={isAdmin ? "flex gap-4" : ""}>
        {/* Kanban board */}
        <div className="flex-1 min-w-0">
          <DragDropContext onDragEnd={handleDragEnd}>
            <div className="grid grid-cols-1 lg:grid-cols-5 md:grid-cols-3 gap-4">
              {KANBAN_STATUSES.map((statusKey) => {
                const items = filtered.filter((e) => e.status === statusKey);
                const isCollapsed = !!collapsedColumns[statusKey];

                return (
                  <div key={statusKey} className="rounded-xl border bg-card overflow-hidden">
                    <button
                      onClick={() => toggleColumn(statusKey)}
                      className={`flex items-center gap-2 px-3 py-2.5 w-full text-left ${kanbanColors[statusKey]}`}
                    >
                      {isCollapsed ? (
                        <ChevronRight className="w-3.5 h-3.5 shrink-0" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 shrink-0" />
                      )}
                      <h3 className="font-display font-semibold text-xs">{STATUS_LABELS[statusKey]}</h3>
                      <span className="ml-auto text-xs font-medium bg-foreground/10 px-2 py-0.5 rounded-full">
                        {items.length}
                      </span>
                    </button>

                    <Droppable droppableId={statusKey}>
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.droppableProps}
                          className={`p-2 space-y-2 min-h-[120px] transition-colors ${
                            snapshot.isDraggingOver ? "bg-accent/30" : ""
                          }`}
                        >
                          {items.map((expense, index) => (
                            <Draggable key={expense.id} draggableId={expense.id} index={index}>
                              {(dragProvided, dragSnapshot) => (
                                <div
                                  ref={dragProvided.innerRef}
                                  {...dragProvided.draggableProps}
                                  {...dragProvided.dragHandleProps}
                                  className={dragSnapshot.isDragging ? "opacity-80 rotate-1" : ""}
                                >
                                  {isCollapsed ? (
                                    <CompactExpenseCard expense={expense} />
                                  ) : (
                                    <ExpenseCard expense={expense} />
                                  )}
                                </div>
                              )}
                            </Draggable>
                          ))}
                          {provided.placeholder}
                          {items.length === 0 && (
                            <div className="flex items-center justify-center h-20 text-xs text-muted-foreground">
                              Нет заявок
                            </div>
                          )}
                        </div>
                      )}
                    </Droppable>
                  </div>
                );
              })}
            </div>
          </DragDropContext>
        </div>

        {/* Approval Sidebar — for admin, CFO and CEO */}
        {(isAdmin || store.isSeniorFinancier() || store.isCeo()) && (
          <aside className="w-72 shrink-0 space-y-3">
            <div className="flex items-center gap-2 mb-2">
              <UserCheck className="w-4 h-4 text-violet-500" />
              <h2 className="text-sm font-semibold text-foreground">Согласования (CFO / Ganiev)</h2>
            </div>
            {APPROVAL_STATUS_GROUPS.map(({ label, statuses }) => {
              const items = expenses.filter((e) => statuses.includes(e.status));
              return (
                <div key={label} className="rounded-xl border bg-card overflow-hidden">
                  <div className="flex items-center justify-between px-3 py-2 bg-muted/40 border-b">
                    <span className="text-xs font-semibold">{label}</span>
                    <span className="text-xs font-medium bg-foreground/10 px-2 py-0.5 rounded-full">{items.length}</span>
                  </div>
                  <div className="p-2 space-y-1.5 max-h-48 overflow-y-auto">
                    {items.length === 0 ? (
                      <p className="text-xs text-muted-foreground text-center py-3">Пусто</p>
                    ) : (
                      items.map((e) => (
                        <div key={e.id} className="text-xs px-2 py-1.5 rounded-lg bg-background border hover:bg-accent/30 cursor-pointer transition-colors">
                          <p className="font-mono font-bold">{e.requestId}</p>
                          <p className="text-muted-foreground truncate">{e.createdBy} — {Number(e.totalAmount).toLocaleString()} {e.currency}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </aside>
        )}
      </div>
    </div>
  );
};

export default Applications;
