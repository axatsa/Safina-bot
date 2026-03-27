import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { store } from "@/lib/store";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, TrendingUp, AlertCircle, FileText, CheckCircle } from "lucide-react";

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

const Statistics = () => {
    const [period, setPeriod] = useState("1m");
    const [segment, setSegment] = useState("global");
    const [requestType, setRequestType] = useState("all");

    const { data: analytics, isLoading } = useQuery({
        queryKey: ["analytics", period, segment, requestType],
        queryFn: () => store.getAnalytics({ period, segment, type: requestType }),
    });

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    const { timeline = [], distribution = [], summary = {} } = analytics || {};

    return (
        <div className="p-6 space-y-8 animate-slide-in pb-20">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b pb-6">
                <div>
                    <h1 className="text-3xl font-display font-bold text-foreground tracking-tight">Статистика и Аналитика</h1>
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

                    <Select value={segment} onValueChange={setSegment}>
                        <SelectTrigger className="w-[200px] bg-background shadow-sm rounded-xl">
                            <SelectValue placeholder="Сегментация" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="global">Все филиалы</SelectItem>
                            <SelectItem value="branch">По филиалам</SelectItem>
                            <SelectItem value="project">По проектам</SelectItem>
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

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                <Card className="xl:col-span-2 shadow-sm border-0 ring-1 ring-border rounded-2xl bg-card/60 backdrop-blur-xl">
                    <CardHeader className="border-b bg-muted/20 pb-4">
                        <CardTitle className="text-xl font-display font-semibold">Динамика трафика (UZS)</CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">Отношение классических расходов к возвратам по времени</p>
                    </CardHeader>
                    <CardContent className="h-[400px] pt-6">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={timeline} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--muted))" />
                                <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${(val / 1000000).toFixed(1)}M`} dx={-10} />
                                <Tooltip
                                    formatter={(value: number) => new Intl.NumberFormat('ru-RU').format(value) + ' UZS'}
                                    contentStyle={{ borderRadius: '12px', border: '1px solid hsl(var(--border))', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                                <Line type="monotone" dataKey="expenses" name="Расходы" stroke="#0ea5e9" strokeWidth={4} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 8 }} />
                                <Line type="monotone" dataKey="refunds" name="Возвраты" stroke="#f43f5e" strokeWidth={4} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 8 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                <Card className="shadow-sm border-0 ring-1 ring-border rounded-2xl bg-card/60 backdrop-blur-xl flex flex-col">
                    <CardHeader className="border-b bg-muted/20 pb-4">
                        <CardTitle className="text-xl font-display font-semibold">Структура (UZS)</CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">Долевое распределение расходов</p>
                    </CardHeader>
                    <CardContent className="flex-1 flex items-center justify-center p-6 pb-2">
                        {distribution?.length > 0 ? (
                            <ResponsiveContainer width="100%" height={320}>
                                <PieChart>
                                    <Pie
                                        data={distribution}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={80}
                                        outerRadius={120}
                                        paddingAngle={4}
                                        dataKey="value"
                                        stroke="none"
                                    >
                                        {distribution.map((_: any, index: number) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip 
                                        formatter={(value: number) => new Intl.NumberFormat('ru-RU').format(value) + ' UZS'} 
                                        contentStyle={{ borderRadius: '12px', border: '1px solid hsl(var(--border))', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex flex-col items-center justify-center text-muted-foreground h-[320px]">
                                <PieChart className="w-16 h-16 mb-4 opacity-20" />
                                <p className="text-sm font-medium">Нет данных за этот период</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Statistics;
