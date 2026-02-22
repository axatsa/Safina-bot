import { useState } from "react";
import { store } from "@/lib/store";
import { TeamMember, Project } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Users, ShieldCheck, ShieldAlert, Loader2, Trash2 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const Team = () => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    lastName: "",
    firstName: "",
    projectIds: [] as string[],
    login: "",
    password: "",
    position: "",
  });

  const { data: team = [], isLoading: isTeamLoading } = useQuery({
    queryKey: ["team"],
    queryFn: () => store.getTeam(),
  });

  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: () => store.getProjects(),
  });

  const mutation = useMutation({
    mutationFn: (newMember: any) => store.createTeamMember(newMember),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team"] });
      setFormData({ lastName: "", firstName: "", projectIds: [], login: "", password: "", position: "" });
      toast.success("Участник добавлен");
    },
    onError: () => toast.error("Ошибка при добавлении")
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => store.deleteTeamMember(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team"] });
      toast.success("Участник удален");
    },
    onError: () => toast.error("Ошибка при удалении")
  });

  const handleDeleteMember = (id: string) => {
    if (confirm("Вы уверены, что хотите удалить этого участника?")) {
      deleteMutation.mutate(id);
    }
  };

  const handleAddMember = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.projectIds.length > 0) {
      mutation.mutate(formData);
    } else {
      toast.error("Выберите хотя бы один проект");
    }
  };

  const toggleProject = (id: string) => {
    setFormData(prev => ({
      ...prev,
      projectIds: prev.projectIds.includes(id)
        ? prev.projectIds.filter(p => p !== id)
        : [...prev.projectIds, id]
    }));
  };

  if (isTeamLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8 animate-slide-in">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Команда</h1>
        <p className="text-sm text-muted-foreground mt-1">Управление участниками проектов</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
        <div className="xl:col-span-1 glass-card p-6 rounded-2xl border space-y-6 h-fit">
          <h2 className="font-display font-bold text-lg flex items-center gap-2">
            <Plus className="w-5 h-5 text-primary" />
            Добавить участника
          </h2>
          <form onSubmit={handleAddMember} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="lastName">Фамилия</Label>
              <Input
                id="lastName"
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="firstName">Имя</Label>
              <Input
                id="firstName"
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="position">Должность (для сметы)</Label>
              <Input
                id="position"
                value={formData.position}
                onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                placeholder="например: Операционный директор"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Проекты</Label>
              <div className="space-y-2 max-h-[150px] overflow-y-auto p-2 border rounded-md">
                {projects.map((p: Project) => (
                  <label key={p.id} className="flex items-center gap-2 hover:bg-muted/50 p-1 rounded cursor-pointer transition-colors">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                      checked={formData.projectIds.includes(p.id)}
                      onChange={() => toggleProject(p.id)}
                    />
                    <span className="text-sm">{p.name}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="login">Логин</Label>
              <Input
                id="login"
                value={formData.login}
                onChange={(e) => setFormData({ ...formData, login: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                minLength={6}
              />
            </div>
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Сохранить
            </Button>
          </form>
        </div>

        <div className="xl:col-span-3">
          <div className="glass-card rounded-2xl border overflow-hidden">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b bg-muted/30">
                  <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Участник
                  </th>
                  <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Должность
                  </th>
                  <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Проекты
                  </th>
                  <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Логин
                  </th>
                  <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Статус
                  </th>
                  <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider text-right">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {team.map((member: TeamMember) => {
                  return (
                    <tr key={member.id} className="hover:bg-muted/10 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                            {(member.lastName || "?")[0]}{(member.firstName || "?")[0]}
                          </div>
                          <div>
                            <p className="font-display font-semibold text-sm">
                              {member.lastName} {member.firstName}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {member.position || "—"}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1.5">
                          {(member.projects || []).map(p => (
                            <span key={p.id} className="text-[10px] font-medium inline-flex items-center gap-1 bg-primary/5 text-primary px-2 py-0.5 rounded-full border border-primary/10">
                              {p.name}
                            </span>
                          ))}
                          {(!member.projects || member.projects.length === 0) && <span className="text-xs text-muted-foreground">—</span>}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <code className="text-xs bg-muted px-2 py-1 rounded">
                          {member.login}
                        </code>
                      </td>
                      <td className="px-6 py-4">
                        {member.status === "active" ? (
                          <div className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                            <ShieldCheck className="w-3 h-3" />
                            Активен
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 px-2.5 py-1 rounded-full border border-red-100">
                            <ShieldAlert className="w-3 h-3" />
                            Заблокирован
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-muted-foreground hover:text-red-600 transition-colors"
                          onClick={() => handleDeleteMember(member.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Team;
