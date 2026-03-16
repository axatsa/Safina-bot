import { Navigate, Outlet } from "react-router-dom";
import AppSidebar from "./AppSidebar";
import { store } from "@/lib/store";

const AppLayout = () => {
  const token = localStorage.getItem("safina_token");
  const hasAccess = store.hasWebAccess();

  if (!token || !hasAccess) {
    if (!token) {
      localStorage.removeItem("safina_token");
      localStorage.removeItem("safina_role");
      localStorage.removeItem("safina_user");
      localStorage.removeItem("safina_projectId");
    }
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-screen w-full">
      <AppSidebar />
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
