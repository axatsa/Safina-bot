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
  const [studentIdError, setStudentIdError] = useState("");
  const [reason, setReason] = useState("");
  const [reasonOther, setReasonOther] = useState("");
  const [reasonError, setReasonError] = useState("");
  const [amount, setAmount] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [cardError, setCardError] = useState("");
  const [amountError, setAmountError] = useState("");
  const [retention, setRetention] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      const finalReason = reason === "Другое" ? `Другое: ${reasonOther}` : reason;
      const formData = new FormData();
      formData.append("user_id", localStorage.getItem("safina_user_id") || ""); // Web endpoint needs user_id
      formData.append("student_id", studentId);
      formData.append("reason", finalReason);
      formData.append("amount", amount.replace(/[^\d]/g, ""));
      formData.append("card_number", cardNumber.replace(/\s/g, ""));
      formData.append("retention", retention.toString());
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
    let hasError = false;

    if (!studentId.trim()) {
      setStudentIdError("Введите ID ученика");
      hasError = true;
    } else {
      setStudentIdError("");
    }

    if (!reason.trim()) {
      setReasonError("Выберите или введите причину");
      hasError = true;
    } else if (reason === "Другое" && !reasonOther.trim()) {
      setReasonError("Укажите причину в поле ниже");
      hasError = true;
    } else {
      setReasonError("");
    }

    const amountNum = parseInt(amount.replace(/[^\d]/g, ""), 10);
    if (!amount || isNaN(amountNum) || amountNum <= 0) {
      setAmountError("Сумма должна быть положительной и больше нуля");
      hasError = true;
    }

    if (cardNumber.replace(/\s/g, "").length !== 16) {
      setCardError("Введите 16 цифр номера карты");
      hasError = true;
    }

    if (hasError) {
      toast.error("Пожалуйста, заполните все обязательные поля");
      return;
    }

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
            <Label htmlFor="studentId" className={studentIdError ? "text-destructive" : ""}>ID ученика</Label>
            <Input 
              id="studentId" 
              value={studentId} 
              onChange={(e) => { setStudentId(e.target.value); if(e.target.value) setStudentIdError(""); }}
              placeholder="Напр. 123456" 
              className={`rounded-xl ${studentIdError ? "border-destructive ring-1 ring-destructive" : ""}`} 
            />
            {studentIdError && <p className="text-[10px] text-destructive italic">{studentIdError}</p>}
          </div>

          {/* Причина возврата + пресеты */}
          <div className="space-y-2">
            <Label htmlFor="reason" className={reasonError ? "text-destructive" : ""}>Причина возврата</Label>
            <div className="flex flex-wrap gap-2 mb-2">
              {REASON_PRESETS.map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => { setReason(r); setReasonError(""); }}
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
            <Input 
              id="reason" 
              value={reason} 
              onChange={(e) => { setReason(e.target.value); if(e.target.value) setReasonError(""); }}
              placeholder="Переезд, отчисление и т.д." 
              className={`rounded-xl ${reasonError ? "border-destructive ring-1 ring-destructive" : ""}`} 
            />
            {reason === "Другое" && (
              <div className="animate-in fade-in slide-in-from-top-1 space-y-1">
                <Label htmlFor="reasonOther" className={reasonError && !reasonOther ? "text-destructive text-xs" : "text-xs text-muted-foreground"}>
                  Укажите причину (обязательно) *
                </Label>
                <Input
                  id="reasonOther"
                  value={reasonOther}
                  onChange={(e) => { setReasonOther(e.target.value); if(e.target.value) setReasonError(""); }}
                  placeholder="Опишите причину возврата..."
                  className={`rounded-xl ${reasonError && !reasonOther ? "border-destructive ring-1 ring-destructive" : ""}`}
                />
              </div>
            )}
            {reasonError && <p className="text-[10px] text-destructive italic">{reasonError}</p>}
          </div>

          {/* Сумма */}
          <div className="space-y-1">
            <Label htmlFor="amount" className={amountError ? "text-destructive" : ""}>Сумма возврата (UZS)</Label>
            <Input id="amount" inputMode="numeric" value={amount}
              onChange={(e) => handleAmountChange(e.target.value)}
              placeholder="1 000 000"
              className={`rounded-xl font-bold ${amountError ? "border-destructive ring-1 ring-destructive" : ""}`} />
            {amountError && <p className="text-[10px] text-destructive italic">{amountError}</p>}
          </div>

          {/* Номер карты */}
          <div className="space-y-1">
            <Label htmlFor="cardNumber" className={cardError ? "text-destructive" : ""}>Номер карты (UZCARD/HUMO)</Label>
            <Input id="cardNumber" inputMode="numeric" value={cardNumber}
              onChange={(e) => handleCardChange(e.target.value)}
              placeholder="8600 0000 0000 0000"
              className={`rounded-xl font-bold tracking-widest ${cardError ? "border-destructive ring-1 ring-destructive" : ""}`} />
            {cardError && <p className="text-[10px] text-destructive italic">{cardError}</p>}
          </div>

          {/* Удержание */}
          <div className="flex items-center gap-4 p-3 bg-muted/40 rounded-xl border">
            <div className="flex-1">
              <Label htmlFor="retention" className="text-sm font-medium cursor-pointer">Удержание</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Есть ли удержание при возврате?</p>
            </div>
            <div className="flex items-center gap-3">
              <Switch id="retention" checked={retention} onCheckedChange={setRetention} />
              <span className={`text-xs font-bold w-16 ${retention ? "text-amber-700" : "text-muted-foreground"}`}>
                {retention ? "ДА (ЕСТЬ)" : "НЕТ (БЕЗ)"}
              </span>
            </div>
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
