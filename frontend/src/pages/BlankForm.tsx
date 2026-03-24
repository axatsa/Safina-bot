import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Trash2, Download, Loader2, ArrowLeft } from "lucide-react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { generateBlank, BlankItem } from "@/lib/services/blanks";
import { store } from "@/lib/store";

const BlankForm = () => {
  const [searchParams] = useSearchParams();
  const template = searchParams.get("template") || searchParams.get("type") || "ls";
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  // Common fields (Service Notes)
  const [purpose, setPurpose] = useState("");
  const [items, setItems] = useState<BlankItem[]>([
    { name: "", qty: 1, amount: 0, currency: "UZS" },
  ]);

  // Refund application fields
  const [refundData, setRefundData] = useState({
    client_name: "",
    passport_series: "",
    passport_number: "",
    passport_issued_by: "",
    passport_date: "",
    phone: "",
    contract_number: "",
    contract_date: "",
    reason: "",
    reason_other: "",
    amount: 0,
    amount_words: "",
    card_holder: "",
    card_number: "",
    transit_account: "",
    bank_name: "",
    retention: false,
  });

  const addItem = () => {
    setItems([...items, { name: "", qty: 1, amount: 0, currency: "UZS" }]);
  };

  const removeItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const updateItem = (index: number, field: keyof BlankItem, value: any) => {
    const newItems = [...items];
    (newItems[index] as any)[field] = value;
    setItems(newItems);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (template === "refund") {
        if (!refundData.client_name.trim()) {
          toast.error("Укажите ФИО клиента");
          setLoading(false);
          return;
        }
        if (refundData.amount <= 0) {
          toast.error("Сумма возврата должна быть больше нуля");
          setLoading(false);
          return;
        }
        if (refundData.reason === "Другое" && !refundData.reason_other.trim()) {
          toast.error("Укажите причину при выборе 'Другое'");
          setLoading(false);
          return;
        }
        const payload = {
          ...refundData,
          project_id: searchParams.get("project_id") || null,
        };
        await store.submitRefundApplicationFromWeb(payload);
        toast.success("Заявление на возврат отправлено Сафине!");
      } else {
        const payload = {
          template,
          purpose,
          items,
          project_id: searchParams.get("project_id") || null,
        };
        await store.submitBlankFromWeb(payload);
        toast.success("Заявка успешно отправлена Сафине!");
      }
      navigate("/dashboard/applications");
    } catch (error) {
      console.error(error);
      toast.error("Ошибка при отправке заявки");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-8 animate-fade-in">
      <div className="max-w-2xl mx-auto space-y-8">
        <Button
          variant="ghost"
          className="absolute top-4 left-4 gap-2 text-muted-foreground hover:text-foreground"
          onClick={() => navigate(-1)}
        >
          <ArrowLeft className="w-4 h-4" /> Назад
        </Button>

        <div className="text-center space-y-2">
          <h1 className="text-3xl font-display font-bold text-foreground tracking-tight">
            {template === "refund" ? "Заявление на возврат" : "Служебная записка / Бланк"}
          </h1>
          <p className="text-muted-foreground">Заполните данные для генерации документа</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-card p-6 md:p-8 rounded-2xl border space-y-6">
          {template !== "refund" ? (
            <>
              {/* Service Note Form */}
              <div className="space-y-2">
                <Label htmlFor="purpose">Цель расхода</Label>
                <Input
                  id="purpose"
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  placeholder="Напр. Закупка офисной техники"
                  required
                />
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Позиции</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addItem} className="rounded-full gap-2">
                    <Plus className="w-4 h-4" /> Добавить
                  </Button>
                </div>

                <div className="space-y-3">
                  {items.map((item, index) => (
                    <div key={index} className="flex gap-3 items-end p-4 bg-muted/30 rounded-xl border relative group">
                      <div className="flex-1 space-y-3">
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label className="text-xs">Наименование</Label>
                            <Input
                              value={item.name}
                              onChange={(e) => updateItem(index, "name", e.target.value)}
                              placeholder="Название"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Кол-во</Label>
                            <Input
                              type="number"
                              value={item.qty}
                              onChange={(e) => updateItem(index, "qty", Number(e.target.value))}
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label className="text-xs">Сумма</Label>
                            <Input
                              type="number"
                              value={item.amount}
                              onChange={(e) => updateItem(index, "amount", Number(e.target.value))}
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Валюта</Label>
                            <Select value={item.currency} onValueChange={(val) => updateItem(index, "currency", val)}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="UZS">UZS</SelectItem>
                                <SelectItem value="USD">USD</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => removeItem(index)}
                        className="h-10 w-10 text-muted-foreground hover:text-red-500"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Refund Application Form - Multi-column/compact */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>ФИО Клиента</Label>
                  <Input value={refundData.client_name} onChange={(e) => setRefundData({...refundData, client_name: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Телефон</Label>
                  <Input value={refundData.phone} onChange={(e) => setRefundData({...refundData, phone: e.target.value})} />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-2">
                    <Label>Серия паспорта</Label>
                    <Input value={refundData.passport_series} onChange={(e) => setRefundData({...refundData, passport_series: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Номер паспорта</Label>
                    <Input value={refundData.passport_number} onChange={(e) => setRefundData({...refundData, passport_number: e.target.value})} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Кем выдан паспорт</Label>
                  <Input value={refundData.passport_issued_by} onChange={(e) => setRefundData({...refundData, passport_issued_by: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Дата выдачи паспорта</Label>
                  <Input type="date" value={refundData.passport_date} onChange={(e) => setRefundData({...refundData, passport_date: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Номер оферты/договора</Label>
                  <Input value={refundData.contract_number} onChange={(e) => setRefundData({...refundData, contract_number: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Дата оферты/договора</Label>
                  <Input type="date" value={refundData.contract_date} onChange={(e) => setRefundData({...refundData, contract_date: e.target.value})} />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label>Причина</Label>
                  <Select value={refundData.reason} onValueChange={(val) => setRefundData({...refundData, reason: val})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Переезд">Переезд</SelectItem>
                      <SelectItem value="Изменение графика">Изменение графика</SelectItem>
                      <SelectItem value="Несоответствие">Несоответствие ожиданиям</SelectItem>
                      <SelectItem value="Материальные трудности">Материальные трудности</SelectItem>
                      <SelectItem value="Другое">Другое</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {refundData.reason === "Другое" && (
                  <div className="space-y-2 md:col-span-2 animate-in fade-in slide-in-from-top-1">
                    <Label className="text-sm font-medium">Укажите причину <span className="text-destructive">*</span></Label>
                    <Input 
                      value={refundData.reason_other} 
                      onChange={(e) => setRefundData({...refundData, reason_other: e.target.value})} 
                      placeholder="Опишите причину возврата..."
                      required
                    />
                  </div>
                )}
                <div className="space-y-2">
                  <Label>Сумма цифрами</Label>
                  <Input type="number" value={refundData.amount} onChange={(e) => setRefundData({...refundData, amount: Number(e.target.value)})} />
                </div>
                <div className="space-y-2">
                  <Label>Сумма прописью</Label>
                  <Input value={refundData.amount_words} onChange={(e) => setRefundData({...refundData, amount_words: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>ФИО владельца карты</Label>
                  <Input value={refundData.card_holder} onChange={(e) => setRefundData({...refundData, card_holder: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Номер карты</Label>
                  <Input value={refundData.card_number} onChange={(e) => setRefundData({...refundData, card_number: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Транзитный счет банка (если есть)</Label>
                  <Input value={refundData.transit_account} onChange={(e) => setRefundData({...refundData, transit_account: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Название банка и филиал</Label>
                  <Input value={refundData.bank_name} onChange={(e) => setRefundData({...refundData, bank_name: e.target.value})} />
                </div>

                {/* Удержание */}
                <div className="md:col-span-2 flex items-center gap-4 p-3 bg-muted/40 rounded-xl border">
                  <div className="flex-1">
                    <Label className="text-sm font-medium cursor-pointer">Удержание</Label>
                    <p className="text-xs text-muted-foreground mt-0.5">Есть ли удержание при возврате?</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch
                      id="retention-blank"
                      checked={refundData.retention}
                      onCheckedChange={(val) => setRefundData({...refundData, retention: val})}
                    />
                    <span className={`text-xs font-bold w-16 ${refundData.retention ? "text-amber-700" : "text-muted-foreground"}`}>
                      {refundData.retention ? "ДА (ЕСТЬ)" : "НЕТ (БЕЗ)"}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}

          <Button type="submit" className="w-full rounded-xl py-6 bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg" disabled={loading}>
            {loading ? <Loader2 className="animate-spin mr-2" /> : <Plus className="mr-2" />}
            Отправить Сафине
          </Button>
        </form>
      </div>
    </div>
  );
};

export default BlankForm;
