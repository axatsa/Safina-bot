import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { Calendar as CalendarIcon, Download, Filter, X, Search } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { Project } from "@/lib/types";

interface FilterBarProps {
  projects: Project[];
  selectedProject: string;
  onProjectChange: (v: string) => void;
  dateRange: { from?: Date; to?: Date };
  onDateRangeChange: (range: { from?: Date; to?: Date }) => void;
  onExport: (allStatuses: boolean) => void;
  searchQuery: string;
  onSearchChange: (v: string) => void;
}

const FilterBar = ({
  projects, selectedProject, onProjectChange,
  dateRange, onDateRangeChange, onExport,
  searchQuery, onSearchChange,
}: FilterBarProps) => {
  const [calOpen, setCalOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [allStatuses, setAllStatuses] = useState(false);

  const hasFilters = selectedProject !== "all" || dateRange.from || dateRange.to || searchQuery;

  const clearFilters = () => {
    onProjectChange("all");
    onDateRangeChange({});
    onSearchChange("");
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <Filter className="w-4 h-4" />
      </div>

      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Поиск по ID..."
          className="h-9 w-[150px] pl-8 text-sm"
        />
      </div>

      <Select value={selectedProject} onValueChange={onProjectChange}>
        <SelectTrigger className="w-[180px] h-9 text-sm">
          <SelectValue placeholder="Все проекты" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все проекты</SelectItem>
          {projects.map((p) => (
            <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Popover open={calOpen} onOpenChange={setCalOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className={cn("h-9 text-sm gap-2", dateRange.from && "text-foreground")}>
            <CalendarIcon className="w-4 h-4" />
            {dateRange.from
              ? dateRange.to
                ? `${format(dateRange.from, "dd.MM", { locale: ru })} — ${format(dateRange.to, "dd.MM", { locale: ru })}`
                : format(dateRange.from, "dd MMM yyyy", { locale: ru })
              : "Период"
            }
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="range"
            selected={dateRange.from ? { from: dateRange.from, to: dateRange.to } : undefined}
            onSelect={(range) => {
              onDateRangeChange({ from: range?.from, to: range?.to });
              if (range?.to) setCalOpen(false);
            }}
            className="p-3 pointer-events-auto"
          />
        </PopoverContent>
      </Popover>

      {hasFilters && (
        <Button variant="ghost" size="sm" className="h-9 text-sm gap-1 text-muted-foreground" onClick={clearFilters}>
          <X className="w-3 h-3" />
          Сбросить
        </Button>
      )}

      <div className="ml-auto">
        <Popover open={exportOpen} onOpenChange={setExportOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="h-9 text-sm gap-2">
              <Download className="w-4 h-4" />
              Скачать расходы
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-64" align="end">
            <div className="space-y-3">
              <p className="text-sm font-medium">Экспорт расходов</p>
              <p className="text-xs text-muted-foreground">
                По умолчанию экспорт только подтверждённых заявок.
              </p>
              <div className="flex items-center gap-2">
                <Checkbox
                  id="allStatuses"
                  checked={allStatuses}
                  onCheckedChange={(v) => setAllStatuses(!!v)}
                />
                <label htmlFor="allStatuses" className="text-sm">Все статусы (вкл. архив)</label>
              </div>
              <Button
                size="sm"
                className="w-full"
                onClick={() => {
                  onExport(allStatuses);
                  setExportOpen(false);
                }}
              >
                Скачать CSV
              </Button>
            </div>
          </PopoverContent>
        </Popover>
      </div>
    </div>
  );
};

export default FilterBar;
