import React from "react";
import { LucideIcon } from "lucide-react";
import { Button } from "./button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  action?: {
    label: string;
    fn: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  subtitle,
  action,
  className,
}) => {
  return (
    <div className={cn("flex flex-col items-center justify-center py-16 text-center animate-in fade-in zoom-in duration-300", className)}>
      <div className="w-16 h-16 bg-muted/30 rounded-full flex items-center justify-center mb-6">
        <Icon className="w-8 h-8 text-muted-foreground/40" />
      </div>
      <h3 className="text-xl font-display font-bold text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground/70 max-w-[250px] mx-auto leading-relaxed">
        {subtitle}
      </p>
      {action && (
        <Button className="mt-8 px-8" onClick={action.fn}>
          {action.label}
        </Button>
      )}
    </div>
  );
};
