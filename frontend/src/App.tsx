import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import AppLayout from "./components/AppLayout";
import Applications from "./pages/Applications";
import Projects from "./pages/Projects";
import Team from "./pages/Team";
import ArchivePage from "./pages/Archive";
import ExpenseDetail from "./pages/ExpenseDetail";
import SubmitExpense from "./pages/SubmitExpense";
import Statistics from "./pages/Statistics";
import Refunds from "./pages/Refunds";
import Approvals from "./pages/Approvals";
import AdminApprovals from "./pages/AdminApprovals";
import BlankForm from "./pages/BlankForm";
import NotFound from "./pages/NotFound";
import { SSEProvider } from "./lib/contexts/SSEContext";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

import { store } from "./lib/store";
import { Navigate } from "react-router-dom";

const DashboardIndex = () => {
  if (store.isFarrukh()) {
    return <Navigate to="/dashboard/approvals" replace />;
  }
  if (store.isSafina()) {
    return <Navigate to="/dashboard/admin-approvals" replace />;
  }
  return <Navigate to="/dashboard/applications" replace />;
};

import ErrorBoundary from "./components/ErrorBoundary";

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <SSEProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Login />} />
              <Route path="/dashboard" element={<AppLayout />}>
                <Route index element={<DashboardIndex />} />
                <Route path="archive" element={<ArchivePage />} />
                <Route path="refunds" element={<Refunds />} />
                <Route path="projects" element={<Projects />} />
                <Route path="team" element={<Team />} />
                <Route path="statistics" element={<Statistics />} />
                <Route path="approvals" element={<Approvals />} />
                <Route path="admin-approvals" element={<AdminApprovals />} />
                <Route path="expense/:id" element={<ExpenseDetail />} />
              </Route>
              <Route path="/submit" element={<SubmitExpense />} />
              <Route path="/blank" element={<BlankForm />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </SSEProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
