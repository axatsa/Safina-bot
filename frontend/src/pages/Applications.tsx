import { useState, useMemo } from "react";
import { store } from "@/lib/store";
import { ExpenseRequest, ExpenseStatus, KANBAN_STATUSES, STATUS_LABELS } from "@/lib/types";
import ExpenseCard from "@/components/ExpenseCard";
import CompactExpenseCard from "@/components/CompactExpenseCard";
import FilterBar from "@/components/FilterBar";
import { ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { DragDropContext, Droppable, Draggable, DropResult } from "@hello-pangea/dnd";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const kanbanColors: Record<string, string> = {
  request: "kanban-request",
  review: "kanban-review",
  confirmed: "kanban-confirmed",
  declined: "kanban-declined",
  revision: "kanban-revision",
};

const Applications = () => {
  const queryClient = useQueryClient();
  const [selectedProject, setSelectedProject] = useState("all");
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [collapsedColumns, setCollapsedColumns] = useState<Record<string, boolean>>({});

  // Fecthing expenses via React Query
  const { data: expenses = [], isLoading } = useQuery({
    queryKey: ["expenses"],
    queryFn: () => store.getExpenses(),
  });

  // Fetching projects
  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: () => store.getProjects(),
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
      if (e.status === "archived") return false;
      if (selectedProject !== "all" && e.projectId !== selectedProject) return false;
      if (dateRange.from && new Date(e.date) < dateRange.from) return false;
      if (dateRange.to) {
        const end = new Date(dateRange.to);
        end.setHours(23, 59, 59);
        if (new Date(e.date) > end) return false;
      }
      if (searchQuery && !e.requestId.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [expenses, selectedProject, dateRange, searchQuery]);

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
    store.exportCSV({
      project: selectedProject,
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
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        onExport={handleExport}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

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
                      className={`p-2 space-y-2 min-h-[120px] transition-colors ${snapshot.isDraggingOver ? "bg-accent/30" : ""
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
  );
};

export default Applications;
