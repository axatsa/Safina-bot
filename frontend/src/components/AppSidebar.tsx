import { 
  ClipboardList, 
  FolderOpen, 
  Users, 
  LogOut, 
  Archive, 
  Send, 
  BarChart, 
  RotateCcw, 
  ShieldCheck, 
  HelpCircle 
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";

const AppSidebar = () => {
  const navigate = useNavigate();
  const isAdmin = store.isAdmin();
  const userName = store.getUser();

  const handleLogout = () => {
    store.logout();
    navigate("/");
  };

  const menuItems = [
    { title: "Заявки", url: "/dashboard/applications", icon: ClipboardList, show: true },
    { title: "Новая заявка", url: "/submit", icon: Send, show: false },
    { 
      title: "Очередь обработки", 
      url: "/dashboard/admin-approvals", 
      icon: ShieldCheck, 
      show: true 
    },
    { title: "Возвраты", url: "/dashboard/refunds", icon: RotateCcw, show: true },
    { title: "Статистика", url: "/dashboard/statistics", icon: BarChart, show: true },
    { title: "Отчёты", url: "/dashboard/archive", icon: Archive, show: true },
    { title: "Проекты", url: "/dashboard/projects", icon: FolderOpen, show: true },
    { title: "Команда", url: "/dashboard/team", icon: Users, show: true },
    { title: "Инструкция / FAQ", url: "/dashboard/faq", icon: HelpCircle, show: true },
  ];

  return (
    <aside className="w-64 min-h-screen bg-sidebar flex flex-col border-r border-sidebar-border shrink-0">
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
            <img src="/logo.png" alt="Thompson Finance" className="w-6 h-6 object-contain" />
          </div>
          <h2 className="font-display text-lg font-extrabold text-sidebar-primary-foreground tracking-tight whitespace-nowrap">
            Thompson Finance
          </h2>
        </div>
        <p className="text-[10px] text-sidebar-muted uppercase font-bold tracking-widest mt-2 opacity-60">Управление расходами</p>
      </div>

      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {menuItems.filter(item => item.show).map((item) => (
          <NavLink
            key={item.url}
            to={item.url}
            end={item.url === "/dashboard"}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-sidebar-foreground hover:bg-sidebar-accent transition-all duration-200 group"
            activeClassName="bg-sidebar-accent text-sidebar-primary font-bold shadow-sm"
          >
            <item.icon className="w-4 h-4 group-hover:scale-110 transition-transform" />
            <span>{item.title}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-sidebar-border space-y-4">
        {userName && (
          <div className="px-3 py-3 rounded-xl bg-muted/30 border border-sidebar-border/30">
            <p className="text-[9px] uppercase font-bold text-sidebar-muted mb-1 tracking-tighter">Аккаунт</p>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-bold text-primary">
                {userName.charAt(0).toUpperCase()}
              </div>
              <span className="text-xs font-semibold text-sidebar-foreground truncate">{userName}</span>
            </div>
          </div>
        )}

        <div className="flex items-center gap-2">
          <button
            onClick={handleLogout}
            className="flex-1 flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors font-medium"
          >
            <LogOut className="w-4 h-4" />
            <span>Выход</span>
          </button>
          <div className="px-2 py-1 rounded bg-muted text-[8px] font-mono font-bold text-muted-foreground whitespace-nowrap">
            v3.0-CLEAN
          </div>
        </div>
      </div>
    </aside>
  );
};

export default AppSidebar;
