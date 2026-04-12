import { useState } from "react";
import { store } from "@/lib/store";
import { TeamMember, Project } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Users, ShieldCheck, ShieldAlert, Loader2, Trash2, KeyRound, Pencil, Lock, PlusCircle, Building2 } from "lucide-react";
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
    { id: "land", label: "Thompson Land" },
    { id: "ls", label: "Learning Center (LS)" },
    { id: "management", label: "Management" },
    { id: "school", label: "School" },
    { id: "refund", label: "Заявление на возврат" },
];

// ── Edit dialog state type ──────────────────────────────────────────────────
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

const Team = () => {
  const queryClient = useQueryClient();

  // Add-member form
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

  // Edit dialog
  const [editOpen, setEditOpen] = useState(false);
  const [editMember, setEditMember] = useState<TeamMember | null>(null);
  const [editForm, setEditForm] = useState<EditFormState>({
    lastName: "", firstName: "", position: "", branchIds: [],
    login: "", password: "", projectIds: [], templates: [],
  });
  const [editTab, setEditTab] = useState<"basic" | "forms">("basic");

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

  // Fetch branches for selected projects (for creation form)
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

  // Fetch branches for edit form
  const { data: editAvailableBranches = [] } = useQuery({
    queryKey: ["branches-for-edit", editForm.projectIds],
    queryFn: async () => {
        const corpProjectIds = editForm.projectIds.filter(id => corporateProjects.some(cp => cp.id === id));
        if (corpProjectIds.length === 0) return [];
        const results = await Promise.all(corpProjectIds.map(id => store.getBranches(id)));
        return results.flat();
    },
    enabled: editOpen && editForm.projectIds.length > 0
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
    setEditTab("basic");
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
        const newProjects = isRemoving
            ? prev.projectIds.filter(p => p !== id)
            : [...prev.projectIds, id];
        
        return {
            ...prev,
            projectIds: newProjects
        };
    });
  };

  const toggleBranch = (id: string) => {
    setFormData(prev => ({
      ...prev,
      branchIds: prev.branchIds.includes(id)
        ? prev.branchIds.filter(b => b !== id)
        : [...prev.branchIds, id]
    }));
  };

  // Compute project-inherited templates for the member being edited
  const projectInheritedTemplates: string[] = editForm.projectIds
    ? [...new Set(
        allProjects
            .filter((p: Project) => editForm.projectIds.includes(p.id))
            .flatMap((p: Project) => p.templates || [])
      )]
    : [];

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
                
                <div className="space-y-1">
                  <Label>Назначить на проекты</Label>
                  <div className="space-y-1.5 max-h-[120px] overflow-y-auto p-2 border rounded-md bg-muted/20">
                    {allProjects.map((p: Project) => (
                      <label key={p.id} className="flex items-center gap-2 hover:bg-muted/50 p-1 rounded cursor-pointer transition-colors">
                        <Checkbox
                          checked={formData.projectIds.includes(p.id)}
                          onCheckedChange={() => toggleProject(p.id)}
                        />
                        <span className="text-xs truncate">{p.name} {p.category === 'corporate' ? '' : ''}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {availableBranches.length > 0 && (
                    <div className="space-y-1">
                        <Label className="flex items-center gap-1.5"><Building2 className="w-3.5 h-3.5" /> Выбрать филиалы</Label>
                        <div className="space-y-1.5 max-h-[120px] overflow-y-auto p-2 border rounded-md bg-muted/20">
                            {availableBranches.map((b: Branch) => (
                                <label key={b.id} className="flex items-center gap-2 hover:bg-muted/50 p-1 rounded cursor-pointer transition-colors">
                                    <Checkbox
                                        checked={formData.branchIds.includes(b.id)}
                                        onCheckedChange={() => toggleBranch(b.id)}
                                    />
                                    <span className="text-xs truncate">{b.name}</span>
                                </label>
                            ))}
                        </div>
                    </div>
                )}

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
                            <td className="px-6 py-4">
                                <div className="flex flex-wrap gap-1">
                                    {(member.projects || []).map(p => (
                                        <span key={p.id} className="text-[9px] bg-primary/5 text-primary px-1.5 py-0.5 rounded border border-primary/10">
                                            {p.name}
                                        </span>
                                    ))}
                                    {(member.branches || []).map(b => (
                                        <span key={b.id} className="text-[9px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 flex items-center gap-0.5">
                                            <Building2 className="w-2.5 h-2.5" />
                                            {b.name}
                                        </span>
                                    ))}
                                    {(!member.projects?.length && !member.branches?.length) && <span className="text-xs text-muted-foreground">—</span>}
                                </div>
                            </td>
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
            <DialogTitle>
              Редактировать: {editMember?.lastName} {editMember?.firstName}
            </DialogTitle>
          </DialogHeader>

          {/* Tab switcher */}
          <div className="flex bg-muted p-1 rounded-lg mb-4">
            <button
              className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${editTab === 'basic' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
              onClick={() => setEditTab('basic')}
            >
              Основное
            </button>
            <button
              className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${editTab === 'forms' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
              onClick={() => setEditTab('forms')}
            >
              Доступ к формам
            </button>
          </div>

          {editTab === 'basic' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Фамилия</Label>
                  <Input value={editForm.lastName} onChange={e => setEditForm(p => ({ ...p, lastName: e.target.value }))} />
                </div>
                <div className="space-y-2">
                  <Label>Имя</Label>
                  <Input value={editForm.firstName} onChange={e => setEditForm(p => ({ ...p, firstName: e.target.value }))} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Должность</Label>
                <Input value={editForm.position} onChange={e => setEditForm(p => ({ ...p, position: e.target.value }))} placeholder="Учитель, admin, ceo..." />
              </div>
              <div className="space-y-1">
                <Label>Проекты и Филиалы</Label>
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2 p-3 border rounded-lg bg-muted/5">
                        <Label className="text-[10px] uppercase text-muted-foreground font-bold">Проекты</Label>
                        <div className="space-y-1 max-h-[150px] overflow-y-auto">
                            {allProjects.map(p => (
                                <label key={p.id} className="flex items-center gap-2 hover:bg-muted/50 p-1 rounded cursor-pointer">
                                    <Checkbox
                                        checked={editForm.projectIds.includes(p.id)}
                                        onCheckedChange={(checked) => {
                                            setEditForm(prev => ({
                                                ...prev,
                                                projectIds: checked ? [...prev.projectIds, p.id] : prev.projectIds.filter(id => id !== p.id)
                                            }));
                                        }}
                                    />
                                    <span className="text-xs truncate">{p.name}</span>
                                </label>
                            ))}
                        </div>
                    </div>
                    <div className="space-y-2 p-3 border rounded-lg bg-muted/5">
                        <Label className="text-[10px] uppercase text-muted-foreground font-bold">Филиалы</Label>
                        <div className="space-y-1 max-h-[150px] overflow-y-auto">
                            {editAvailableBranches.map(b => (
                                <label key={b.id} className="flex items-center gap-2 hover:bg-muted/50 p-1 rounded cursor-pointer">
                                    <Checkbox
                                        checked={editForm.branchIds.includes(b.id)}
                                        onCheckedChange={(checked) => {
                                            setEditForm(prev => ({
                                                ...prev,
                                                branchIds: checked ? [...prev.branchIds, b.id] : prev.branchIds.filter(id => id !== b.id)
                                            }));
                                        }}
                                    />
                                    <span className="text-xs truncate">{b.name}</span>
                                </label>
                            ))}
                            {editAvailableBranches.length === 0 && (
                                <p className="text-[10px] text-muted-foreground italic">Сперва выберите проект</p>
                            )}
                        </div>
                    </div>
                </div>
              </div>
            </div>
          )}

          {editTab === 'forms' && (
            <div className="space-y-5">
              {/* Block 1: project-inherited (read-only) */}
              <div>
                <div className="space-y-4 mb-6">
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-4 h-4 text-primary" />
                    <p className="text-sm font-semibold">Назначенные проекты</p>
                  </div>
                  <div className="grid grid-cols-2 gap-2 p-3 border rounded-lg bg-muted/10">
                    {projects.map((p: Project) => (
                      <label key={p.id} className="flex items-center gap-2 hover:bg-muted/50 p-1 rounded cursor-pointer transition-colors">
                        <Checkbox
                          checked={editForm.projectIds.includes(p.id)}
                          onCheckedChange={(checked) => {
                            setEditForm(prev => ({
                              ...prev,
                              projectIds: checked
                                ? [...prev.projectIds, p.id]
                                : prev.projectIds.filter(id => id !== p.id)
                            }));
                          }}
                        />
                        <span className="text-sm truncate" title={p.name}>{p.name}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2 mb-3">
                  <Lock className="w-4 h-4 text-muted-foreground" />
                  <p className="text-sm font-semibold text-muted-foreground">Формы из проектов</p>
                  <span className="text-[10px] bg-muted text-muted-foreground px-2 py-0.5 rounded-full">автоматически</span>
                </div>
                <div className="space-y-2 p-3 border rounded-lg bg-muted/5">
                  {projectInheritedTemplates.length > 0 ? projectInheritedTemplates.map(tplId => {
                    const tpl = AVAILABLE_TEMPLATES.find(t => t.id === tplId);
                    return (
                      <div key={tplId} className="flex items-center gap-3 opacity-60">
                        <Checkbox checked disabled />
                        <span className="text-sm">{tpl?.label || tplId}</span>
                      </div>
                    );
                  }) : (
                    <p className="text-xs text-muted-foreground italic">Нет форм из проектов. Выберите проекты выше.</p>
                  )}
                </div>
                <p className="text-[11px] text-muted-foreground mt-1 italic">
                  Управляется на странице «Проекты» → шаблоны проекта.
                </p>
              </div>

              {/* Block 2: personal additional (editable) */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <PlusCircle className="w-4 h-4 text-primary" />
                  <p className="text-sm font-semibold">Дополнительные личные формы</p>
                </div>
                <div className="space-y-2 p-3 border rounded-lg">
                  {AVAILABLE_TEMPLATES.map(tpl => {
                    const fromProject = projectInheritedTemplates.includes(tpl.id);
                    return (
                      <label
                        key={tpl.id}
                        className={`flex items-center gap-3 p-1.5 rounded-lg transition-colors ${fromProject ? 'opacity-40 cursor-not-allowed' : 'hover:bg-muted/50 cursor-pointer'}`}
                      >
                        <Checkbox
                          checked={editForm.templates.includes(tpl.id)}
                          disabled={fromProject}
                          onCheckedChange={(checked) => {
                            if (fromProject) return;
                            setEditForm(prev => ({
                              ...prev,
                              templates: checked
                                ? [...prev.templates, tpl.id]
                                : prev.templates.filter(id => id !== tpl.id)
                            }));
                          }}
                        />
                        <div>
                          <p className="text-sm font-medium">{tpl.label}</p>
                          {fromProject && (
                            <p className="text-[10px] text-muted-foreground">Уже включена через проект</p>
                          )}
                        </div>
                      </label>
                    );
                  })}
                </div>
                <p className="text-[11px] text-muted-foreground mt-1 italic">
                  * Эти формы доступны сотруднику в боте ПОМИМО форм его проектов.
                </p>
              </div>
            </div>
          )}

          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setEditOpen(false)}>Отмена</Button>
            <Button onClick={handleEditSave} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Сохранить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Team;
