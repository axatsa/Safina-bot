import { useState } from "react";
import { store } from "@/lib/store";
import { TeamMember, Project } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Users, ShieldCheck, ShieldAlert, Loader2, Trash2, KeyRound, Pencil, Building2, ChevronDown, ChevronRight, FolderKanban, FileText, Info, Eye, EyeOff } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { EmptyState } from "@/components/ui/empty-state";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const AVAILABLE_TEMPLATES = [
    { id: "land", label: "Thompson Land", description: "Форма заявок для проекта Land" },
    { id: "ls", label: "Learning Center (LS)", description: "Форма для учебного центра" },
    { id: "management", label: "Management", description: "Управленческие заявки" },
    { id: "school", label: "School", description: "Форма для школы Thompson" },
    { id: "refund", label: "Заявление на возврат", description: "Оформление возврата денег клиенту" },
];

interface EditFormState {
  lastName: string;
  firstName: string;
  position: string;
  branchIds: string[];
  login: string;
  password: string;
  projectIds: string[];
  templates: string[];
}

const MemberObjects = ({ member }: { member: TeamMember }) => {
    const [expanded, setExpanded] = useState(false);
    const hasProjects = (member.projects || []).length > 0;
    const hasBranches = (member.branches || []).length > 0;

    if (!hasProjects && !hasBranches) {
        return <span className="text-xs text-muted-foreground">—</span>;
    }

    return (
        <div className="space-y-2">
            <div className="flex flex-wrap gap-1">
                {(member.projects || []).map(p => (
                    <span key={p.id} className="text-[9px] bg-primary/5 text-primary px-1.5 py-0.5 rounded border border-primary/10 font-bold uppercase tracking-tighter">
                        {p.name}
                    </span>
                ))}
            </div>
            {hasBranches && (
                <div className="space-y-1">
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="flex items-center gap-1 text-[10px] font-bold text-muted-foreground hover:text-primary transition-colors uppercase tracking-widest"
                    >
                        {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                        {expanded ? "Свернуть" : `Филиалы (${member.branches?.length})`}
                    </button>
                    {expanded && (
                        <div className="flex flex-wrap gap-1 animate-in fade-in slide-in-from-top-1">
                            {member.branches?.map(b => (
                                <span key={b.id} className="text-[9px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 flex items-center gap-0.5 font-medium">
                                    <Building2 className="w-2.5 h-2.5 opacity-50" />
                                    {b.name}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

const SectionHeader = ({ icon: Icon, title, hint }: { icon: any; title: string; hint?: string }) => (
    <div className="flex items-start gap-3 mb-4">
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
            <Icon className="w-4 h-4 text-primary" />
        </div>
        <div>
            <p className="font-bold text-sm text-foreground">{title}</p>
            {hint && <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{hint}</p>}
        </div>
    </div>
);

const Team = () => {
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    lastName: "",
    firstName: "",
    projectIds: [] as string[],
    branchIds: [] as string[],
    login: "",
    password: "",
    position: "",
    team: "",
  });

  const [editOpen, setEditOpen] = useState(false);
  const [editMember, setEditMember] = useState<TeamMember | null>(null);
  const [editForm, setEditForm] = useState<EditFormState>({
    lastName: "", firstName: "", position: "", branchIds: [],
    login: "", password: "", projectIds: [], templates: [],
  });
  const [showPassword, setShowPassword] = useState(false);

  const { data: team = [], isLoading: isTeamLoading, isError: isTeamError } = useQuery({
    queryKey: ["team"],
    queryFn: () => store.getTeam(),
  });

  const { data: corporateProjects = [] } = useQuery({
    queryKey: ["projects", "corporate"],
    queryFn: () => store.getProjects("corporate"),
  });

  const { data: startupProjects = [] } = useQuery({
    queryKey: ["projects", "startup"],
    queryFn: () => store.getProjects("startup"),
  });

  const allProjects = [...corporateProjects, ...startupProjects];

  const { data: availableBranches = [] } = useQuery({
    queryKey: ["branches-for-selection", formData.projectIds],
    queryFn: async () => {
        const corpProjectIds = formData.projectIds.filter(id => corporateProjects.some(cp => cp.id === id));
        if (corpProjectIds.length === 0) return [];
        const results = await Promise.all(corpProjectIds.map(id => store.getBranches(id)));
        return results.flat();
    },
    enabled: formData.projectIds.length > 0
  });

  const mutation = useMutation({
    mutationFn: (newMember: any) => store.createTeamMember(newMember),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team"] });
      setFormData({ lastName: "", firstName: "", projectIds: [], branchIds: [], login: "", password: "", position: "", team: "" });
      toast.success("Участник добавлен");
    },
    onError: (error: any) => toast.error(error.message || "Ошибка при добавлении")
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => store.deleteTeamMember(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team"] });
      toast.success("Участник удален");
    },
    onError: () => toast.error("Ошибка при удалении")
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EditFormState> & { password?: string } }) =>
      store.updateTeamMember(id, {
        lastName: data.lastName,
        firstName: data.firstName,
        position: data.position,
        branchIds: data.branchIds,
        login: data.login,
        password: data.password || undefined,
        projectIds: data.projectIds,
        templates: data.templates,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team"] });
      setEditOpen(false);
      toast.success("Данные обновлены");
    },
    onError: (error: any) => toast.error(error.message || "Ошибка при обновлении"),
  });

  const openEdit = (member: TeamMember) => {
    setEditMember(member);
    setEditForm({
      lastName: member.lastName,
      firstName: member.firstName,
      position: member.position || "",
      branchIds: member.branchIds || [],
      login: member.login,
      password: "",
      projectIds: member.projectIds || [],
      templates: member.templates || [],
    });
    setShowPassword(false);
    setEditOpen(true);
  };

  const handleEditSave = () => {
    if (!editMember) return;
    const payload: any = { ...editForm };
    if (!payload.password) delete payload.password;
    updateMutation.mutate({ id: editMember.id, data: payload });
  };

  const generatePassword = () => {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    let pass = "";
    for (let i = 0; i < 6; i++) {
      pass += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setFormData(prev => ({ ...prev, password: pass }));
  };

  const handleAddMember = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  const toggleProject = (id: string) => {
    setFormData(prev => {
        const isRemoving = prev.projectIds.includes(id);
        return { ...prev, projectIds: isRemoving ? prev.projectIds.filter(p => p !== id) : [...prev.projectIds, id] };
    });
  };

  const toggleBranch = (id: string) => {
    setFormData(prev => ({
      ...prev,
      branchIds: prev.branchIds.includes(id) ? prev.branchIds.filter(b => b !== id) : [...prev.branchIds, id]
    }));
  };

  // Forms that come automatically from assigned projects
  const projectInheritedTemplates: string[] = editForm.projectIds
    ? [...new Set(
        allProjects
            .filter((p: Project) => editForm.projectIds.includes(p.id))
            .flatMap((p: Project) => p.templates || [])
      )]
    : [];

  // Which projects give which templates (for display)
  const templateSourceMap: Record<string, string[]> = {};
  allProjects
    .filter((p: Project) => editForm.projectIds.includes(p.id))
    .forEach((p: Project) => {
      (p.templates || []).forEach(tplId => {
        if (!templateSourceMap[tplId]) templateSourceMap[tplId] = [];
        templateSourceMap[tplId].push(p.name);
      });
    });

  const selectedProjectCount = editForm.projectIds.length;
  const selectedBranchCount = editForm.branchIds.length;

  return (
    <div className="p-6 space-y-8 animate-slide-in">
      {isTeamLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : isTeamError ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-4">
          <ShieldAlert className="w-12 h-12 text-destructive" />
          <h2 className="text-xl font-bold">Доступ ограничен</h2>
          <p className="text-muted-foreground">У вас нет прав для просмотра этого раздела или произошла ошибка.</p>
          <Button variant="outline" onClick={() => window.history.back()}>Назад</Button>
        </div>
      ) : (
        <>
          <div>
            <h1 className="text-2xl font-display font-bold text-foreground">Команда</h1>
            <p className="text-sm text-muted-foreground mt-1">Управление участниками проектов</p>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
            {/* Add member form */}
            <div className="xl:col-span-1 glass-card p-6 rounded-2xl border space-y-6 h-fit">
              <h2 className="font-display font-bold text-lg flex items-center gap-2">
                <Plus className="w-5 h-5 text-primary" />
                Добавить участника
              </h2>
              <form onSubmit={handleAddMember} className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                        <Label htmlFor="lastName">Фамилия</Label>
                        <Input id="lastName" value={formData.lastName} onChange={(e) => setFormData({ ...formData, lastName: e.target.value })} required />
                    </div>
                    <div className="space-y-1">
                        <Label htmlFor="firstName">Имя</Label>
                        <Input id="firstName" value={formData.firstName} onChange={(e) => setFormData({ ...formData, firstName: e.target.value })} required />
                    </div>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="position">Должность</Label>
                  <Input id="position" value={formData.position} onChange={(e) => setFormData({ ...formData, position: e.target.value })} placeholder="Напр: Учитель, Бухгалтер..." />
                </div>

                <div className="space-y-1.5 pt-2">
                  <Label className="text-sm font-semibold flex items-center gap-1.5 text-primary">
                    <FolderKanban className="w-4 h-4" /> Назначить проекты и филиалы
                  </Label>
                  <div className="flex items-center gap-3 text-[10px] text-muted-foreground mb-1">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-violet-400 inline-block" />Корпоративный</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />Стартап</span>
                  </div>
                  <div className="max-h-[250px] overflow-y-auto border rounded-xl bg-muted/10">
                    {corporateProjects.length > 0 && (
                      <div>
                        <div className="px-3 pt-2.5 pb-1 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-violet-400 shrink-0" />
                          <span className="text-[9px] font-bold text-violet-500 uppercase tracking-widest">Корпоративные</span>
                        </div>
                        {corporateProjects.map((p: Project) => (
                          <div key={p.id}>
                            <label className={`flex items-center gap-2 mx-2 p-1.5 rounded-lg cursor-pointer transition-all group ${
                              formData.projectIds.includes(p.id) ? "bg-violet-50 border border-violet-200" : "hover:bg-violet-50/50 border border-transparent"
                            }`}>
                              <Checkbox
                                checked={formData.projectIds.includes(p.id)}
                                onCheckedChange={() => toggleProject(p.id)}
                                className="w-3.5 h-3.5 data-[state=checked]:bg-violet-500 data-[state=checked]:border-violet-500"
                              />
                              <div className="min-w-0">
                                <span className="text-xs font-bold truncate block text-violet-900">{p.name}</span>
                                {p.branches && p.branches.length > 0 && (
                                  <span className="text-[9px] text-violet-400 flex items-center gap-0.5">
                                    <Building2 className="w-2.5 h-2.5" />{p.branches.length} филиала
                                  </span>
                                )}
                              </div>
                            </label>
                            {formData.projectIds.includes(p.id) && p.branches && p.branches.length > 0 && (
                              <div className="ml-8 mr-2 mb-1 border-l-2 border-violet-200 pl-2 space-y-0.5 animate-in slide-in-from-top-1">
                                {p.branches.map((b: any) => (
                                  <label key={b.id} className={`flex items-center gap-2 p-1 rounded-md cursor-pointer transition-colors ${
                                    formData.branchIds.includes(b.id) ? "bg-violet-100/60" : "hover:bg-violet-50"
                                  }`}>
                                    <Checkbox
                                      checked={formData.branchIds.includes(b.id)}
                                      onCheckedChange={() => toggleBranch(b.id)}
                                      className="w-3 h-3 data-[state=checked]:bg-violet-500 data-[state=checked]:border-violet-500"
                                    />
                                    <span className="text-[11px] truncate text-violet-800 flex items-center gap-1">
                                      <Building2 className="w-2.5 h-2.5 text-violet-300" />{b.name}
                                    </span>
                                  </label>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    {startupProjects.length > 0 && (
                      <div className={corporateProjects.length > 0 ? "border-t" : ""}>
                        <div className="px-3 pt-2.5 pb-1 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-blue-400 shrink-0" />
                          <span className="text-[9px] font-bold text-blue-500 uppercase tracking-widest">Стартапы</span>
                        </div>
                        {startupProjects.map((p: Project) => (
                          <label key={p.id} className={`flex items-center gap-2 mx-2 mb-1 p-1.5 rounded-lg cursor-pointer transition-all group ${
                            formData.projectIds.includes(p.id) ? "bg-blue-50 border border-blue-200" : "hover:bg-blue-50/50 border border-transparent"
                          }`}>
                            <Checkbox
                              checked={formData.projectIds.includes(p.id)}
                              onCheckedChange={() => toggleProject(p.id)}
                              className="w-3.5 h-3.5 data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500"
                            />
                            <span className="text-xs font-bold truncate text-blue-900">{p.name}</span>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-1 pt-2 border-t">
                  <Label htmlFor="login">Логин</Label>
                  <Input id="login" value={formData.login} onChange={(e) => setFormData({ ...formData, login: e.target.value })} required />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="password">Пароль</Label>
                  <div className="flex gap-2">
                    <Input id="password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} required minLength={6} />
                    <Button type="button" variant="outline" size="icon" className="shrink-0" onClick={generatePassword}>
                      <KeyRound className="w-4 h-4 text-muted-foreground" />
                    </Button>
                  </div>
                </div>
                <Button type="submit" className="w-full" disabled={mutation.isPending}>
                  {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Сохранить
                </Button>
              </form>
            </div>

            {/* Team table */}
            <div className="xl:col-span-3">
              <div className="glass-card rounded-2xl border overflow-hidden">
                {team.length === 0 ? (
                    <div className="py-20">
                        <EmptyState icon={Users} title="Команда пуста" subtitle="Добавьте первого участника, чтобы начать работу" />
                    </div>
                ) : (
                    <table className="w-full text-left">
                    <thead>
                        <tr className="border-b bg-muted/30">
                            <th className="px-6 py-4 text-xs font-medium text-muted-foreground uppercase">Участник</th>
                            <th className="px-6 py-4 text-xs font-medium text-muted-foreground uppercase">Должность</th>
                            <th className="px-6 py-4 text-xs font-medium text-muted-foreground uppercase">Проекты / Филиалы</th>
                            <th className="px-6 py-4 text-xs font-medium text-muted-foreground uppercase">Логин</th>
                            <th className="px-6 py-4 text-xs font-medium text-muted-foreground uppercase">Статус</th>
                            <th className="px-6 py-4 text-xs font-medium text-muted-foreground uppercase text-right">Действия</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {team.map((member: TeamMember) => (
                            <tr key={member.id} className="hover:bg-muted/10 transition-colors group">
                            <td className="px-6 py-4">
                                <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                                    {(member.lastName || "?")[0]}{(member.firstName || "?")[0]}
                                </div>
                                <div>
                                    <p className="font-display font-semibold text-sm">{member.lastName} {member.firstName}</p>
                                </div>
                                </div>
                            </td>
                            <td className="px-6 py-4 text-sm text-muted-foreground">{member.position || "—"}</td>
                            <td className="px-6 py-4"><MemberObjects member={member} /></td>
                            <td className="px-6 py-4">
                                <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{member.login}</code>
                            </td>
                            <td className="px-6 py-4">
                                {member.status === "active" ? (
                                    <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                                        <ShieldCheck className="w-3 h-3" />Доступ
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center gap-1 text-[10px] text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-100">
                                        <ShieldAlert className="w-3 h-3" />Блок
                                    </span>
                                )}
                            </td>
                            <td className="px-6 py-4 text-right space-x-1">
                                <Button
                                  variant="ghost" size="icon"
                                  className="text-muted-foreground hover:text-indigo-600 transition-colors"
                                  onClick={() => openEdit(member)}
                                  title="Редактировать участника"
                                >
                                  <Pencil className="w-4 h-4" />
                                </Button>
                                <AlertDialog>
                                    <AlertDialogTrigger asChild>
                                        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-red-600 transition-colors" title="Удалить участника">
                                            <Trash2 className="w-4 h-4" />
                                        </Button>
                                    </AlertDialogTrigger>
                                    <AlertDialogContent>
                                        <AlertDialogHeader>
                                            <AlertDialogTitle>Удалить участника?</AlertDialogTitle>
                                            <AlertDialogDescription>
                                                Вы уверены, что хотите удалить этого участника? Он потеряет доступ к системе. Это действие нельзя отменить.
                                            </AlertDialogDescription>
                                        </AlertDialogHeader>
                                        <AlertDialogFooter>
                                            <AlertDialogCancel>Отмена</AlertDialogCancel>
                                            <AlertDialogAction onClick={() => deleteMutation.mutate(member.id)} className="bg-red-600 hover:bg-red-700">Удалить</AlertDialogAction>
                                        </AlertDialogFooter>
                                    </AlertDialogContent>
                                </AlertDialog>
                            </td>
                            </tr>
                        ))}
                    </tbody>
                    </table>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* ── Edit Member Dialog ─────────────────────────────────────────────── */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                {(editMember?.lastName || "?")[0]}{(editMember?.firstName || "?")[0]}
              </div>
              {editMember?.lastName} {editMember?.firstName}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6 py-2">

            {/* Block 1: Personal info */}
            <div className="space-y-3">
              <SectionHeader
                icon={Users}
                title="Личные данные"
                hint="Имя и должность сотрудника — видны в таблице команды"
              />
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Фамилия</Label>
                  <Input value={editForm.lastName} onChange={e => setEditForm(p => ({ ...p, lastName: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Имя</Label>
                  <Input value={editForm.firstName} onChange={e => setEditForm(p => ({ ...p, firstName: e.target.value }))} />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Должность</Label>
                <Input value={editForm.position} onChange={e => setEditForm(p => ({ ...p, position: e.target.value }))} placeholder="Учитель, Бухгалтер, admin, ceo..." />
              </div>
            </div>

            <div className="border-t" />

            {/* Block 2: Projects & branches */}
            <div className="space-y-3">
              <SectionHeader
                icon={FolderKanban}
                title="Проекты и филиалы"
                hint="Выберите, к каким проектам и конкретным офисам/школам имеет доступ этот сотрудник. Он сможет подавать заявки только по ним."
              />

              {/* Legend */}
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-violet-400 inline-block" />
                  Корпоративный (с филиалами)
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-400 inline-block" />
                  Стартап
                </span>
              </div>

              {/* Summary chips */}
              {(selectedProjectCount > 0 || selectedBranchCount > 0) && (
                <div className="flex flex-wrap gap-1.5 p-3 bg-muted/30 rounded-lg border">
                  {allProjects.filter(p => editForm.projectIds.includes(p.id)).map(p => {
                    const isCorp = corporateProjects.some(cp => cp.id === p.id);
                    return (
                      <span key={p.id} className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                        isCorp ? "bg-violet-100 text-violet-700 border border-violet-200" : "bg-blue-100 text-blue-700 border border-blue-200"
                      }`}>
                        {p.name}
                      </span>
                    );
                  })}
                  {selectedBranchCount > 0 && (
                    <span className="text-[11px] bg-violet-50 text-violet-600 border border-violet-100 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                      <Building2 className="w-3 h-3" />
                      {selectedBranchCount} {selectedBranchCount === 1 ? "филиал" : selectedBranchCount < 5 ? "филиала" : "филиалов"}
                    </span>
                  )}
                </div>
              )}

              <div className="space-y-1 max-h-[280px] overflow-y-auto rounded-xl border bg-muted/5">
                {/* Corporate projects group */}
                {corporateProjects.length > 0 && (
                  <div>
                    <div className="px-3 pt-3 pb-1.5 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-violet-400 shrink-0" />
                      <span className="text-[10px] font-bold text-violet-600 uppercase tracking-widest">Корпоративные</span>
                    </div>
                    {corporateProjects.map(p => (
                      <div key={p.id}>
                        <label className={`flex items-center gap-2.5 mx-2 p-2 rounded-lg cursor-pointer transition-all group ${
                          editForm.projectIds.includes(p.id)
                            ? "bg-violet-50 border border-violet-200"
                            : "hover:bg-violet-50/60 border border-transparent"
                        }`}>
                          <Checkbox
                            checked={editForm.projectIds.includes(p.id)}
                            onCheckedChange={(checked) => {
                              setEditForm(prev => {
                                const newProjects = checked ? [...prev.projectIds, p.id] : prev.projectIds.filter(id => id !== p.id);
                                let newBranches = prev.branchIds;
                                if (!checked && p.branches) {
                                  const pBranchIds = p.branches.map(b => b.id);
                                  newBranches = prev.branchIds.filter(id => !pBranchIds.includes(id));
                                }
                                return { ...prev, projectIds: newProjects, branchIds: newBranches };
                              });
                            }}
                            className="w-4 h-4 data-[state=checked]:bg-violet-500 data-[state=checked]:border-violet-500"
                          />
                          <div className="flex-1 min-w-0">
                            <span className="text-sm font-semibold truncate block text-violet-900 group-hover:text-violet-700 transition-colors">{p.name}</span>
                            {p.branches && p.branches.length > 0 && (
                              <span className="text-[10px] text-violet-400 flex items-center gap-0.5">
                                <Building2 className="w-2.5 h-2.5" />
                                {p.branches.length} {p.branches.length === 1 ? "филиал" : "филиала"}
                              </span>
                            )}
                          </div>
                        </label>

                        {editForm.projectIds.includes(p.id) && p.branches && p.branches.length > 0 && (
                          <div className="ml-9 mr-2 mb-1 space-y-0.5 animate-in slide-in-from-top-1 border-l-2 border-violet-200 pl-3">
                            <p className="text-[9px] text-violet-400 font-bold uppercase tracking-wider py-1">Выберите филиалы:</p>
                            {p.branches.map(b => (
                              <label key={b.id} className={`flex items-center gap-2 p-1.5 rounded-md cursor-pointer group/branch transition-colors ${
                                editForm.branchIds.includes(b.id) ? "bg-violet-100/60" : "hover:bg-violet-50"
                              }`}>
                                <Checkbox
                                  checked={editForm.branchIds.includes(b.id)}
                                  onCheckedChange={(checked) => {
                                    setEditForm(prev => ({
                                      ...prev,
                                      branchIds: checked ? [...prev.branchIds, b.id] : prev.branchIds.filter(id => id !== b.id)
                                    }));
                                  }}
                                  className="w-3.5 h-3.5 data-[state=checked]:bg-violet-500 data-[state=checked]:border-violet-500"
                                />
                                <span className="text-xs truncate flex items-center gap-1 text-violet-800">
                                  <Building2 className="w-3 h-3 text-violet-300" />
                                  {b.name}
                                </span>
                              </label>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Startup projects group */}
                {startupProjects.length > 0 && (
                  <div className={corporateProjects.length > 0 ? "border-t mt-1 pt-1" : ""}>
                    <div className="px-3 pt-2 pb-1.5 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-blue-400 shrink-0" />
                      <span className="text-[10px] font-bold text-blue-600 uppercase tracking-widest">Стартапы</span>
                    </div>
                    {startupProjects.map(p => (
                      <label key={p.id} className={`flex items-center gap-2.5 mx-2 mb-1 p-2 rounded-lg cursor-pointer transition-all group ${
                        editForm.projectIds.includes(p.id)
                          ? "bg-blue-50 border border-blue-200"
                          : "hover:bg-blue-50/60 border border-transparent"
                      }`}>
                        <Checkbox
                          checked={editForm.projectIds.includes(p.id)}
                          onCheckedChange={(checked) => {
                            setEditForm(prev => ({
                              ...prev,
                              projectIds: checked ? [...prev.projectIds, p.id] : prev.projectIds.filter(id => id !== p.id)
                            }));
                          }}
                          className="w-4 h-4 data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500"
                        />
                        <span className="text-sm font-semibold truncate text-blue-900 group-hover:text-blue-700 transition-colors">{p.name}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="border-t" />

            {/* Block 3: Forms access */}
            <div className="space-y-3">
              <SectionHeader
                icon={FileText}
                title="Доступ к формам в боте"
                hint="Какие типы заявок сотрудник видит в Telegram-боте. Часть форм добавляется автоматически через проекты — их менять не нужно."
              />

              {/* Auto-inherited forms */}
              {projectInheritedTemplates.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                    Автоматически через проекты
                  </p>
                  <div className="p-3 bg-emerald-50/60 border border-emerald-100 rounded-lg space-y-1.5">
                    {projectInheritedTemplates.map(tplId => {
                      const tpl = AVAILABLE_TEMPLATES.find(t => t.id === tplId);
                      const sources = templateSourceMap[tplId] || [];
                      return (
                        <div key={tplId} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded bg-emerald-500 flex items-center justify-center">
                              <ShieldCheck className="w-2.5 h-2.5 text-white" />
                            </div>
                            <span className="text-sm font-medium text-emerald-800">{tpl?.label || tplId}</span>
                          </div>
                          <span className="text-[10px] text-emerald-600 bg-emerald-100 px-1.5 py-0.5 rounded-full">
                            через {sources.join(", ")}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Manual extra forms */}
              <div className="space-y-2">
                <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <Plus className="w-3.5 h-3.5 text-primary" />
                  Добавить отдельно
                  <span className="text-[9px] bg-muted px-1.5 py-0.5 rounded-full normal-case tracking-normal font-normal">
                    не входит ни в один проект выше
                  </span>
                </p>
                <div className="space-y-1 border rounded-lg overflow-hidden">
                  {AVAILABLE_TEMPLATES.map(tpl => {
                    const fromProject = projectInheritedTemplates.includes(tpl.id);
                    if (fromProject) return null;
                    return (
                      <label
                        key={tpl.id}
                        className="flex items-center gap-3 p-3 hover:bg-muted/40 cursor-pointer transition-colors border-b last:border-0 group"
                      >
                        <Checkbox
                          checked={editForm.templates.includes(tpl.id)}
                          onCheckedChange={(checked) => {
                            setEditForm(prev => ({
                              ...prev,
                              templates: checked
                                ? [...prev.templates, tpl.id]
                                : prev.templates.filter(id => id !== tpl.id)
                            }));
                          }}
                          className="w-4 h-4 data-[state=checked]:bg-primary"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium group-hover:text-primary transition-colors">{tpl.label}</p>
                          <p className="text-[11px] text-muted-foreground">{tpl.description}</p>
                        </div>
                      </label>
                    );
                  })}
                  {AVAILABLE_TEMPLATES.every(t => projectInheritedTemplates.includes(t.id)) && (
                    <p className="text-xs text-muted-foreground italic p-3">
                      Все доступные формы уже включены через проекты.
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="border-t" />

            {/* Block 4: Login credentials */}
            <div className="space-y-3">
              <SectionHeader
                icon={KeyRound}
                title="Данные для входа"
                hint="Логин и пароль для входа в систему. Пароль менять необязательно — оставьте поле пустым, если хотите сохранить старый."
              />
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Логин</Label>
                <Input value={editForm.login} onChange={e => setEditForm(p => ({ ...p, login: e.target.value }))} />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Новый пароль <span className="text-muted-foreground/60">(оставьте пустым, чтобы не менять)</span></Label>
                <div className="relative">
                  <Input
                    type={showPassword ? "text" : "password"}
                    value={editForm.password}
                    onChange={e => setEditForm(p => ({ ...p, password: e.target.value }))}
                    placeholder="Введите новый пароль..."
                    className="pr-10"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    onClick={() => setShowPassword(v => !v)}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Tip box */}
              <div className="flex gap-2 p-3 bg-amber-50 border border-amber-100 rounded-lg">
                <Info className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                <p className="text-xs text-amber-700 leading-relaxed">
                  После сохранения изменений сотрудник должен <strong>перезапустить бот</strong> (/start), чтобы обновлённые доступы применились.
                </p>
              </div>
            </div>
          </div>

          <DialogFooter className="mt-2">
            <Button variant="outline" onClick={() => setEditOpen(false)}>Отмена</Button>
            <Button onClick={handleEditSave} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Сохранить изменения
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Team;
