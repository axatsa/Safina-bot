import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { ExpenseRequest, ExpenseStatus, STATUS_LABELS } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  ArrowLeft, Download, Clock, CheckCircle, XCircle,
  RotateCcw, Archive, Send, Loader2, FastForward, Crown
} from "lucide-react";
import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const statusColorMap: Record<ExpenseStatus, string> = {
  request:         "bg-amber-100 text-amber-800",
  review:          "bg-blue-100 text-blue-800",
  confirmed:       "bg-emerald-100 text-emerald-800",
  declined:        "bg-red-100 text-red-800",
  revision:        "bg-orange-100 text-orange-800",
  archived:        "bg-gray-100 text-gray-800",
  pending_senior:  "bg-purple-100 text-purple-800",
  approved_senior: "bg-teal-100 text-teal-800",
  rejected_senior: "bg-rose-100 text-rose-800",
  pending_ceo:     "bg-violet-100 text-violet-800",
  approved_ceo:    "bg-green-100 text-green-800",
  rejected_ceo:    "bg-pink-100 text-pink-800",
};

const ExpenseDetail = () => {
  const { id = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isAdmin = store.isAdmin();
  const isFarrukh = store.isFarrukh();
  const queryClient = useQueryClient();

  const { data: expenses = [] } = useQuery({
    queryKey: ["expenses"],
    queryFn: () => store.getExpenses(),
  });

  const expense = expenses.find((e) => e.id === id);

  const [internalComment, setInternalComment] = useState("");
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<ExpenseStatus | null>(null);
  const [statusComment, setStatusComment] = useState("");

  useEffect(() => {
    if (expense?.internalComment) {
      setInternalComment(expense.internalComment);
    }
  }, [expense]);

  const statusMutation = useMutation({
    mutationFn: ({ status, comment }: { status: ExpenseStatus; comment?: string }) =>
      store.updateExpenseStatus(id, status, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      toast.success("Статус обновлен");
    },
    onError: () => toast.error("Ошибка при обновлении статуса"),
  });

  const internalCommentMutation = useMutation({
    mutationFn: (comment: string) => store.updateInternalComment(id, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      toast.info("Для этого статуса требуется комментарий. Откройте детали инвестиции.");
    },
  });

  const forwardSeniorMutation = useMutation({
    mutationFn: () => store.forwardToSenior(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      toast.success("Инвестиция отправлена CFO");
    },
    onError: () => toast.error("Ошибка при отправке CFO"),
  });

  const forwardCeoMutation = useMutation({
    mutationFn: () => store.forwardToCeo(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      toast.success("Инвестиция отправлена CEO");
    },
    onError: (e: Error) => toast.error(e.message || "Ошибка при отправке CEO"),
  });

  if (!expense) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        <p>Инвестиция не найдена</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate("/dashboard")}>
          Назад
        </Button>
      </div>
    );
  }

  const handleStatusChange = (newStatus: ExpenseStatus) => {
    if (newStatus === "declined" || newStatus === "revision") {
      setPendingStatus(newStatus);
      setStatusComment("");
      setCommentDialogOpen(true);
    } else {
      statusMutation.mutate({ status: newStatus });
    }
  };

  const handleStatusWithComment = () => {
    if (!statusComment.trim() || !pendingStatus) return;
    statusMutation.mutate({ status: pendingStatus, comment: statusComment.trim() });
    setCommentDialogOpen(false);
    setPendingStatus(null);
    setStatusComment("");
  };

  const isArchived = expense.status === "archived";

  const actionButtons: { status: ExpenseStatus; label: string; icon: React.ReactNode; variant: "default" | "outline" | "destructive" | "ghost" }[] = [
    { status: "review", label: "В рассмотрение", icon: <Clock className="w-4 h-4" />, variant: "outline" },
    { status: "confirmed", label: "Подтвердить", icon: <CheckCircle className="w-4 h-4" />, variant: "default" as const },
    { status: "declined", label: "Отклонить", icon: <XCircle className="w-4 h-4" />, variant: "destructive" as const },
    { status: "revision", label: "На доработку", icon: <RotateCcw className="w-4 h-4" />, variant: "outline" as const },
    { status: "archived", label: "В архив", icon: <Archive className="w-4 h-4" />, variant: "ghost" as const },
  ];

  return (
    <div className="p-6 space-y-6 animate-slide-in max-w-4xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-display font-bold text-foreground">{expense.requestId}</h1>
            <Badge className={statusColorMap[expense.status]}>
              {STATUS_LABELS[expense.status]}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{expense.purpose}</p>
        </div>
        <Button variant="outline" size="sm" className="gap-2" onClick={() => store.exportDocx(expense.id)}>
          <Download className="w-4 h-4" />
          Скачать инвестицию (Word)
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Проект", value: `${expense.projectName} (${expense.projectCode})` },
          { label: "Ответственный", value: expense.createdBy },
          { label: "Дата/время", value: format(new Date(expense.date), "yyyy-MM-dd HH:mm", { locale: ru }) },
          { label: "Сумма", value: `${expense.totalAmount.toLocaleString()} ${expense.currency}` },
        ].map((item) => (
          <div key={item.label} className="glass-card rounded-lg p-3">
            <p className="text-xs text-muted-foreground">{item.label}</p>
            <p className="font-medium text-sm mt-1">{item.value}</p>
          </div>
        ))}
      </div>

      {expense.statusComment && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <p className="text-xs font-medium text-destructive mb-1">Комментарий к статусу:</p>
          <p className="text-sm">{expense.statusComment}</p>
        </div>
      )}

      <div className="glass-card rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50 text-left text-muted-foreground">
              <th className="py-3 px-4 font-medium">Наименование</th>
              <th className="py-3 px-4 font-medium text-right">Кол-во</th>
              <th className="py-3 px-4 font-medium text-right">Сумма</th>
            </tr>
          </thead>
          <tbody>
            {expense.items.map((item, i) => (
              <tr key={i} className="border-b">
                <td className="py-3 px-4">{item.name}</td>
                <td className="py-3 px-4 text-right">{item.quantity}</td>
                <td className="py-3 px-4 text-right">{item.amount.toLocaleString()} {item.currency}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-muted/30 font-semibold">
              <td className="py-3 px-4" colSpan={2}>Итого</td>
              <td className="py-3 px-4 text-right">{expense.totalAmount.toLocaleString()} {expense.currency}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {!isArchived && (
        <div className="flex flex-wrap gap-2">
          {actionButtons
            .filter((a) => a.status !== expense.status)
            .map((action) => (
              <Button
                key={action.status}
                variant={action.variant}
                size="sm"
                className="gap-2"
                onClick={() => handleStatusChange(action.status)}
                disabled={statusMutation.isPending || forwardSeniorMutation.isPending}
              >
                {statusMutation.isPending && pendingStatus === action.status ? <Loader2 className="w-4 h-4 animate-spin" /> : action.icon}
                {action.label}
              </Button>
            ))}

          {/* Safina/Admin: forward to CFO */}
          {(store.isAdmin() || store.isSafina()) && expense.status !== "archived" && expense.status !== "pending_senior" && (
            <Button
              variant="default"
              size="sm"
              className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white"
              onClick={() => forwardSeniorMutation.mutate()}
              disabled={forwardSeniorMutation.isPending || statusMutation.isPending}
            >
              {forwardSeniorMutation.isPending
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <FastForward className="w-4 h-4" />}
              На согласование CFO
            </Button>
          )}

          {/* CFO/Admin/Farrukh: forward to CEO */}
          {(store.isSeniorFinancier() || (store.isAdmin() && !store.isSafina()) || isFarrukh) && 
            expense.status !== "archived" && 
            !["pending_ceo", "approved_ceo"].includes(expense.status) && (
            <Button
              variant="default"
              size="sm"
              className="gap-2 bg-violet-600 hover:bg-violet-700 text-white"
              onClick={() => forwardCeoMutation.mutate()}
              disabled={forwardCeoMutation.isPending || statusMutation.isPending}
            >
              {forwardCeoMutation.isPending
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Crown className="w-4 h-4" />}
              Отправить CEO
            </Button>
          )}

          {/* Safina: Return from CFO to review */}
          {store.isSafina() && expense.status === "pending_senior" && (
             <Button
                variant="outline"
                size="sm"
                className="gap-2 border-orange-200 text-orange-700 hover:bg-orange-50"
                onClick={() => handleStatusChange("review")}
                disabled={statusMutation.isPending}
             >
                <RotateCcw className="w-4 h-4" />
                Вернуть на рассмотрение
             </Button>
          )}
        </div>
      )}

      {isArchived && (
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={() => handleStatusChange("request")}
          disabled={statusMutation.isPending}
        >
          {statusMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
          Вернуть из архива
        </Button>
      )}

      <div className="glass-card rounded-lg p-4 space-y-3">
        <Label className="text-sm font-medium">Internal comment (видно только в админке)</Label>
        <Textarea
          value={internalComment}
          onChange={(e) => setInternalComment(e.target.value)}
          placeholder="Добавьте комментарий..."
          rows={3}
        />
        <Button size="sm" onClick={() => internalCommentMutation.mutate(internalComment)} disabled={internalCommentMutation.isPending}>
          {internalCommentMutation.isPending ? "Сохранение..." : "Сохранить"}
        </Button>
      </div>

      <Dialog open={commentDialogOpen} onOpenChange={setCommentDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {pendingStatus === "declined" ? "Причина отклонения" : "Комментарий для доработки"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <p className="text-sm text-muted-foreground">
              Комментарий обязателен и будет отправлен ответственному в Telegram.
            </p>
            <Textarea
              value={statusComment}
              onChange={(e) => setStatusComment(e.target.value)}
              placeholder="Введите комментарий..."
              rows={4}
            />
            <Button
              onClick={handleStatusWithComment}
              disabled={!statusComment.trim() || statusMutation.isPending}
              className="w-full gap-2"
            >
              {statusMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Отправить
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ExpenseDetail;
