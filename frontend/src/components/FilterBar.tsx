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
        <PopoverContent className="w-[600px] p-0 rounded-2xl shadow-xl border-primary/10 overflow-hidden" align="start">
          <div className="p-3 border-b bg-muted/20 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-2">Фильтр объектов</h3>
            <div className="flex gap-2">
              {(selectedProjectIds.length > 0 || selectedBranchIds.length > 0) && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => { onProjectIdsChange([]); onBranchIdsChange([]); }}
                  className="h-7 text-[10px] hover:text-destructive"
                >
                  Сбросить всё
                </Button>
              )}
            </div>
          </div>
          
          <div className="flex h-[400px]">
            {/* Projects Column */}
            <div className="w-1/2 border-r flex flex-col bg-background">
              <div className="p-2 border-b bg-muted/5 flex items-center justify-between">
                <span className="text-[9px] font-bold uppercase text-muted-foreground/60 px-2 tracking-widest">Проекты</span>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="h-6 px-2 text-[9px]"
                  onClick={() => {
                    if (selectedProjectIds.length === projects.length) {
                      onProjectIdsChange([]);
                      onBranchIdsChange([]);
                    } else {
                      onProjectIdsChange(projects.map(p => p.id));
                    }
                  }}
                >
                  {selectedProjectIds.length === projects.length ? "Снять все" : "Выбрать все"}
                </Button>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {projects.map((p) => (
                  <div 
                    key={p.id} 
                    className={`flex items-center space-x-3 p-2 rounded-lg cursor-pointer transition-all ${selectedProjectIds.includes(p.id) ? 'bg-primary/5 ring-1 ring-primary/10' : 'hover:bg-muted'}`}
                    onClick={() => {
                        const isSelected = selectedProjectIds.includes(p.id);
                        if (isSelected) {
                          onProjectIdsChange(selectedProjectIds.filter(id => id !== p.id));
                          const pBranches = (p.branches || []).map(b => b.id);
                          onBranchIdsChange(selectedBranchIds.filter(id => !pBranches.includes(id)));
                        } else {
                          onProjectIdsChange([...selectedProjectIds, p.id]);
                        }
                    }}
                  >
                    <Checkbox
                      checked={selectedProjectIds.includes(p.id)}
                      onCheckedChange={() => {}} 
                      className="pointer-events-none"
                    />
                    <span className={`text-sm font-semibold truncate ${selectedProjectIds.includes(p.id) ? 'text-primary' : ''}`}>{p.name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Branches Column */}
            <div className="w-1/2 flex flex-col bg-muted/5">
              <div className="p-2 border-b bg-muted/5 flex items-center justify-between">
                <span className="text-[9px] font-bold uppercase text-muted-foreground/60 px-2 tracking-widest">Филиалы</span>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="h-6 px-2 text-[9px]"
                  disabled={availableBranches.length === 0}
                  onClick={() => {
                    const availableIds = availableBranches.map(b => b.id);
                    const allSelected = availableIds.every(id => selectedBranchIds.includes(id));
                    if (allSelected) {
                      onBranchIdsChange(selectedBranchIds.filter(id => !availableIds.includes(id)));
                    } else {
                      onBranchIdsChange([...new Set([...selectedBranchIds, ...availableIds])]);
                    }
                  }}
                >
                  {availableBranches.every(b => selectedBranchIds.includes(b.id)) && availableBranches.length > 0 ? "Снять все" : "Выбрать все"}
                </Button>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {selectedProjectIds.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center p-6 text-center opacity-40">
                    <Building2 className="w-8 h-8 mb-2" />
                    <p className="text-[10px]">Выберите проект</p>
                  </div>
                ) : projects.filter(p => selectedProjectIds.includes(p.id)).map(p => (
                   <div key={p.id} className="space-y-1 pt-2 first:pt-0">
                      <div className="px-2 pb-0.5">
                        <span className="text-[9px] font-black text-primary/40 uppercase tracking-tighter">{p.name}</span>
                      </div>
                      {p.branches?.map((b) => (
                        <div 
                          key={b.id} 
                          className={`flex items-center space-x-3 p-1.5 rounded-md cursor-pointer transition-all ${selectedBranchIds.includes(b.id) ? 'bg-primary/5' : 'hover:bg-muted'}`}
                          onClick={() => {
                              if (selectedBranchIds.includes(b.id)) {
                                onBranchIdsChange(selectedBranchIds.filter(id => id !== b.id));
                              } else {
                                onBranchIdsChange([...selectedBranchIds, b.id]);
                              }
                          }}
                        >
                          <Checkbox
                            checked={selectedBranchIds.includes(b.id)}
                            onCheckedChange={() => {}}
                            className="w-3.5 h-3.5 pointer-events-none"
                          />
                          <span className="text-xs truncate">{b.name}</span>
                        </div>
                      ))}
                      {(!p.branches || p.branches.length === 0) && (
                        <p className="px-2 text-[10px] text-muted-foreground italic">Нет филиалов</p>
                      )}
                   </div>
                ))}
              </div>
            </div>
          </div>
          <div className="p-2 border-t bg-muted/20 flex justify-end">
             <PopoverTrigger asChild>
                <Button size="sm" className="h-8 text-[10px] font-bold px-4">Готово</Button>
             </PopoverTrigger>
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
