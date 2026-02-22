import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const Login = () => {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    const success = await store.login(login, password);

    setIsLoading(false);
    if (success) {
      toast.success("Вход выполнен");
      navigate("/dashboard");
    } else {
      toast.error("Неверный логин или пароль");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 animate-fade-in">
      <div className="w-full max-w-md space-y-8 glass-card p-8 rounded-2xl border">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary text-primary-foreground font-display font-bold text-xl mb-4">
            T
          </div>
          <h1 className="text-2xl font-display font-bold tracking-tight">Thompson Finance Admin</h1>
          <p className="text-muted-foreground text-sm">Войдите в систему для управления расходами</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="login">Логин</Label>
            <Input
              id="login"
              type="text"
              placeholder="Введите логин"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              required
              className="rounded-xl"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Пароль</Label>
            <Input
              id="password"
              type="password"
              placeholder="Введите пароль"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="rounded-xl"
            />
          </div>

          <Button type="submit" className="w-full rounded-xl py-6 font-semibold" disabled={isLoading}>
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Войти
          </Button>
        </form>

        <div className="text-center">
          <p className="text-xs text-muted-foreground italic">
            Для демонстрации: safina / admin123
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
