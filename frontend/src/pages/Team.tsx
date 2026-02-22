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
import { Plus, Users, ShieldCheck, ShieldAlert, Loader2 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const Team = () => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    lastName: "",
    firstName: "",
    projectId: "",
    login: "",
    password: "",
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
    mutationFn: (newMember: any) => {
      return fetch("http://localhost:8000/api/team", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("safina_token")}`
        },
        body: JSON.stringify({
          last_name: newMember.lastName,
          first_name: newMember.firstName,
          project_id: newMember.projectId,
          login: newMember.login,
          password: newMember.password
        }),
      }).then(res => res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team"] });
      setFormData({ lastName: "", firstName: "", projectId: "", login: "", password: "" });
      toast.success("Участник добавлен");
    },
    onError: () => toast.error("Ошибка при добавлении")
  });

  const handleAddMember = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.projectId) {
      mutation.mutate(formData);
    } else {
      toast.error("Выберите проект");
    }
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
              <Label>Проект</Label>
              <Select
                value={formData.projectId}
                onValueChange={(val) => setFormData({ ...formData, projectId: val })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Выберите проект" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((p: Project) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
                    Проект
                  </th>
                  <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Логин
                  </th>
                  <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Статус
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {team.map((member: TeamMember) => {
                  const project = projects.find((p) => p.id === member.projectId);
                  return (
                    <tr key={member.id} className="hover:bg-muted/10 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                            {member.lastName[0]}{member.firstName[0]}
                          </div>
                          <div>
                            <p className="font-display font-semibold text-sm">
                              {member.lastName} {member.firstName}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm font-medium inline-flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                          {project?.name || "—"}
                        </span>
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
