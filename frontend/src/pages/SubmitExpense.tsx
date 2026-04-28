import { useState } from "react";
import { store } from "@/lib/store";
import { Project, ExpenseItem } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Plus,
    Trash2,
    Send,
    Loader2,
    ArrowLeft,
    FilePlus,
    RotateCcw,
    FileText,
    Landmark,
    GraduationCap,
    Building2,
    ArrowRight
} from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/** Format a number as "1 000 000" with spaces */
const formatAmount = (value: number): string => {
    if (!value && value !== 0) return "";
    return value.toLocaleString("ru-RU");
};

type ItemWithDisplay = ExpenseItem & { displayAmount: string; displayQuantity: string };

const emptyItem = (currency: "UZS" | "USD" | "RUB" = "UZS"): ItemWithDisplay => ({
    name: "",
    quantity: 1,
    unit: "кг",
    amount: 0,
    currency,
    displayAmount: "",
    displayQuantity: "1",
});

const APPLICATION_TYPES = [
    {
        id: "expense",
        title: "Инвестиция",
        desc: "Стандартный запрос на расход / закупку ТМЦ",
        icon: FilePlus,
        color: "text-blue-600",
        bg: "bg-blue-50",
        path: "/submit?type=expense"
    },
    {
        id: "refund",
        title: "Заявление на возврат",
        desc: "Форма заявления на возврат денег клиенту",
        icon: RotateCcw,
        color: "text-rose-600",
        bg: "bg-rose-50",
        path: "/blank?template=refund"
    },
    {
        id: "ls",
        title: "Служебная записка",
        desc: "Общий бланк служебной записки (LS)",
        icon: FileText,
        color: "text-amber-600",
        bg: "bg-amber-50",
        path: "/blank?template=ls"
    },
    {
        id: "land",
        title: "Бланк LAND",
        desc: "Форма для проекта LAND",
        icon: Building2,
        color: "text-emerald-600",
        bg: "bg-emerald-50",
        path: "/blank?template=land"
    },
    {
        id: "drujba",
        title: "Бланк DRUJBA",
        desc: "Форма для проекта DRUJBA",
        icon: Landmark,
        color: "text-indigo-600",
        bg: "bg-indigo-50",
        path: "/blank?template=drujba"
    },
    {
        id: "school",
        title: "Бланк SCHOOL",
        desc: "Форма для общеобразовательной школы",
        icon: GraduationCap,
        color: "text-violet-600",
        bg: "bg-violet-50",
        path: "/blank?template=school"
    },
];

