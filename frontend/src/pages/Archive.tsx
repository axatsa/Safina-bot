import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { ExpenseRequest } from "@/lib/types";
import { Button } from "@/components/ui/button";
import FilterBar from "@/components/FilterBar";
import { Download, ExternalLink, Loader2, Archive as ArchiveIcon } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";


const Archive = () => {
  const navigate = useNavigate();
  const [selectedProject, setSelectedProject] = useState("all");
  const [selectedUser, setSelectedUser] = useState("all");
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("all");

  const { data: expensesPage, isLoading, isError } = useQuery({
    queryKey: ["expenses", { limit: 100, status: "archived" }],
    queryFn: () => store.getExpenses({ limit: 100, status: "archived" }),
    refetchInterval: 60000, // Refresh every minute
  });
  const expenses = expensesPage?.items ?? [];

  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: () => store.getProjects(),
  });

  const { data: team = [] } = useQuery({
    queryKey: ["team"],
    queryFn: () => store.getTeam(),
  });

  const filtered = expenses.filter((e) => {
    // Note: status filter is now redundant if we filter on backend, 
    // but kept for safety if backend doesn't support status param.
    if (e.status !== "archived") return false;
    
    // Filter by tab 
    if (activeTab === "refunds") {
      if (e.requestType !== "refund" && e.requestType !== "blank_refund") return false;
    } else if (activeTab === "expenses") {
      if (e.requestType === "refund" || e.requestType === "blank_refund") return false;
    }
    
    if (selectedProject !== "all" && e.projectId !== selectedProject) return false;
    if (selectedUser !== "all" && e.createdById !== selectedUser) return false;
    if (dateRange.from && new Date(e.date) < dateRange.from) return false;
    if (dateRange.to) {
      const end = new Date(dateRange.to);
      end.setHours(23, 59, 59);
      if (new Date(e.date) > end) return false;
    }
    if (searchQuery && !e.requestId.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const totalRefundAmount = filtered.reduce((acc, curr) => acc + Number(curr.totalAmount || 0), 0);

  const handleExport = (allStatuses: boolean) => {
    store.exportXLSX({
      project: selectedProject,
      user: selectedUser,
      from: dateRange.from?.toISOString(),
      to: dateRange.to?.toISOString(),
      allStatuses: true
    });
  };


  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col h-[80vh] items-center justify-center space-y-4">
        <p className="text-destructive font-medium">Ошибка при загрузке архива</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Попробовать снова
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 animate-slide-in">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Отчёты</h1>
        <p className="text-sm text-muted-foreground mt-1">Завершённые заявки и экспорт данных</p>
      </div>

      <Tabs defaultValue="all" value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-4 bg-muted/50 p-1 border">
          <TabsTrigger value="all" className="rounded-md">Все отчёты</TabsTrigger>
          <TabsTrigger value="expenses" className="rounded-md">Только расходы</TabsTrigger>
          <TabsTrigger value="refunds" className="rounded-md">Возвраты</TabsTrigger>
        </TabsList>
      </Tabs>

      {activeTab === "refunds" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="bg-gradient-to-br from-rose-500 to-red-600 text-white border-0 shadow-md">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-white/80">Общая сумма возвратов</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold font-display">
                {totalRefundAmount.toLocaleString()} UZS
              </div>
              <p className="text-xs text-white/70 mt-1">За выбранный период и фильтры</p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-slate-800 to-slate-900 text-white border-0 shadow-md">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-white/80">Количество возвратов</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold font-display">
                {filtered.length}
              </div>
              <p className="text-xs text-white/70 mt-1">Завершенных заявок на возврат</p>
            </CardContent>
          </Card>
        </div>
      )}

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

      <div className="glass-card rounded-2xl border overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b bg-muted/30">
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">ID</th>
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Дата</th>
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Проект</th>
              <th className="px-6 py-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Ответственный</th>
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
                  {format(new Date(expense.date), "yyyy-MM-dd HH:mm", { locale: ru })}
                </td>
                <td className="px-6 py-4 text-sm font-medium">
                  {expense.projectName}
                </td>
                <td className="px-6 py-4 text-sm">
                  {expense.createdBy}
                </td>
                <td className="px-6 py-4 text-right font-display font-bold text-sm">
                  {Number(expense.totalAmount || 0).toLocaleString()} {expense.currency}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <Button variant="ghost" size="icon" onClick={() => store.exportDocx(expense.id)}>
                      <Download className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => navigate(`/dashboard/expense/${expense.id}`)}>
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6}>
                  <EmptyState 
                    icon={ArchiveIcon}
                    title="Отчёты пусты"
                    subtitle="Завершённые заявки появятся здесь после обработки"
                  />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Archive;
