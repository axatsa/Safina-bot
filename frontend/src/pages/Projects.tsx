import { useState } from "react";
import { store } from "@/lib/store";
import { Project, Branch } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
    Plus, 
    FolderKanban, 
    Loader2, 
    Trash2, 
    Calendar, 
    Users, 
    X, 
    FileText, 
    FolderOpen,
    GitBranch,
    Rocket,
    Building2
} from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { format } from "date-fns";
import { Checkbox } from "@/components/ui/checkbox";
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
    { id: "drujba", label: "ЛС (Дружба)" },
    { id: "management", label: "Management" },
    { id: "school", label: "School" },
    { id: "refund", label: "Заявление на возврат" },
];

interface ProjectsProps {
    category: "startup" | "corporate";
}

const Projects = ({ category }: ProjectsProps) => {
    const queryClient = useQueryClient();
    const [formData, setFormData] = useState({
        name: "",
        code: "",
    });

    const isCorporate = category === "corporate";
    const title = isCorporate ? "Проекты" : "Start Ups";
    const subtitle = isCorporate ? "Корпоративные проекты с филиалами" : "Плоские проекты без структуры";
    const Icon = isCorporate ? Building2 : Rocket;

    const { data: projects = [], isLoading: isProjectsLoading } = useQuery({
        queryKey: ["projects", category],
        queryFn: () => store.getProjects(category),
    });

    // Auto-sync activeProject when projects list is refetched
    useEffect(() => {
        if (activeProject && projects.length > 0) {
            const updated = projects.find(p => p.id === activeProject.id);
            if (updated) {
                setActiveProject(updated);
            }
        }
    }, [projects]);

    const mutation = useMutation({
        mutationFn: (newProject: { name: string; code: string; category: string }) => store.createProject(newProject),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects", category] });
            setFormData({ name: "", code: "" });
            toast.success("Создано успешно");
        },
        onError: () => toast.error("Ошибка при создании")
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => store.deleteProject(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects", category] });
            toast.success("Удалено");
        },
        onError: () => toast.error("Ошибка при удалении")
    });

    const [memberDialogOpen, setMemberDialogOpen] = useState(false);
    const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
    const [branchDialogOpen, setBranchDialogOpen] = useState(false);
    const [activeProject, setActiveProject] = useState<Project | null>(null);
    const [pendingTemplates, setPendingTemplates] = useState<string[] | null>(null);
    const [newBranchName, setNewBranchName] = useState("");

    const { data: team = [] } = useQuery({
        queryKey: ["team"],
        queryFn: () => store.getTeam()
    });

    const { data: currentBranches = [], isLoading: isBranchesLoading, refetch: refetchBranches } = useQuery({
        queryKey: ["branches", activeProject?.id],
        queryFn: () => activeProject ? store.getBranches(activeProject.id) : Promise.resolve([]),
        enabled: !!activeProject && isCorporate
    });

    const createBranchMutation = useMutation({
        mutationFn: (name: string) => store.createBranch(activeProject!.id, { name }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["branches", activeProject?.id] });
            queryClient.invalidateQueries({ queryKey: ["projects", category] });
            setNewBranchName("");
            toast.success("Филиал добавлен");
            refetchBranches();
        },
        onError: (error: any) => {
            console.error("Branch create error:", error);
            toast.error(error.message || "Ошибка при создании филиала");
        }
    });

    const deleteBranchMutation = useMutation({
        mutationFn: (id: string) => store.deleteBranch(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["branches", activeProject?.id] });
            queryClient.invalidateQueries({ queryKey: ["projects", category] });
            toast.success("Филиал удален");
            refetchBranches();
        },
        onError: (error: any) => {
            console.error("Branch delete error:", error);
            toast.error(error.message || "Ошибка при удалении филиала");
        }
    });
    });

    const addMemberMutation = useMutation({
        mutationFn: ({ projectId, memberId }: { projectId: string; memberId: string }) =>
            store.addProjectMember(projectId, memberId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects", category] });
            queryClient.invalidateQueries({ queryKey: ["team"] });
            toast.success("Участник добавлен");
        }
    });

    const removeMemberMutation = useMutation({
        mutationFn: ({ projectId, memberId }: { projectId: string; memberId: string }) =>
            store.removeProjectMember(projectId, memberId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects", category] });
            queryClient.invalidateQueries({ queryKey: ["team"] });
            toast.success("Участник исключен");
        }
    });

    const updateTemplatesMutation = useMutation({
        mutationFn: ({ projectId, templates }: { projectId: string; templates: string[] }) =>
            store.updateProjectTemplates(projectId, templates),
        onSuccess: (updatedProject) => {
            queryClient.invalidateQueries({ queryKey: ["projects", category] });
            if (activeProject && updatedProject.id === activeProject.id) {
                setActiveProject(updatedProject);
            }
            toast.success("Шаблоны обновлены");
            setTemplateDialogOpen(false);
            setPendingTemplates(null);
        }
    });

    const handleTemplateToggle = (templateId: string) => {
        if (pendingTemplates === null) return;
        const updated = pendingTemplates.includes(templateId)
            ? pendingTemplates.filter(id => id !== templateId)
            : [...pendingTemplates, templateId];
        setPendingTemplates(updated);
    };

    const handleSaveTemplates = () => {
        if (!activeProject || pendingTemplates === null) return;
        updateTemplatesMutation.mutate({
            projectId: activeProject.id,
            templates: pendingTemplates
        });
    };

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
        mutation.mutate({ ...formData, category });
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
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                    <Icon className="w-6 h-6" />
                </div>
                <div>
                    <h1 className="text-2xl font-display font-bold text-foreground">{title}</h1>
                    <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
                <div className="xl:col-span-1 glass-card p-6 rounded-2xl border space-y-6 h-fit">
                    <h2 className="font-display font-bold text-lg flex items-center gap-2">
                        <Plus className="w-5 h-5 text-primary" />
                        Создать
                    </h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Название</Label>
                            <Input
                                id="name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="напр. Thompson Marketing"
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="code">Код (префикс ID)</Label>
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
                        {projects.length === 0 ? (
                            <div className="py-20">
                                <EmptyState 
                                    icon={FolderOpen}
                                    title="Пусто"
                                    subtitle="Нет созданных элементов в этой категории"
                                />
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead>
                                        <tr className="border-b bg-muted/30">
                                            <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                                                Название
                                            </th>
                                            <th className="px-6 py-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                                                Код
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
                                                        <p className="font-display font-semibold text-sm">
                                                            {project.name}
                                                        </p>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <code className="text-xs bg-muted px-2 py-1 rounded font-bold">
                                                        {project.code}
                                                    </code>
                                                </td>
                                                <td className="px-6 py-4 text-right space-x-1">
                                                    {isCorporate && (
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            className="text-muted-foreground hover:text-blue-600"
                                                            onClick={() => {
                                                                setActiveProject(project);
                                                                setBranchDialogOpen(true);
                                                            }}
                                                            title="Филиалы"
                                                        >
                                                            <GitBranch className="w-4 h-4" />
                                                        </Button>
                                                    )}
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
                                                        className="text-muted-foreground hover:text-indigo-600 transition-colors"
                                                        onClick={() => {
                                                            setActiveProject(project);
                                                            setPendingTemplates(project.templates || []);
                                                            setTemplateDialogOpen(true);
                                                        }}
                                                        title="Шаблоны бланков"
                                                    >
                                                        <FileText className="w-4 h-4" />
                                                    </Button>
                                                    
                                                    <AlertDialog>
                                                        <AlertDialogTrigger asChild>
                                                            <Button
                                                                variant="ghost"
                                                                size="icon"
                                                                className="text-muted-foreground hover:text-red-600 transition-colors"
                                                                title="Удалить"
                                                            >
                                                                <Trash2 className="w-4 h-4" />
                                                            </Button>
                                                        </AlertDialogTrigger>
                                                        <AlertDialogContent>
                                                            <AlertDialogHeader>
                                                                <AlertDialogTitle>Удалить?</AlertDialogTitle>
                                                                <AlertDialogDescription>
                                                                    Вы уверены, что хотите удалить этот проект?
                                                                </AlertDialogDescription>
                                                            </AlertDialogHeader>
                                                            <AlertDialogFooter>
                                                                <AlertDialogCancel>Отмена</AlertDialogCancel>
                                                                <AlertDialogAction 
                                                                    onClick={() => deleteMutation.mutate(project.id)}
                                                                    className="bg-red-600 hover:bg-red-700"
                                                                >
                                                                    Удалить
                                                                </AlertDialogAction>
                                                            </AlertDialogFooter>
                                                        </AlertDialogContent>
                                                    </AlertDialog>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Branches Dialog */}
            <Dialog open={branchDialogOpen} onOpenChange={setBranchDialogOpen}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>Филиалы: {activeProject?.name}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-6 pt-4">
                        <div className="flex gap-2">
                            <Input 
                                placeholder="Название филиала" 
                                value={newBranchName}
                                onChange={(e) => setNewBranchName(e.target.value)}
                            />
                            <Button 
                                onClick={() => createBranchMutation.mutate(newBranchName)}
                                disabled={!newBranchName || createBranchMutation.isPending}
                            >
                                <Plus className="w-4 h-4" />
                            </Button>
                        </div>
                        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                            {isBranchesLoading ? (
                                <div className="flex justify-center py-10">
                                    <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : (
                                <>
                                    {currentBranches.map((branch: any) => (
                                        <div key={branch.id} className="flex items-center justify-between bg-muted/40 p-3 rounded-lg border">
                                            <div className="flex flex-col">
                                                <p className="text-sm font-bold text-slate-900">
                                                    {branch.name || branch.branch_name || "Без названия"}
                                                </p>
                                                <code className="text-[10px] font-mono text-slate-500 uppercase">
                                                    {branch.code || "---"}
                                                </code>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 text-slate-400 hover:text-red-500 transition-colors"
                                                onClick={() => {
                                                    console.log("Deleting branch:", branch.id);
                                                    deleteBranchMutation.mutate(branch.id);
                                                }}
                                                disabled={deleteBranchMutation.isPending}
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </Button>
                                        </div>
                                    ))}
                                    {currentBranches.length === 0 && (
                                        <p className="text-sm text-center text-muted-foreground py-10 italic">
                                            Нет созданных филиалов
                                        </p>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </DialogContent>
            </Dialog>

            <Dialog open={memberDialogOpen} onOpenChange={setMemberDialogOpen}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>Участники: {activeProject?.name}</DialogTitle>
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
                            </div>
                        </div>

                        <div className="space-y-3 pt-2 border-t">
                            <Label className="text-sm font-medium">Добавить участника</Label>
                            <Select onValueChange={(value) => {
                                if (activeProject) {
                                    addMemberMutation.mutate({
                                        projectId: activeProject.id,
                                        memberId: value
                                    });
                                }
                            }}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Выберите сотрудника..." />
                                </SelectTrigger>
                                <SelectContent>
                                    {availableMembers.map((m) => (
                                        <SelectItem key={m.id} value={m.id}>
                                            {m.lastName} {m.firstName}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>

            <Dialog 
                open={templateDialogOpen} 
                onOpenChange={(open) => {
                    setTemplateDialogOpen(open);
                    if (!open) setPendingTemplates(null);
                }}
            >
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>Шаблоны: {activeProject?.name}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 pt-4">
                        <div className="grid grid-cols-1 gap-2">
                            {AVAILABLE_TEMPLATES.map((tpl: any) => (
                                <div key={tpl.id} className="flex items-center space-x-3 p-3 rounded-lg border bg-muted/20">
                                    <Checkbox 
                                        id={`tpl-${tpl.id}`}
                                        checked={(pendingTemplates ?? []).includes(tpl.id)}
                                        onCheckedChange={() => handleTemplateToggle(tpl.id)}
                                    />
                                    <Label htmlFor={`tpl-${tpl.id}`} className="text-sm cursor-pointer flex-1">
                                        {tpl.label}
                                    </Label>
                                </div>
                            ))}
                        </div>
                        <Button
                            onClick={handleSaveTemplates}
                            disabled={updateTemplatesMutation.isPending}
                            className="w-full mt-4"
                        >
                            Сохранить
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default Projects;
