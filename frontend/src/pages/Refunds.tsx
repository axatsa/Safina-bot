import { useState, useMemo, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { ExpenseRequest, ExpenseStatus, STATUS_LABELS } from "@/lib/types";
import CompactExpenseCard from "@/components/CompactExpenseCard";
import ExpenseCard from "@/components/ExpenseCard";
import { 
  Loader2, RefreshCw, Download, 
  ClipboardList, ChevronDown, ChevronRight 
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { DragDropContext, Droppable, Draggable, DropResult } from "@hello-pangea/dnd";
import { toast } from "sonner";

const COLUMN_DEFS = [
  {
    id: "new",
    label: "Новые заявления",
    statuses: ["request", "review", "revision"] as ExpenseStatus[],
    color: "bg-orange-500",
    headerClass: "bg-gradient-to-br from-orange-500 to-amber-500 text-white border-transparent shadow-sm"
  },
  {
    id: "cfo",
    label: "На согласовании CFO",
    statuses: ["pending_senior", "pending_ceo"] as ExpenseStatus[],
    color: "bg-blue-500",
    headerClass: "bg-gradient-to-br from-blue-600 to-indigo-600 text-white border-transparent shadow-sm"
  },
  {
    id: "completed",
    label: "Утверждено / Оплачено",
    statuses: ["approved_senior", "approved_ceo", "confirmed"] as ExpenseStatus[],
    color: "bg-emerald-500",
    headerClass: "bg-gradient-to-br from-emerald-500 to-teal-600 text-white border-transparent shadow-sm"
  },
  {
    id: "rejected",
    label: "Отклонено",
    statuses: ["declined", "rejected_senior", "rejected_ceo"] as ExpenseStatus[],
    color: "bg-rose-500",
    headerClass: "bg-gradient-to-br from-rose-500 to-red-600 text-white border-transparent shadow-sm"
  }
];

const Refunds = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [collapsedColumns, setCollapsedColumns] = useState<Record<string, boolean>>({});

  const { data: expensesPage, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["expenses-refunds"],
    queryFn: () => store.getExpenses({ 
      limit: 1000, // Fetch all for kanban
    }),
    refetchInterval: 30000,
  });

  const refunds = useMemo(() => {
    const items = expensesPage?.items ?? [];
    return items.filter(
      (e) => (e.requestType === "refund" || e.requestType === "blank_refund") && e.status !== "archived"
    );
  }, [expensesPage]);

  const filtered = useMemo(() => {
    if (!search) return refunds;
    const q = search.toLowerCase();
    return refunds.filter((e) =>
      e.requestId?.toLowerCase().includes(q) ||
      e.createdBy?.toLowerCase().includes(q) ||
      e.purpose?.toLowerCase().includes(q)
    );
  }, [refunds, search]);

  const mutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ExpenseStatus }) =>
      store.updateExpenseStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses-refunds"] });
      toast.success("Статус обновлен");
    },
    onError: () => {
      toast.error("Не удалось обновить статус");
    }
  });

  const handleDragEnd = (result: DropResult) => {
    const { draggableId, destination } = result;
    if (!destination) return;

    // Find which status to assign based on column
    const column = COLUMN_DEFS.find(c => c.id === destination.droppableId);
    if (!column) return;

    const item = refunds.find(r => r.id === draggableId);
    if (!item) return;

    // Use the first status of the column as the target, 
    // but only if the item isn't already in one of the column's statuses
    if (!column.statuses.includes(item.status)) {
        const newStatus = column.statuses[0];
        
        if (newStatus === "declined" || newStatus === "revision") {
            toast.info("Для этого статуса требуется комментарий. Откройте детали заявления.");
            return;
        }
        
        mutation.mutate({ id: draggableId, status: newStatus });
    }
  };

  const toggleColumn = (id: string) => {
    setCollapsedColumns(prev => ({ ...prev, [id]: !prev[id] }));
  };

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
          <p className="text-sm text-muted-foreground mt-1">Канбан-доска заявлений на возврат</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => store.exportXLSX({ allStatuses: true, project: 'all' })}>
            <Download className="w-4 h-4 mr-2" />
            Экспорт
          </Button>
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Обновить
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск по ID, автору или назначению..."
          className="w-full max-w-md px-4 py-2 text-sm rounded-xl border bg-background focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4 -mx-6 px-6 min-h-[calc(100vh-250px)]">
        <DragDropContext onDragEnd={handleDragEnd}>
          {COLUMN_DEFS.map((column) => {
            const items = filtered.filter(f => column.statuses.includes(f.status));
            const isCollapsed = !!collapsedColumns[column.id];

            return (
              <div 
                key={column.id} 
                className={`flex flex-col rounded-xl border bg-muted/30 shrink-0 transition-all duration-300 ${isCollapsed ? 'w-12 basis-12' : 'w-80 lg:w-auto lg:flex-1 lg:min-w-[280px]'}`}
              >
                <div 
                    className={`flex items-center gap-2 px-3 py-2.5 rounded-t-xl border-b font-display font-bold text-xs uppercase tracking-wider ${column.headerClass} ${isCollapsed ? 'flex-col py-4' : ''}`}
                    onClick={() => toggleColumn(column.id)}
                    role="button"
                >
                    {isCollapsed ? (
                        <ChevronRight className="w-4 h-4" />
                    ) : (
                        <ChevronDown className="w-4 h-4" />
                    )}
                    <span className={isCollapsed ? 'vertical-text mt-4' : ''}>{column.label}</span>
                    {!isCollapsed && (
                        <span className="ml-auto bg-white/20 px-2 py-0.5 rounded-full text-[10px]">
                            {items.length}
                        </span>
                    )}
                </div>

                {!isCollapsed && (
                    <Droppable droppableId={column.id}>
                        {(provided, snapshot) => (
                            <div
                                ref={provided.innerRef}
                                {...provided.droppableProps}
                                className={`flex-1 p-2 space-y-3 transition-colors ${snapshot.isDraggingOver ? 'bg-primary/5' : ''}`}
                            >
                                {items.map((refund, index) => (
                                    <Draggable key={refund.id} draggableId={refund.id} index={index}>
                                        {(dragProvided, dragSnapshot) => (
                                            <div
                                                ref={dragProvided.innerRef}
                                                {...dragProvided.draggableProps}
                                                {...dragProvided.dragHandleProps}
                                                className={dragSnapshot.isDragging ? "opacity-80 rotate-1 scale-105" : ""}
                                            >
                                                <ExpenseCard expense={refund} />
                                            </div>
                                        )}
                                    </Draggable>
                                ))}
                                {provided.placeholder}
                                {items.length === 0 && (
                                    <div className="flex flex-col items-center justify-center py-12 text-center opacity-30 select-none">
                                        <ClipboardList className="w-10 h-10 mb-2" />
                                        <p className="text-xs font-medium">Пусто</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </Droppable>
                )}
              </div>
            );
          })}
        </DragDropContext>
      </div>

      <style>{`
        .vertical-text {
            writing-mode: vertical-rl;
            text-orientation: mixed;
            transform: rotate(180deg);
        }
      `}</style>
    </div>
  );
};

export default Refunds;

