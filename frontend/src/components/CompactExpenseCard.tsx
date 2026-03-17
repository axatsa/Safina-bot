import { ExpenseRequest } from "@/lib/types";
import { useNavigate } from "react-router-dom";

interface CompactExpenseCardProps {
  expense: ExpenseRequest;
}

const CompactExpenseCard = ({ expense }: CompactExpenseCardProps) => {
  const navigate = useNavigate();

  return (
    <div
      className="bg-card rounded border px-3 py-2 flex items-center gap-2 cursor-pointer hover:shadow-sm transition-shadow animate-fade-in"
      onClick={() => navigate(`/dashboard/expense/${expense.id}`)}
    >
      <span className="font-mono text-[10px] font-bold text-primary shrink-0">
        {expense.projectCode}
      </span>
      <span className="text-xs text-foreground truncate">{expense.purpose}</span>
    </div>
  );
};

export default CompactExpenseCard;
