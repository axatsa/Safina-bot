import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { Calendar as CalendarIcon, Download, Filter, X, Search, Building2 } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { Project, TeamMember } from "@/lib/types";

interface FilterBarProps {
  projects: Project[];
  selectedProjectIds: string[];
  onProjectIdsChange: (v: string[]) => void;
  selectedBranchIds: string[];
  onBranchIdsChange: (v: string[]) => void;
  team?: TeamMember[];
  selectedUser?: string;
  onUserChange?: (v: string) => void;
  dateRange: { from?: Date; to?: Date };
  onDateRangeChange: (range: { from?: Date; to?: Date }) => void;
  onExport: (allStatuses: boolean) => void;
  searchQuery: string;
  onSearchChange: (v: string) => void;
  hideExport?: boolean;
}

const FilterBar = ({
  projects, selectedProjectIds, onProjectIdsChange,
  selectedBranchIds, onBranchIdsChange,
  team, selectedUser, onUserChange,
  dateRange, onDateRangeChange, onExport,
  searchQuery, onSearchChange,
  hideExport = false,
}: FilterBarProps) => {
  const [calOpen, setCalOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [allStatuses, setAllStatuses] = useState(false);

  const hasFilters = selectedProjectIds.length > 0 || selectedBranchIds.length > 0 || (selectedUser && selectedUser !== "all") || dateRange.from || dateRange.to || searchQuery;

  const clearFilters = () => {
    onProjectIdsChange([]);
    onBranchIdsChange([]);
    if (onUserChange) onUserChange("all");
    onDateRangeChange({});
    onSearchChange("");
  };

  const getAvailableBranches = () => {
    if (selectedProjectIds.length === 0) {
      return projects.flatMap(p => p.branches || []);
    }
    return projects
      .filter(p => selectedProjectIds.includes(p.id))
      .flatMap(p => p.branches || []);
  };

  const availableBranches = getAvailableBranches();

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
          placeholder="Поиск (ID или товар)..."
          className="h-9 w-[180px] pl-8 text-sm"
        />
      </div>

      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" className="h-9 min-w-[200px] justify-between text-sm px-3 font-normal">
            <span className="truncate flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 text-primary" />
              {selectedProjectIds.length === 0 && selectedBranchIds.length === 0 
                ? "Проекты и филиалы" 
                : (selectedProjectIds.length > 0 ? `Проектов: ${selectedProjectIds.length}` : "") + 
                  (selectedProjectIds.length > 0 && selectedBranchIds.length > 0 ? ", " : "") +
                  (selectedBranchIds.length > 0 ? `Филиалов: ${selectedBranchIds.length}` : "")
              }
            </span>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[320px] p-0" align="start">
          <div className="p-2 border-b bg-muted/20 flex items-center justify-between">
            <span className="text-xs font-bold uppercase text-muted-foreground px-2">Фильтр объектов</span>
            {(selectedProjectIds.length > 0 || selectedBranchIds.length > 0) && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => { onProjectIdsChange([]); onBranchIdsChange([]); }}
                className="h-7 text-[10px] hover:text-destructive"
              >
                Сбросить
              </Button>
            )}
          </div>
          <div className="max-h-[400px] overflow-y-auto p-2 space-y-2">
            {projects.map((p) => (
              <div key={p.id} className="space-y-1">
                <label className="flex items-center space-x-2 p-1.5 hover:bg-primary/5 rounded-md cursor-pointer group">
                  <Checkbox
                    checked={selectedProjectIds.includes(p.id)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        onProjectIdsChange([...selectedProjectIds, p.id]);
                      } else {
                        onProjectIdsChange(selectedProjectIds.filter(id => id !== p.id));
                        // Also unselect all branches of this project if project is unselected? 
                        // Usually better to keep them if they were individually selected, but nested UI implies dependence.
                        const pBranches = (p.branches || []).map(b => b.id);
                        onBranchIdsChange(selectedBranchIds.filter(id => !pBranches.includes(id)));
                      }
                    }}
                    className="data-[state=checked]:bg-primary"
                  />
                  <span className="text-sm font-bold truncate group-hover:text-primary transition-colors">{p.name}</span>
                </label>
                
                {p.branches && p.branches.length > 0 && (
                  <div className="pl-6 space-y-1 border-l ml-3.5 border-primary/20 animate-in slide-in-from-left-1">
                    {p.branches.map((b) => (
                      <label key={b.id} className="flex items-center space-x-2 p-1 hover:bg-muted rounded-md cursor-pointer group">
                        <Checkbox
                          checked={selectedBranchIds.includes(b.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              onBranchIdsChange([...selectedBranchIds, b.id]);
                            } else {
                              onBranchIdsChange(selectedBranchIds.filter(id => id !== b.id));
                            }
                          }}
                        />
                        <span className="text-xs truncate group-hover:text-foreground transition-colors">{b.name}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {projects.length === 0 && <div className="p-4 text-xs text-muted-foreground text-center italic">Нет доступных проектов</div>}
          </div>
        </PopoverContent>
      </Popover>

      {team && selectedUser !== undefined && onUserChange && (
        <Select value={selectedUser} onValueChange={onUserChange}>
          <SelectTrigger className="w-[180px] h-9 text-sm">
            <SelectValue placeholder="Все сотрудники" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Все сотрудники</SelectItem>
            {team.map((m) => (
              <SelectItem key={m.id} value={m.id}>{m.lastName} {m.firstName}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

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

      {!hideExport && (
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
                  Скачать .xlsx
                </Button>
              </div>
            </PopoverContent>
          </Popover>
        </div>
      )}
    </div>
  );
};

export default FilterBar;
