import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { store } from "@/lib/store";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, TrendingUp, AlertCircle, FileText, CheckCircle } from "lucide-react";

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

const Statistics = () => {
    const [period, setPeriod] = useState("1m");
    const [segment, setSegment] = useState("global");

    const { data: analytics, isLoading } = useQuery({
        queryKey: ["analytics", period, segment],
        queryFn: () => store.getAnalytics({ period, segment }),
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
        <div className="p-6 space-y-8 animate-slide-in">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-display font-bold text-foreground">Статистика</h1>
                    <p className="text-sm text-muted-foreground mt-1">Аналитика расходов и возвратов</p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                    <Select value={period} onValueChange={setPeriod}>
                        <SelectTrigger className="w-[150px] bg-background">
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
                        <SelectTrigger className="w-[180px] bg-background">
                            <SelectValue placeholder="Сегментация" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="global">Глобально (Филиалы)</SelectItem>
                            <SelectItem value="branch">По филиалам</SelectItem>
                            <SelectItem value="project">По проектам</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="glass-card shadow-sm border-0 ring-1 ring-black/5">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Ожидают</CardTitle>
                        <TrendingUp className="w-4 h-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary.Pending || 0}</div>
                        <p className="text-xs text-muted-foreground mt-1">заявок в обработке</p>
                    </CardContent>
                </Card>
                <Card className="glass-card shadow-sm border-0 ring-1 ring-black/5">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Одобрено СФ</CardTitle>
                        <FileText className="w-4 h-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary.Approved || 0}</div>
                        <p className="text-xs text-muted-foreground mt-1">ожидают оплаты</p>
                    </CardContent>
                </Card>
                <Card className="glass-card shadow-sm border-0 ring-1 ring-black/5">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Подтверждено</CardTitle>
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary.Confirmed || 0}</div>
                        <p className="text-xs text-muted-foreground mt-1">успешно оплачено</p>
                    </CardContent>
                </Card>
                <Card className="glass-card shadow-sm border-0 ring-1 ring-black/5">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Отклонено</CardTitle>
                        <AlertCircle className="w-4 h-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-500">{summary.Rejected || 0}</div>
                        <p className="text-xs text-muted-foreground mt-1">отказано финансистом</p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="lg:col-span-2 glass-card shadow-sm border-0 ring-1 ring-black/5">
                    <CardHeader>
                        <CardTitle className="text-lg">Динамика трафика</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[350px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={timeline} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis dataKey="date" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${(val / 1000000).toFixed(1)}M`} />
                                <Tooltip
                                    formatter={(value: number) => new Intl.NumberFormat('ru-RU').format(value) + ' UZS'}
                                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />
                                <Legend />
                                <Line type="monotone" dataKey="expenses" name="Расходы" stroke="#00C49F" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                                <Line type="monotone" dataKey="refunds" name="Возвраты" stroke="#FF8042" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                <Card className="glass-card shadow-sm border-0 ring-1 ring-black/5">
                    <CardHeader>
                        <CardTitle className="text-lg">Структура (UZS)</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[350px] flex items-center justify-center">
                        {distribution.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={distribution}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {distribution.map((_: any, index: number) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip formatter={(value: number) => new Intl.NumberFormat('ru-RU').format(value) + ' UZS'} />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="text-sm text-muted-foreground text-center">Нет данных для выбранного периода</div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Statistics;
