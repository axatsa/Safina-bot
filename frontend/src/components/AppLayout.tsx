import { Navigate, Outlet } from "react-router-dom";
import AppSidebar from "./AppSidebar";
import { store } from "@/lib/store";

const AppLayout = () => {
  const isValidUser = store.hasWebAccess();

  if (!isValidUser) {
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
