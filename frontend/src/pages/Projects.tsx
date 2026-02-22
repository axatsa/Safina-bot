import { useState } from "react";
import { store } from "@/lib/store";
import { Project } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Layout, Loader2 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const Projects = () => {
  const queryClient = useQueryClient();
  const [newName, setNewName] = useState("");
  const [newCode, setNewCode] = useState("");

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => store.getProjects(),
  });

  const mutation = useMutation({
    mutationFn: (newProject: { name: string; code: string }) => {
      return fetch("http://localhost:8000/api/projects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("safina_token")}`
        },
        body: JSON.stringify(newProject),
      }).then(res => res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setNewName("");
      setNewCode("");
      toast.success("Проект добавлен");
    },
  });

  const handleAddProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (newName && newCode) {
      mutation.mutate({ name: newName, code: newCode.toUpperCase() });
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8 animate-slide-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Проекты</h1>
          <p className="text-sm text-muted-foreground mt-1">Управление списком активных проектов</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 glass-card p-6 rounded-2xl border space-y-6 h-fit">
          <h2 className="font-display font-bold text-lg flex items-center gap-2">
            <Plus className="w-5 h-5 text-primary" />
            Новый проект
          </h2>
          <form onSubmit={handleAddProject} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Название</Label>
              <Input
                id="name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Напр. Tashkent Office"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="code">Код проекта (3 буквы)</Label>
              <Input
                id="code"
                value={newCode}
                onChange={(e) => setNewCode(e.target.value.toUpperCase())}
                placeholder="Напр. TST"
                maxLength={3}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Добавить проект
            </Button>
          </form>
        </div>

        <div className="md:col-span-2 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {projects.map((project: Project) => (
              <div key={project.id} className="glass-card p-5 rounded-2xl border group hover:border-primary/50 transition-all duration-300">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="inline-flex items-center justify-center px-1.5 py-0.5 rounded-md bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-wider mb-2">
                      {project.code}
                    </div>
                    <h3 className="font-display font-bold text-foreground text-lg group-hover:text-primary transition-colors">
                      {project.name}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      Создан: {new Date(project.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center">
                    <Layout className="w-5 h-5 text-muted-foreground" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Projects;
