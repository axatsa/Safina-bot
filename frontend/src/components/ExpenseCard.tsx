import { ExpenseRequest, ExpenseStatus, STATUS_LABELS } from "@/lib/types";
import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { Calendar, Download, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { store } from "@/lib/store";
import { useNavigate } from "react-router-dom";

interface ExpenseCardProps {
  expense: ExpenseRequest;
}

const statusColorMap: Record<ExpenseStatus, string> = {
  request: "bg-amber-100 text-amber-800",
  review: "bg-blue-100 text-blue-800",
  confirmed: "bg-emerald-100 text-emerald-800",
  declined: "bg-red-100 text-red-800",
  revision: "bg-orange-100 text-orange-800",
  archived: "bg-gray-100 text-gray-800",
};

const ExpenseCard = ({ expense }: ExpenseCardProps) => {
  const navigate = useNavigate();

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    store.exportDocx(expense.id);
  };

  const handleOpen = () => {
    navigate(`/dashboard/expense/${expense.id}`);
  };

  return (
    <div className="bg-card rounded-lg border p-4 space-y-3 animate-fade-in hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="font-mono text-xs font-semibold text-primary">{expense.requestId}</p>
          <p className="font-medium text-sm text-foreground leading-tight">{expense.purpose}</p>
        </div>
        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${statusColorMap[expense.status]}`}>
          {STATUS_LABELS[expense.status]}
        </span>
      </div>

      <div className="space-y-1 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          {format(expense.date, "yyyy-MM-dd HH:mm", { locale: ru })}
        </div>
        <p>Проект: <span className="text-foreground">{expense.projectName}</span></p>
        <p>Ответственный: <span className="text-foreground">{expense.createdBy}</span></p>
      </div>

      <div className="pt-2 border-t space-y-1">
        <div className="flex items-center justify-between">
          <span className="font-display font-semibold text-sm text-foreground">
            {expense.totalAmount.toLocaleString()}
          </span>
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" onClick={handleDownload}>
            <Download className="w-3 h-3" />
            Смета
          </Button>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">{expense.currency}</span>
          <Button variant="outline" size="sm" className="h-7 text-xs gap-1" onClick={handleOpen}>
            <Eye className="w-3 h-3" />
            Открыть
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ExpenseCard;
