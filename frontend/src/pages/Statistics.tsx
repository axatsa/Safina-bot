import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { store } from "@/lib/store";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, TrendingUp, AlertCircle, FileText, CheckCircle, PieChart as PieChartIcon, Filter, X, Building2 } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];
const COLORS_REFUNDS = ['#f43f5e', '#fb923c', '#facc15', '#a78bfa', '#34d399', '#60a5fa', '#f472b6'];

const DonutChart = ({
  data,
  title,
  subtitle,
  colors,
}: {
  data: any[];
  title: string;
  subtitle: string;
  colors: string[];
}) => (
  <Card className="shadow-sm border-0 ring-1 ring-border rounded-2xl bg-card/60 backdrop-blur-xl flex flex-col">
    <CardHeader className="border-b bg-muted/20 pb-4">
      <CardTitle className="text-xl font-display font-semibold">{title}</CardTitle>
      <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
    </CardHeader>
    <CardContent className="flex-1 flex items-center justify-center p-6 pb-2">
      {data?.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={110}
              paddingAngle={4}
              dataKey="value"
              stroke="none"
            >
              {data.map((_: any, index: number) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => formatCurrency(Math.round(value), "UZS")}
              contentStyle={{ borderRadius: '12px', border: '1px solid hsl(var(--border))', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
            />
            <Legend wrapperStyle={{ paddingTop: '10px' }} />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex flex-col items-center justify-center text-muted-foreground h-[300px]">
          <PieChartIcon className="w-16 h-16 mb-4 opacity-20" />
          <p className="text-sm font-medium">Нет данных за этот период</p>
        </div>
      )}
    </CardContent>
  </Card>
);

const Statistics = () => {
    const [period, setPeriod] = useState("1m");
    const [segment, setSegment] = useState("branch");
    const [requestType, setRequestType] = useState("all");
    const [selectedBranchNames, setSelectedBranchNames] = useState<string[]>([]);
    const [selectedProjectIds, setSelectedProjectIds] = useState<string[]>([]);

    const { data: projects = [] } = useQuery({
        queryKey: ["all-projects"],
        queryFn: () => store.getProjects(),
    });

    const { data: analytics, isLoading } = useQuery({
        queryKey: ["analytics", period, segment, requestType, selectedBranchNames, selectedProjectIds],
        queryFn: () => store.getAnalytics({ 
            period, 
            segment, 
            type: requestType, 
            branchNames: selectedBranchNames,
            projectIds: selectedProjectIds
        }),
    });

    const getAvailableBranches = () => {
        if (selectedProjectIds.length === 0) {
            return projects.flatMap((p: any) => p.branches || []).map((b: any) => b.name);
        }
        return projects
            .filter((p: any) => selectedProjectIds.includes(p.id))
            .flatMap((p: any) => p.branches || [])
            .map((b: any) => b.name);
    };

    const availableBranches: string[] = Array.from(new Set(getAvailableBranches())).filter(Boolean) as string[];

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    const { timeline = [], distribution = [], expense_distribution, refund_distribution, summary = {} } = analytics || {};

    // Если бэкенд ещё не возвращает разделённые данные — используем distribution как запасной вариант
    const expenseDist: any[] = expense_distribution ?? distribution;
    const refundDist: any[] = refund_distribution ?? [];

    return (
        <div className="p-6 space-y-8 animate-slide-in pb-20">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b pb-6">
                <div>
                    <h1 className="text-3xl font-display font-bold text-foreground tracking-tight">Аналитика</h1>
                    <p className="text-muted-foreground mt-2">Финансовые показатели, расходы и статистика возвратов</p>
                </div>

                <div className="flex flex-col sm:flex-row items-end sm:items-center gap-3">
                    <Tabs defaultValue="all" value={requestType} onValueChange={setRequestType} className="w-full sm:w-auto">
                        <TabsList className="bg-muted/50 border mb-0">
                            <TabsTrigger value="all">Все заявки</TabsTrigger>
                            <TabsTrigger value="expense">Расходы</TabsTrigger>
                            <TabsTrigger value="refund">Возвраты</TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                <div className="flex flex-wrap items-center gap-3">
                    <Popover>
                        <PopoverTrigger asChild>
                            <Button variant="outline" className="h-10 border-primary/20 bg-background px-4 rounded-xl shadow-sm ring-1 ring-primary/5 hover:ring-primary/20 transition-all min-w-[240px] justify-between">
                                <span className="flex items-center gap-2">
                                    <Building2 className="w-4 h-4 text-primary" />
                                    <span className="text-sm font-medium">
                                        {selectedProjectIds.length === 0 && selectedBranchNames.length === 0 
                                            ? "Объекты аналитики" 
                                            : `${selectedProjectIds.length} пр. / ${selectedBranchNames.length} фил.`}
                                    </span>
                                </span>
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-[320px] p-0 rounded-2xl shadow-xl border-primary/10 overflow-hidden" align="end">
                            <div className="p-4 border-b bg-muted/20">
                                <div className="flex items-center justify-between">
                                    <h3 className="font-semibold text-sm">Проекты и филиалы</h3>
                                    {(selectedProjectIds.length > 0 || selectedBranchNames.length > 0) && (
                                        <Button 
                                            variant="ghost" 
                                            size="sm" 
                                            onClick={() => { setSelectedProjectIds([]); setSelectedBranchNames([]); }}
                                            className="h-8 text-xs text-destructive hover:text-destructive hover:bg-destructive/10"
                                        >
                                            Сбросить
                                        </Button>
                                    )}
                                </div>
                            </div>
                            <div className="max-h-[400px] overflow-y-auto p-2 space-y-2">
                                {projects.map((project) => (
                                    <div key={project.id} className="space-y-1">
                                        <div 
                                            className="flex items-center space-x-3 p-2 rounded-xl hover:bg-primary/5 cursor-pointer transition-colors group"
                                            onClick={() => {
                                                const isSelected = selectedProjectIds.includes(project.id);
                                                setSelectedProjectIds(prev => 
                                                    isSelected ? prev.filter(id => id !== project.id) : [...prev, project.id]
                                                );
                                                // If unchecking project, also uncheck its branches
                                                if (isSelected && project.branches) {
                                                    const pBranchNames = project.branches.map((b: any) => b.name);
                                                    setSelectedBranchNames(prev => prev.filter(name => !pBranchNames.includes(name)));
                                                }
                                            }}
                                        >
                                            <Checkbox 
                                                id={`project-${project.id}`}
                                                checked={selectedProjectIds.includes(project.id)}
                                                onCheckedChange={() => {}} 
                                                className="data-[state=checked]:bg-primary"
                                            />
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-bold truncate group-hover:text-primary transition-colors">{project.name}</p>
                                            </div>
                                        </div>
                                        
                                        {project.branches && project.branches.length > 0 && (
                                            <div className="pl-6 space-y-1 border-l ml-4 border-primary/20">
                                                {project.branches.map((branch: any) => (
                                                    <div 
                                                        key={branch.id} 
                                                        className="flex items-center space-x-3 p-1.5 rounded-lg hover:bg-muted cursor-pointer transition-colors group/branch"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setSelectedBranchNames(prev => 
                                                                prev.includes(branch.name) 
                                                                ? prev.filter(b => b !== branch.name) 
                                                                : [...prev, branch.name]
                                                            );
                                                        }}
                                                    >
                                                        <Checkbox 
                                                            checked={selectedBranchNames.includes(branch.name)}
                                                            onCheckedChange={() => {}} 
                                                            className="w-3.5 h-3.5"
                                                        />
                                                        <span className="text-xs truncate group-hover/branch:text-foreground">{branch.name}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </PopoverContent>
                    </Popover>

                    <Select value={period} onValueChange={setPeriod}>
                        <SelectTrigger className="w-[160px] bg-background shadow-sm rounded-xl">
                            <SelectValue placeholder="Период" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="1m">За месяц</SelectItem>
                            <SelectItem value="3m">За 3 месяца</SelectItem>
                            <SelectItem value="6m">За полгода</SelectItem>
                            <SelectItem value="1y">За год</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="relative overflow-hidden border-0 shadow-lg rounded-2xl bg-gradient-to-br from-orange-500 to-amber-500 text-white">
                    <div className="absolute top-0 right-0 p-4 opacity-20">
                        <TrendingUp className="w-16 h-16" />
                    </div>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-white/80">Ожидают обработки</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold tracking-tight">{summary.Pending || 0}</div>
                        <p className="text-sm text-white/80 mt-2 font-medium">заявок в обработке</p>
                    </CardContent>
                </Card>

                <Card className="relative overflow-hidden border-0 shadow-lg rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white">
                    <div className="absolute top-0 right-0 p-4 opacity-20">
                        <FileText className="w-16 h-16" />
                    </div>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-white/80">Одобрено CFO</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold tracking-tight">{summary.Approved || 0}</div>
                        <p className="text-sm text-white/80 mt-2 font-medium">ожидают оплаты</p>
                    </CardContent>
                </Card>

                <Card className="relative overflow-hidden border-0 shadow-lg rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
                    <div className="absolute top-0 right-0 p-4 opacity-20">
                        <CheckCircle className="w-16 h-16" />
                    </div>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-white/80">Успешно оплачено</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold tracking-tight">{summary.Confirmed || 0}</div>
                        <p className="text-sm text-white/80 mt-2 font-medium">закрытых расходов</p>
                    </CardContent>
                </Card>

                <Card className="relative overflow-hidden border-0 shadow-lg rounded-2xl bg-gradient-to-br from-rose-500 to-red-600 text-white">
                    <div className="absolute top-0 right-0 p-4 opacity-20">
                        <AlertCircle className="w-16 h-16" />
                    </div>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-white/80">Отклонено</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold tracking-tight">{summary.Rejected || 0}</div>
                        <p className="text-sm text-white/80 mt-2 font-medium">отказано финансистом / CEO</p>
                    </CardContent>
                </Card>
            </div>

            {/* Линейный график */}
            <Card className="shadow-sm border-0 ring-1 ring-border rounded-2xl bg-card/60 backdrop-blur-xl">
                <CardHeader className="border-b bg-muted/20 pb-4">
                    <CardTitle className="text-xl font-display font-semibold">Динамика трафика (UZS)</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">Динамика расходов и возвратов по времени</p>
                </CardHeader>
                <CardContent className="h-[400px] pt-6">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={timeline} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--muted))" />
                            <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                            <YAxis
                                stroke="hsl(var(--muted-foreground))"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={(val) => `${(val / 1000000).toFixed(0)} млн`}
                                dx={-10}
                            />
                            <Tooltip
                                formatter={(value: number, name: string) => [
                                    formatCurrency(Math.round(value), "UZS"),
                                    name === "expenses" ? "Расходы" : "Возвраты"
                                ]}
                                contentStyle={{ borderRadius: '12px', border: '1px solid hsl(var(--border))', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                            />
                            <Legend
                                wrapperStyle={{ paddingTop: '20px' }}
                                formatter={(value) => value === "expenses" ? "Расходы" : "Возвраты"}
                            />
                            <Line type="monotone" dataKey="expenses" name="expenses" stroke="#0ea5e9" strokeWidth={4} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 8 }} />
                            <Line type="monotone" dataKey="refunds" name="refunds" stroke="#f43f5e" strokeWidth={4} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 8 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            {/* Два отдельных донат-графика */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                {(requestType === "all" || requestType === "expense") && (
                    <DonutChart
                        data={expenseDist}
                        title="Структура расходов"
                        subtitle="Долевое распределение по расходам"
                        colors={COLORS}
                    />
                )}
                {(requestType === "all" || requestType === "refund") && (
                    <DonutChart
                        data={refundDist}
                        title="Структура возвратов"
                        subtitle="Долевое распределение по возвратам"
                        colors={COLORS_REFUNDS}
                    />
                )}
            </div>
        </div>
    );
};

export default Statistics;
