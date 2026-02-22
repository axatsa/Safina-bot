import { ClipboardList, FolderOpen, Users, LogOut, Archive } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useNavigate } from "react-router-dom";
import { store } from "@/lib/store";

const navItems = [
  { title: "Заявки", url: "/dashboard", icon: ClipboardList },
  { title: "Архив", url: "/dashboard/archive", icon: Archive },
  { title: "Проекты", url: "/dashboard/projects", icon: FolderOpen },
  { title: "Команда", url: "/dashboard/team", icon: Users },
];

const AppSidebar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    store.logout();
    navigate("/");
  };

  return (
    <aside className="w-60 min-h-screen bg-sidebar flex flex-col border-r border-sidebar-border shrink-0">
      <div className="p-5 border-b border-sidebar-border">
        <h2 className="font-display text-lg font-bold text-sidebar-primary-foreground tracking-tight">
          Thompson Finance
        </h2>
        <p className="text-xs text-sidebar-muted mt-0.5">Управление расходами</p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.url}
            to={item.url}
            end={item.url === "/dashboard"}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground hover:bg-sidebar-accent transition-colors"
            activeClassName="bg-sidebar-accent text-sidebar-primary font-medium"
          >
            <item.icon className="w-4 h-4" />
            <span>{item.title}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-sidebar-border">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground hover:bg-sidebar-accent transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Выход</span>
        </button>
      </div>
    </aside>
  );
};

export default AppSidebar;
