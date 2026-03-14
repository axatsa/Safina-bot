import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Send, Loader2, ArrowLeft, UploadCloud, Camera } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Switch } from "@/components/ui/switch";

const REASON_PRESETS = ["Переезд", "Отчисление", "Болезнь", "Другое"];

const API = import.meta.env.VITE_APP_API_URL || "/api";

/** Закрывает Telegram Mini-App overlay после успешной отправки */
const closeTelegramWebApp = () => {
  // @ts-ignore
  window.Telegram?.WebApp?.close();
};

interface SubmitRefundProps {
  chatId: string | null;
}

const SubmitRefund = ({ chatId }: SubmitRefundProps) => {
  const navigate = useNavigate();
  const [studentId, setStudentId] = useState("");
  const [reason, setReason] = useState("");
  const [amount, setAmount] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [cardError, setCardError] = useState("");
  const [amountError, setAmountError] = useState("");
  const [retention, setRetention] = useState(false);
  const [receiptPhoto, setReceiptPhoto] = useState<File | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!receiptPhoto) throw new Error("Фото чека обязательно");
      const formData = new FormData();
      formData.append("student_id", studentId);
      formData.append("reason", reason);
      formData.append("amount", amount.replace(/[^\d]/g, ""));
      formData.append("card_number", cardNumber.replace(/\s/g, ""));
      formData.append("retention", String(retention));
      formData.append("receipt_photo", receiptPhoto);
      if (chatId) formData.append("chat_id", chatId);

      const token = localStorage.getItem("safina_token");
      const headers: Record<string, string> = {};
      if (token && !chatId) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API}/expenses/refund/web-submit`, {
        method: "POST",
        body: formData,
        headers,
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData?.detail || "Ошибка отправки");
      }
      return await res.json();
    },
    onSuccess: () => {
      toast.success("Возврат оформлен!");
      if (chatId) {
        setSubmitted(true);
        // Закрываем Mini-App после успеха
        setTimeout(() => closeTelegramWebApp(), 1800);
      } else {
        setTimeout(() => navigate("/dashboard"), 2000);
      }
    },
    onError: (err: any) => toast.error(err.message || "Ошибка при отправке"),
  });

  const handleAmountChange = (raw: string) => {
    const digitsOnly = raw.replace(/[^\d]/g, "");
    setAmountError("");
    if (!digitsOnly) { setAmount(""); return; }
    const num = parseInt(digitsOnly, 10);
    if (num <= 0) setAmountError("Сумма должна быть положительной");
    setAmount(num.toLocaleString("ru-RU"));
  };

  const handleCardChange = (raw: string) => {
    let digitsOnly = raw.replace(/[^\d]/g, "");
    if (digitsOnly.length > 16) digitsOnly = digitsOnly.slice(0, 16);
    setCardNumber(digitsOnly.replace(/(\d{4})/g, "$1 ").trim());
    setCardError(
      digitsOnly.length > 0 && digitsOnly.length !== 16
        ? `Введено ${digitsOnly.length} / 16 цифр`
        : ""
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId.trim()) return toast.error("Введите ID ученика");
    if (!reason.trim()) return toast.error("Выберите или введите причину");
    if (!amount) return toast.error("Введите сумму");
    if (cardNumber.replace(/\s/g, "").length !== 16) return toast.error("Введите 16 цифр номера карты");
    if (!receiptPhoto) return toast.error("Загрузите фото чека");
    mutation.mutate();
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center space-y-4 glass-card p-10 rounded-2xl border max-w-sm w-full animate-fade-in">
          <div className="text-6xl">✅</div>
          <h2 className="text-2xl font-display font-bold text-foreground">Заявка отправлена!</h2>
          <p className="text-muted-foreground text-sm">Окно закрывается...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8 animate-fade-in">
      <div className="max-w-xl mx-auto space-y-8">
        {!chatId && (
          <Button variant="ghost" className="gap-2 text-muted-foreground hover:text-foreground" onClick={() => navigate("/dashboard")}>
            <ArrowLeft className="w-4 h-4" /> Назад
          </Button>
        )}

        <div className="text-center space-y-2">
          <h1 className="text-3xl font-display font-bold text-foreground tracking-tight">Возврат инвестиции</h1>
          <p className="text-muted-foreground">Заполните данные для возврата средств по инвестиции</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-card p-6 md:p-8 rounded-2xl border space-y-6">
          {/* ID ученика */}
          <div className="space-y-2">
            <Label htmlFor="studentId">ID ученика</Label>
            <Input id="studentId" value={studentId} onChange={(e) => setStudentId(e.target.value)}
              placeholder="Напр. 123456" required className="rounded-xl" />
          </div>

          {/* Причина возврата + пресеты */}
          <div className="space-y-2">
            <Label htmlFor="reason">Причина возврата</Label>
            <div className="flex flex-wrap gap-2 mb-2">
              {REASON_PRESETS.map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setReason(r)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                    reason === r
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-muted text-muted-foreground border-muted-foreground/20 hover:bg-accent"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
            <Input id="reason" value={reason} onChange={(e) => setReason(e.target.value)}
              placeholder="Переезд, отчисление и т.д." required className="rounded-xl" />
          </div>

          {/* Сумма */}
          <div className="space-y-1">
            <Label htmlFor="amount">Сумма возврата (UZS)</Label>
            <Input id="amount" inputMode="numeric" value={amount}
              onChange={(e) => handleAmountChange(e.target.value)}
              placeholder="1 000 000" required
              className={`rounded-xl font-bold ${amountError ? "border-destructive" : ""}`} />
            {amountError && <p className="text-xs text-destructive">{amountError}</p>}
          </div>

          {/* Номер карты */}
          <div className="space-y-1">
            <Label htmlFor="cardNumber">Номер карты (UZCARD/HUMO)</Label>
            <Input id="cardNumber" inputMode="numeric" value={cardNumber}
              onChange={(e) => handleCardChange(e.target.value)}
              placeholder="8600 0000 0000 0000" required
              className={`rounded-xl font-bold tracking-widest ${cardError ? "border-destructive" : ""}`} />
            {cardError && <p className="text-xs text-destructive">{cardError}</p>}
          </div>

          {/* Удержание */}
          <div className="flex items-center justify-between p-4 bg-muted/30 rounded-xl border border-dashed">
            <div className="space-y-0.5">
              <Label>Удержание</Label>
              <p className="text-[10px] text-muted-foreground">Применяется ли удержание?</p>
            </div>
            <Switch id="retention" checked={retention} onCheckedChange={setRetention} />
          </div>

          {/* Фото чека */}
          <div className="space-y-2">
            <Label>Фото чека (Обязательно)</Label>
            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer hover:bg-muted/50 transition-colors">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                {receiptPhoto
                  ? <><UploadCloud className="w-8 h-8 text-primary mb-2" /><span className="text-sm text-primary font-medium">{receiptPhoto.name}</span></>
                  : <><Camera className="w-8 h-8 text-muted-foreground mb-2" /><span className="text-sm text-muted-foreground">Съёмка / загрузка фото чека</span></>}
              </div>
              {/* capture="environment" — открывает заднюю камеру на мобильных */}
              <input type="file" className="hidden" accept="image/*" capture="environment"
                onChange={(e) => setReceiptPhoto(e.target.files?.[0] || null)} />
            </label>
          </div>

          <Button type="submit" className="w-full rounded-xl py-6 text-lg font-bold" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Send className="w-5 h-5 mr-2" />}
            Создать возврат
          </Button>
        </form>
      </div>
    </div>
  );
};

export default SubmitRefund;