const SelectionScreen = ({ chatId }: { chatId: string | null }) => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-background p-6 md:p-12 animate-fade-in pb-20">
            <div className="max-w-4xl mx-auto space-y-10">
                {!chatId && (
                    <Button
                        variant="ghost"
                        className="gap-2 text-muted-foreground hover:text-foreground"
                        onClick={() => navigate("/dashboard")}
                    >
                        <ArrowLeft className="w-4 h-4" /> В дашборд
                    </Button>
                )}

                <div className="text-center space-y-3">
                    <h1 className="text-4xl font-display font-black text-foreground tracking-tight">Тип новой заявки</h1>
                    <p className="text-muted-foreground text-lg">Выберите, какой документ вы хотите оформить сегодня</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {APPLICATION_TYPES.map((type) => (
                        <Card
                            key={type.id}
                            className="group cursor-pointer hover:shadow-xl transition-all duration-300 border-0 ring-1 ring-border hover:ring-primary/50 overflow-hidden relative"
                            onClick={() => {
                                const fullPath = chatId ? `${type.path}&chat_id=${chatId}` : type.path;
                                navigate(fullPath);
                            }}
                        >
                            <div className={`absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 rounded-full ${type.bg} opacity-50 group-hover:scale-150 transition-transform duration-500`} />
                            <CardHeader className="relative pb-2">
                                <div className={`w-12 h-12 rounded-2xl ${type.bg} flex items-center justify-center mb-2 group-hover:scale-110 transition-transform`}>
                                    <type.icon className={`w-6 h-6 ${type.color}`} />
                                </div>
                                <CardTitle className="text-xl font-bold">{type.title}</CardTitle>
                            </CardHeader>
                            <CardContent className="relative">
                                <p className="text-sm text-muted-foreground leading-relaxed italic pr-4">
                                    {type.desc}
                                </p>
                                <div className="mt-6 flex items-center text-xs font-bold text-primary opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-widest gap-2">
                                    Начать заполнение <ArrowRight className="w-3 h-3" />
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </div>
    );
};

const SubmitExpense = () => {
    const [searchParams] = useSearchParams();
    const chatId = searchParams.get("chat_id");
    const reqType = searchParams.get("template") || searchParams.get("type");
    const navigate = useNavigate();
    const [projectId, setProjectId] = useState("");
    const [branchId, setBranchId] = useState("");
    const [supplier, setSupplier] = useState<string>("Продукты");
    const [purpose, setPurpose] = useState("");
    const [items, setItems] = useState<ItemWithDisplay[]>([emptyItem()]);
    const [submitted, setSubmitted] = useState(false);
    const [errors, setErrors] = useState<{ purpose?: boolean; items?: number[]; project?: boolean; branch?: boolean }>({});

    const { data: projects = [] } = useQuery({
        queryKey: ["projects", chatId],
        queryFn: async () => {
            let list = [];
            if (chatId) {
                list = await store.getProjectsByChatId(chatId);
            } else {
                list = await store.getProjects();
            }
            if (list.length === 1 && !projectId) {
                setProjectId(list[0].id);
            }
            return list;
        },
    });

    const activeProject = projects.find((p: Project) => p.id === projectId);
    const isCorporate = activeProject?.category === "corporate";

    const { data: branches = [] } = useQuery({
        queryKey: ["branches", projectId, chatId],
        queryFn: () => {
            if (chatId) {
                return Promise.resolve((activeProject?.branches ?? []) as any[]);
            }
            return store.getBranches(projectId);
        },
        enabled: !!projectId && isCorporate
    });

    const mutation = useMutation({
        mutationFn: () => {
            const apiItems: ExpenseItem[] = items.map(({ displayAmount: _d, displayQuantity: _q, ...rest }) => rest);
            const data = {
                project_id: projectId,
                branch_id: isCorporate ? (branchId === "no_branch" ? null : branchId) : undefined,
                supplier,
                purpose,
                items: apiItems,
            };

            if (chatId) {
                return store.submitExpenseFromWeb({ ...data, chat_id: chatId });
            } else {
                return store.createExpenseRequest(data);
            }
        },
        onSuccess: () => {
            toast.success("Заявка отправлена!");
            if (chatId) {
                setSubmitted(true);
                setTimeout(() => {
                    setSubmitted(false);
                    setPurpose("");
                    setItems([emptyItem()]);
                    setErrors({});
                    setBranchId("");
                }, 2500);
            } else {
                setTimeout(() => navigate("/dashboard"), 2000);
            }
        },
        onError: () => toast.error("Ошибка при отправке"),
    });

    const addItem = () => {
        setItems([...items, emptyItem(items[0]?.currency || "UZS")]);
    };

    const removeItem = (index: number) => {
        if (items.length > 1) {
            setItems(items.filter((_, i) => i !== index));
            if (errors.items) {
                setErrors({
                    ...errors,
                    items: errors.items.filter(i => i !== index).map(i => i > index ? i - 1 : i)
                });
            }
        }
    };

    const updateItem = (index: number, field: keyof ItemWithDisplay, value: any) => {
        const newItems = [...items];
        (newItems[index] as any)[field] = value;
        
        // Auto-change unit for "зелень"
        if (field === "name" && value.toLowerCase().includes("зелень")) {
            newItems[index].unit = "пучки";
        }

        if (field === "currency") {
            newItems.forEach(item => (item.currency = value));
        }
        setItems(newItems);
        if (errors.items?.includes(index)) {
            const item = newItems[index];
            if (item.name && item.amount > 0) {
                setErrors({
                    ...errors,
                    items: errors.items.filter(i => i !== index)
                });
            }
        }
    };

    const handleAmountChange = (index: number, raw: string) => {
        const digitsOnly = raw.replace(/[^\d]/g, "");
        const withoutLeadingZeros = digitsOnly.replace(/^0+(\d)/, '$1');
        const num = withoutLeadingZeros === "" ? 0 : parseInt(withoutLeadingZeros, 10);
        const displayAmount = withoutLeadingZeros === "" ? "" : num.toLocaleString("ru-RU");
        const newItems = [...items];
        newItems[index] = { ...newItems[index], amount: num, displayAmount };
        setItems(newItems);
        if (errors.items?.includes(index) && num > 0 && newItems[index].name) {
            setErrors({
                ...errors,
                items: errors.items.filter(i => i !== index)
            });
        }
    };

    const handleQuantityChange = (index: number, raw: string) => {
        // Allow digits, one dot or comma
        let sanitized = raw.replace(/,/g, ".");
        sanitized = sanitized.replace(/[^\d.]/g, "");
        
        // Ensure only one dot
        const parts = sanitized.split(".");
        if (parts.length > 2) {
            sanitized = parts[0] + "." + parts.slice(1).join("");
        }

        const num = sanitized === "" || sanitized === "." ? 0 : parseFloat(sanitized);
        const newItems = [...items];
        newItems[index] = { ...newItems[index], quantity: num, displayQuantity: raw };
        setItems(newItems);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const newErrors: typeof errors = {};

        if (!projectId) {
            newErrors.project = true;
            toast.error("Выберите проект");
        }
        if (isCorporate && !branchId) {
            newErrors.branch = true;
            toast.error("Выберите филиал (или «Нет филиала»)");
        }
        if (!purpose.trim()) {
            newErrors.purpose = true;
            toast.error("Введите цель расхода");
        }

        const invalidItems = items.reduce((acc, item, idx) => {
            if (!item.name || item.amount <= 0) acc.push(idx);
            return acc;
        }, [] as number[]);

        if (invalidItems.length > 0) {
            newErrors.items = invalidItems;
            toast.error("Заполните все поля товаров");
        }

        setErrors(newErrors);
        if (Object.keys(newErrors).length > 0) return;

        mutation.mutate();
    };

    if (!reqType) {
        return <SelectionScreen chatId={chatId} />;
    }

    if (submitted) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center p-4">
                <div className="text-center space-y-4 glass-card p-10 rounded-2xl border max-w-sm w-full animate-fade-in">
                    <div className="text-6xl">✅</div>
                    <h2 className="text-2xl font-display font-bold text-foreground">Заявка отправлена!</h2>
                    <p className="text-muted-foreground text-sm">Возвращаемся к форме...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background p-4 md:p-8 animate-fade-in">
            <div className="max-w-2xl mx-auto space-y-8">
                {!chatId && (
                    <Button
                        variant="ghost"
                        className="absolute top-4 left-4 gap-2 text-muted-foreground hover:text-foreground"
                        onClick={() => navigate("/submit")}
                    >
                        <ArrowLeft className="w-4 h-4" /> Назад
                    </Button>
                )}

                <div className="text-center space-y-2">
                    <h1 className="text-3xl font-display font-bold text-foreground tracking-tight">Новая инвестиция</h1>
                    <p className="text-muted-foreground">Оформите новую инвестицию на расход</p>
                </div>

                <form onSubmit={handleSubmit} className="glass-card p-6 md:p-8 rounded-2xl border space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2 animate-fade-in">
                            <Label className={errors.project ? "text-destructive" : ""}>Проект</Label>
                            <Select value={projectId} onValueChange={(val) => { setProjectId(val); setErrors({ ...errors, project: false }); setBranchId(""); }}>
                                <SelectTrigger className={`rounded-xl ${errors.project ? "border-destructive ring-1 ring-destructive" : ""}`}>
                                    <SelectValue placeholder="Выберите проект" />
                                </SelectTrigger>
                                <SelectContent>
                                    {projects.map((p: Project) => (
                                        <SelectItem key={p.id} value={p.id}>
                                            {p.name} ({p.code})
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {isCorporate && (
                            <div className="space-y-2 animate-slide-in">
                                <Label className={errors.branch ? "text-destructive" : ""}>Филиал</Label>
                                <Select value={branchId} onValueChange={(val) => { setBranchId(val); setErrors({ ...errors, branch: false }) }}>
                                    <SelectTrigger className={`rounded-xl ${errors.branch ? "border-destructive ring-1 ring-destructive" : ""}`}>
                                        <SelectValue placeholder="Выберите филиал" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {branches.map((b: any) => (
                                            <SelectItem key={b.id} value={b.id}>
                                                {b.name}
                                            </SelectItem>
                                        ))}
                                        <SelectItem value="no_branch" className="text-muted-foreground font-medium italic">
                                            Нет филиала
                                        </SelectItem>
                                        {branches.length === 0 && (
                                            <div className="p-2 text-[10px] text-center text-muted-foreground opacity-50">Блок филиалов пуст</div>
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>
                        )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <Label>Поставщик / Категория</Label>
                            <Select value={supplier} onValueChange={setSupplier}>
                                <SelectTrigger className="rounded-xl">
                                    <SelectValue placeholder="Выберите поставщика" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Продукты">Продукты (Стандарт)</SelectItem>
                                    <SelectItem value="Мясо">Мясо (Chef)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="purpose" className={errors.purpose ? "text-destructive" : ""}>Цель расхода</Label>
                        <Input
                            id="purpose"
                            value={purpose}
                            onChange={(e) => { setPurpose(e.target.value); if (e.target.value) setErrors({ ...errors, purpose: false }) }}
                            placeholder="Напр. Закупка канцелярии"
                            className={`rounded-xl ${errors.purpose ? "border-destructive ring-1 ring-destructive placeholder:text-destructive/50" : ""}`}
                        />
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <Label>Список товаров/услуг</Label>
                            <Button type="button" variant="outline" size="sm" onClick={addItem} className="rounded-full gap-2 text-xs">
                                <Plus className="w-3 h-3" /> Добавить
                            </Button>
                        </div>

                        <div className="space-y-3">
                            {items.map((item, index) => (
                                <div key={index} className="flex gap-3 items-start p-4 bg-muted/30 rounded-xl border border-dashed animate-slide-in relative group">
                                    <div className="flex-1 space-y-3">
                                        <div className="flex gap-2">
                                            <div className="flex-1 space-y-1">
                                                <Label className="text-[10px] text-muted-foreground">Наименование</Label>
                                                <Input
                                                    value={item.name}
                                                    onChange={(e) => updateItem(index, "name", e.target.value)}
                                                    placeholder="Что покупаем?"
                                                    className="rounded-lg h-10 text-sm"
                                                />
                                            </div>
                                            <div className="w-24 space-y-1">
                                                <Label className="text-[10px] text-muted-foreground">Кол-во</Label>
                                                <Input
                                                    type="text"
                                                    inputMode="decimal"
                                                    value={item.displayQuantity}
                                                    onChange={(e) => handleQuantityChange(index, e.target.value)}
                                                    className="rounded-lg h-10 text-sm"
                                                />
                                            </div>
                                            <div className="w-24 space-y-1">
                                                <Label className="text-[10px] text-muted-foreground">Ед. изм.</Label>
                                                <Select value={item.unit} onValueChange={(val) => updateItem(index, "unit", val)}>
                                                    <SelectTrigger className="rounded-lg h-10 text-xs">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="кг">кг</SelectItem>
                                                        <SelectItem value="пучки">пучки</SelectItem>
                                                        <SelectItem value="шт">шт</SelectItem>
                                                        <SelectItem value="литры">литры</SelectItem>
                                                        <SelectItem value="ед.">ед.</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>

                                        <div className="flex gap-2">
                                            <div className="flex-1 space-y-1">
                                                <Label className="text-[10px] text-muted-foreground">Сумма</Label>
                                                <Input
                                                    type="text"
                                                    inputMode="numeric"
                                                    value={item.displayAmount}
                                                    onChange={(e) => handleAmountChange(index, e.target.value)}
                                                    placeholder="0"
                                                    className="rounded-lg h-10 text-sm font-bold"
                                                />
                                            </div>
                                            <div className="w-32 space-y-1">
                                                <Label className="text-[10px] text-muted-foreground">Валюта</Label>
                                                <Select value={item.currency} onValueChange={(val) => updateItem(index, "currency", val as any)}>
                                                    <SelectTrigger className="rounded-lg h-10 text-xs">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="UZS">UZS</SelectItem>
                                                        <SelectItem value="USD">USD</SelectItem>
                                                        <SelectItem value="RUB">RUB</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="pt-5">
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => removeItem(index)}
                                            className="h-10 w-10 text-muted-foreground hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <Button type="submit" className="w-full rounded-xl py-6 text-lg font-bold" disabled={mutation.isPending}>
                        {mutation.isPending ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Send className="w-5 h-5 mr-2" />}
                        {mutation.isPending ? "Создание..." : "Создать инвестицию"}
                    </Button>
                </form>
            </div>
        </div>
    );
};

export default SubmitExpense;
