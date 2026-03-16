import { useState } from "react";
import { store } from "@/lib/store";
import { Project } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, FolderKanban, Loader2, Trash2, Calendar, Users, UserPlus, X } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { format } from "date-fns";

const Projects = () => {
    const queryClient = useQueryClient();
    const [formData, setFormData] = useState({
        name: "",
        code: "",
    });

    const { data: projects = [], isLoading: isProjectsLoading } = useQuery({
        queryKey: ["projects"],
        queryFn: () => store.getProjects(),
    });

    const mutation = useMutation({
        mutationFn: (newProject: { name: string; code: string }) => store.createProject(newProject),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
            setFormData({ name: "", code: "" });
            toast.success("Проект успешно создан");
        },
        onError: () => toast.error("Ошибка при создании проекта")
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => store.deleteProject(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
            toast.success("Проект удален");
        },
        onError: () => toast.error("Ошибка при удалении")
    });

    const handleDeleteProject = (id: string) => {
        if (confirm("Вы уверены, что хотите удалить этот проект? Это может повлиять на связанные заявки и участников.")) {
            deleteMutation.mutate(id);
        }
    };

    const [memberDialogOpen, setMemberDialogOpen] = useState(false);
    const [activeProject, setActiveProject] = useState<Project | null>(null);

    const { data: team = [] } = useQuery({
        queryKey: ["team"],
        queryFn: () => store.getTeam()
    });

    const addMemberMutation = useMutation({
        mutationFn: ({ projectId, memberId }: { projectId: string; memberId: string }) =>
            store.addProjectMember(projectId, memberId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
            queryClient.invalidateQueries({ queryKey: ["team"] });
            toast.success("Участник добавлен");
        }
    });

    const removeMemberMutation = useMutation({
        mutationFn: ({ projectId, memberId }: { projectId: string; memberId: string }) =>
            store.removeProjectMember(projectId, memberId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
            queryClient.invalidateQueries({ queryKey: ["team"] });
            toast.success("Участник исключен");
        }
    });

    const projectMembers = activeProject
        ? projects.find((p: Project) => p.id === activeProject.id)?.members || []
        : [];

    const availableMembers = team.filter(
        (m) => !projectMembers.some((pm: any) => pm.id === m.id)
    );

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name || !formData.code) {
            toast.error("Заполните все поля");
            return;
        }
        mutation.mutate(formData);
    };

    if (isProjectsLoading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="p-6 space-y-8 animate-slide-in">
            <div>
                <h1 className="text-2xl font-display font-bold text-foreground">Проекты</h1>
                <p className="text-sm text-muted-foreground mt-1">Управление списком активных проектов</p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
                <div className="xl:col-span-1 glass-card p-6 rounded-2xl border space-y-6 h-fit">
                    <h2 className="font-display font-bold text-lg flex items-center gap-2">
                        <Plus className="w-5 h-5 text-primary" />
                        Новый проект
                    </h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Название проекта</Label>
                            <Input
                                id="name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="напр. Thompson Marketing"
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="code">Код проекта (префикс ID)</Label>
                            <Input
                                id="code"
                                value={formData.code}
                                onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                                placeholder="напр. TM"
                                required
                                maxLength={10}
                            />
                        </div>
                        <Button type="submit" className="w-full" disabled={mutation.isPending}>
                            {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                            Создать
                        </Button>
                    </form>
                </div>

                <div className="xl:col-span-3">
                    <div className="glass-card rounded-2xl border overflow-hidden">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b bg-muted/30">
                                    <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                                        Название
                                    </th>
                                    <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                                        Код
                                    </th>
                                    <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                                        Дата создания
                                    </th>
                                    <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider text-right">
                                        Действия
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {projects.map((project: Project) => (
                                    <tr key={project.id} className="hover:bg-muted/10 transition-colors group">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                                                    <FolderKanban className="w-4 h-4" />
                                                </div>
                                                <div>
                                                    <p className="font-display font-semibold text-sm">
                                                        {project.name}
                                                    </p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <code className="text-xs bg-muted px-2 py-1 rounded font-bold">
                                                {project.code}
                                            </code>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-muted-foreground">
                                            <div className="flex items-center gap-2">
                                                <Calendar className="w-3 h-3" />
                                                {project.createdAt ? format(new Date(project.createdAt), "dd.MM.yyyy") : "—"}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right space-x-2">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="text-muted-foreground hover:text-primary transition-colors"
                                                onClick={() => {
                                                    setActiveProject(project);
                                                    setMemberDialogOpen(true);
                                                }}
                                                title="Участники проекта"
                                            >
                                                <Users className="w-4 h-4" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="text-muted-foreground hover:text-red-600 transition-colors"
                                                onClick={() => handleDeleteProject(project.id)}
                                                title="Удалить проект"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                                {projects.length === 0 && (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-8 text-center text-muted-foreground">
                                            Проектов пока нет
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <Dialog open={memberDialogOpen} onOpenChange={setMemberDialogOpen}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>Участники проекта: {activeProject?.name}</DialogTitle>
                    </DialogHeader>

                    <div className="space-y-6 pt-4">
                        <div className="space-y-4">
                            <Label className="text-sm font-medium">Текущие участники ({projectMembers.length})</Label>
                            <div className="space-y-2 max-h-[200px] overflow-y-auto pr-2">
                                {projectMembers.map((member: any) => (
                                    <div key={member.id} className="flex items-center justify-between bg-muted/40 p-2 rounded-lg border">
                                        <div>
                                            <p className="text-sm font-medium">{member.lastName} {member.firstName}</p>
                                            <p className="text-xs text-muted-foreground">{member.position || "Сотрудник"}</p>
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-8 w-8 text-muted-foreground hover:text-red-500"
                                            onClick={() => removeMemberMutation.mutate({
                                                projectId: activeProject!.id,
                                                memberId: member.id
                                            })}
                                            disabled={removeMemberMutation.isPending}
                                        >
                                            <X className="w-4 h-4" />
                                        </Button>
                                    </div>
                                ))}
                                {projectMembers.length === 0 && (
                                    <p className="text-sm text-muted-foreground italic text-center py-4">
                                        В проекте пока нет участников
                                    </p>
                                )}
                            </div>
                        </div>

                        <div className="space-y-3 pt-2 border-t">
                            <Label className="text-sm font-medium">Добавить участника</Label>
                            <div className="flex gap-2">
                                <Select onValueChange={(value) => {
                                    if (activeProject) {
                                        addMemberMutation.mutate({
                                            projectId: activeProject.id,
                                            memberId: value
                                        });
                                    }
                                }}>
                                    <SelectTrigger className="flex-1">
                                        <SelectValue placeholder="Выберите сотрудника..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {availableMembers.map((m) => (
                                            <SelectItem key={m.id} value={m.id}>
                                                {m.lastName} {m.firstName} ({m.position || "чел"})
                                            </SelectItem>
                                        ))}
                                        {availableMembers.length === 0 && (
                                            <div className="p-2 text-xs text-center text-muted-foreground">
                                                Нет доступных сотрудников
                                            </div>
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default Projects;
