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
import { Plus, Trash2, Send, Loader2, ArrowLeft } from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useNavigate, useSearchParams } from "react-router-dom";

const SubmitExpense = () => {
    const [searchParams] = useSearchParams();
    const chatId = searchParams.get("chat_id");
    const navigate = useNavigate();
    const [projectId, setProjectId] = useState("");
    const [purpose, setPurpose] = useState("");
    const [items, setItems] = useState<ExpenseItem[]>([
        { name: "", quantity: 1, amount: 0, currency: "UZS" }
    ]);

    const { data: projects = [] } = useQuery({
        queryKey: ["projects", chatId],
        queryFn: async () => {
            let list = [];
            if (chatId) {
                list = await store.getProjectsByChatId(chatId);
            } else {
                list = await store.getProjects();
            }

            // Auto-select if only one project
            if (list.length === 1 && !projectId) {
                setProjectId(list[0].id);
            }
            return list;
        },
    });

    const mutation = useMutation({
        mutationFn: () => {
            const data = {
                project_id: projectId,
                purpose,
                items,
            };

            if (chatId) {
                return store.submitExpenseFromWeb({ ...data, chat_id: chatId });
            } else {
                return store.createExpenseRequest(data);
            }
        },
        onSuccess: () => {
            toast.success("Заявка отправлена!");
            setTimeout(() => {
                setPurpose("");
                setItems([{ name: "", quantity: 1, amount: 0, currency: items[0]?.currency || "UZS" }]);
            }, 2000);
        },
        onError: () => toast.error("Ошибка при отправке")
    });

    const addItem = () => {
        setItems([...items, { name: "", quantity: 1, amount: 0, currency: items[0]?.currency || "UZS" }]);
    };

    const removeItem = (index: number) => {
        if (items.length > 1) {
            setItems(items.filter((_, i) => i !== index));
        }
    };

    const updateItem = (index: number, field: keyof ExpenseItem, value: any) => {
        const newItems = [...items];
        (newItems[index] as any)[field] = value;

        // Enforce single currency
        if (field === "currency") {
            newItems.forEach(item => item.currency = value);
        }

        setItems(newItems);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!projectId) return toast.error("Выберите проект");
        if (!purpose) return toast.error("Введите цель расхода");
        if (items.some(i => !i.name || i.amount <= 0)) return toast.error("Заполните все поля товаров");

        mutation.mutate({});
    };

    return (
        <div className="min-h-screen bg-background p-4 md:p-8 animate-fade-in">
            <div className="max-w-2xl mx-auto space-y-8">
                {!chatId && (
                    <Button
                        variant="ghost"
                        className="absolute top-4 left-4 gap-2 text-muted-foreground hover:text-foreground"
                        onClick={() => navigate("/dashboard")}
                    >
                        <ArrowLeft className="w-4 h-4" /> Назад
                    </Button>
                )}

                <div className="text-center space-y-2">
                    <h1 className="text-3xl font-display font-bold text-foreground tracking-tight">Новая заявка</h1>
                    <p className="text-muted-foreground">Заполните форму для отправки запроса на расход</p>
                </div>

                <form onSubmit={handleSubmit} className="glass-card p-6 md:p-8 rounded-2xl border space-y-6">
                    {projects.length > 1 && (
                        <div className="space-y-2 animate-fade-in">
                            <Label>Проект</Label>
                            <Select value={projectId} onValueChange={setProjectId}>
                                <SelectTrigger className="rounded-xl">
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
                    )}

                    {projects.length === 1 && projectId && (
                        <div className="bg-muted/50 p-4 rounded-xl border border-dashed text-sm flex justify-between items-center">
                            <span className="text-muted-foreground">Проект:</span>
                            <span className="font-bold">{projects[0].name} ({projects[0].code})</span>
                        </div>
                    )}

                    <div className="space-y-2">
                        <Label htmlFor="purpose">Цель расхода</Label>
                        <Input
                            id="purpose"
                            value={purpose}
                            onChange={(e) => setPurpose(e.target.value)}
                            placeholder="Напр. Закупка канцелярии"
                            required
                            className="rounded-xl"
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
                                <div key={index} className="flex gap-2 items-end p-3 bg-muted/30 rounded-xl border border-dashed animate-slide-in">
                                    <div className="flex-1 space-y-1">
                                        <Label className="text-[10px] text-muted-foreground">Наименование</Label>
                                        <Input
                                            value={item.name}
                                            onChange={(e) => updateItem(index, "name", e.target.value)}
                                            placeholder="Товар..."
                                            className="rounded-lg h-9 text-sm"
                                        />
                                    </div>
                                    <div className="w-16 space-y-1">
                                        <Label className="text-[10px] text-muted-foreground">Кол-во</Label>
                                        <Input
                                            type="number"
                                            value={item.quantity}
                                            onChange={(e) => updateItem(index, "quantity", Number(e.target.value))}
                                            className="rounded-lg h-9 text-sm"
                                        />
                                    </div>
                                    <div className="w-24 space-y-1">
                                        <Label className="text-[10px] text-muted-foreground">Сумма</Label>
                                        <Input
                                            type="text"
                                            value={item.amount ? item.amount.toLocaleString("ru-RU") : ""}
                                            onChange={(e) => {
                                                const val = e.target.value.replace(/\D/g, "");
                                                updateItem(index, "amount", val ? Number(val) : 0);
                                            }}
                                            className="rounded-lg h-9 text-sm"
                                        />
                                    </div>
                                    <div className="w-20 space-y-1">
                                        <Label className="text-[10px] text-muted-foreground">Валюта</Label>
                                        <Select value={item.currency} onValueChange={(val) => updateItem(index, "currency", val)}>
                                            <SelectTrigger className="rounded-lg h-9 text-xs">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="UZS">UZS</SelectItem>
                                                <SelectItem value="USD">USD</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => removeItem(index)}
                                        className="h-9 w-9 text-muted-foreground hover:text-red-500"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </div>

                    <Button type="submit" className="w-full rounded-xl py-6 text-lg font-bold" disabled={mutation.isPending}>
                        {mutation.isPending ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Send className="w-5 h-5 mr-2" />}
                        Отправить на согласование
                    </Button>
                </form>
            </div>
        </div>
    );
};

export default SubmitExpense;
