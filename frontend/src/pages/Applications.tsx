import { useState, useMemo, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { ExpenseRequest, ExpenseStatus, KANBAN_STATUSES, APPROVAL_STATUSES, STATUS_LABELS } from "@/lib/types";
import ExpenseCard from "@/components/ExpenseCard";
import CompactExpenseCard from "@/components/CompactExpenseCard";
import FilterBar from "@/components/FilterBar";
import { ChevronDown, ChevronRight, Loader2, DollarSign, FileText, Clock, CheckCircle, UserCheck, ExternalLink } from "lucide-react";
import { DragDropContext, Droppable, Draggable, DropResult } from "@hello-pangea/dnd";
import { useQuery, useMutation, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import { toast } from "sonner";

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
  const navigate = useNavigate();
  const [selectedProject, setSelectedProject] = useState("all");
  const [selectedUser, setSelectedUser] = useState("all");
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [collapsedColumns, setCollapsedColumns] = useState<Record<string, boolean>>({});

  const [skip, setSkip] = useState(0);
  const [allExpenses, setAllExpenses] = useState<ExpenseRequest[]>([]);
  const LIMIT = 50;

  // Fecthing expenses via React Query
  const { data: expensesPage, isLoading, isFetching } = useQuery({
    queryKey: ["expenses", skip],
    queryFn: () => store.getExpenses({ skip, limit: LIMIT }),
    refetchInterval: 10000,
    placeholderData: keepPreviousData,
  });

  // Reset pagination when filters change
  useEffect(() => {
    setSkip(0);
    setAllExpenses([]);
  }, [selectedProject, selectedUser, searchQuery, dateRange]);

  // Accumulate items when pages are loaded
  useEffect(() => {
    if (expensesPage?.items) {
      if (skip === 0) {
        setAllExpenses(expensesPage.items);
      } else {
        setAllExpenses(prev => {
          // Prevent duplicates if query refetches
          const existingIds = new Set(prev.map(e => e.id));
          const newItems = expensesPage!.items.filter(e => !existingIds.has(e.id));
          return [...prev, ...newItems];
        });
      }
    }
  }, [expensesPage, skip]);

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
    return allExpenses.filter((e) => {
      // Basic Status Filter (Archive is separate)
      if (e.status === "archived") return false;

      // Filter out refunds from main dashboard
      const isRefund = e.requestType === "refund" || 
                       (e as any).request_type === "refund" || 
                       (e.purpose && e.purpose.toLowerCase().includes("возврат"));
      
      if (isRefund) return false;

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
    const item = allExpenses.find(e => e.id === draggableId);

    if (item && item.status !== newStatus) {
      if (newStatus === "declined" || newStatus === "revision") {
        toast.info("Для этого статуса требуется комментарий. Откройте детали инвестиции.");
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

  // ── JSX: standard kanban for admin / user ─────────────────────────────────
  return (
    <div className="p-6 space-y-6 animate-slide-in">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Инвестиции</h1>
        <p className="text-sm text-muted-foreground mt-1">Управление инвестициями на расход</p>
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
            <p className="text-sm font-medium text-muted-foreground">Всего инвестиций</p>
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

      {/* Main area: kanban */}
      <div className="flex gap-4">
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
                              Нет инвестиций
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
      </div>

      {/* Pagination Footer */}
      <div className="flex flex-col items-center gap-4 py-6 border-t mt-6">
        <p className="text-sm text-muted-foreground">
          Показано {allExpenses.length} из {expensesPage?.total ?? 0} инвестиций
        </p>
        
        {expensesPage?.has_more && (
          <button
            onClick={() => setSkip(prev => prev + LIMIT)}
            disabled={isFetching}
            className="flex items-center gap-2 px-8 py-2.5 rounded-lg border bg-background hover:bg-accent transition-colors disabled:opacity-50"
          >
            {isFetching ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Загрузка...</span>
              </>
            ) : (
              <span>Загрузить ещё</span>
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export default Applications;
