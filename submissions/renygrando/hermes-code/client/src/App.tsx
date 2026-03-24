import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "@/context/auth";

import Login from "./pages/login";
import Register from "./pages/register";
import Dashboard from "./pages/dashboard";
import TicketsList from "./pages/tickets/index";
import TicketDetail from "./pages/tickets/[id]";
import Analytics from "./pages/analytics";
import KnowledgeBase from "./pages/knowledge-base";
import Settings from "./pages/settings";
import MeusChamados from "./pages/meus-chamados";
import AbrirChamado from "./pages/abrir-chamado";
import ChamadoChat from "./pages/chamado/[id]";
import AdminDashboard from "./pages/admin/index";
import AdminChamados from "./pages/admin/chamados";
import NotFound from "@/pages/not-found";

import { useEffect } from "react";

function Redirect({ to }: { to: string }) {
  const [, setLocation] = useLocation();
  useEffect(() => { setLocation(to); }, [to]);
  return null;
}

function AuthGuard({ children, adminOnly = false }: { children: React.ReactNode; adminOnly?: boolean }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin w-8 h-8 border-4 border-secondary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!user) return <Redirect to="/entrar" />;
  if (adminOnly && user.role !== "admin") return <Redirect to="/meus-chamados" />;
  return <>{children}</>;
}

function Router() {
  return (
    <Switch>
      <Route path="/entrar" component={Login} />
      <Route path="/cadastro" component={Register} />

      <Route path="/meus-chamados">
        <AuthGuard><MeusChamados /></AuthGuard>
      </Route>
      <Route path="/abrir-chamado">
        <AuthGuard><AbrirChamado /></AuthGuard>
      </Route>
      <Route path="/chamado/:id">
        <AuthGuard><ChamadoChat /></AuthGuard>
      </Route>

      <Route path="/admin">
        <AuthGuard adminOnly><AdminDashboard /></AuthGuard>
      </Route>
      <Route path="/admin/chamados">
        <AuthGuard adminOnly><AdminChamados /></AuthGuard>
      </Route>
      <Route path="/tickets/:id">
        <AuthGuard adminOnly><TicketDetail /></AuthGuard>
      </Route>
      <Route path="/analytics">
        <AuthGuard adminOnly><Analytics /></AuthGuard>
      </Route>
      <Route path="/base-conhecimento">
        <AuthGuard><KnowledgeBase /></AuthGuard>
      </Route>
      <Route path="/configuracoes">
        <AuthGuard adminOnly><Settings /></AuthGuard>
      </Route>

      <Route path="/">
        <AuthRedirect />
      </Route>

      <Route component={NotFound} />
    </Switch>
  );
}

function AuthRedirect() {
  const { user, isLoading } = useAuth();
  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="animate-spin w-8 h-8 border-4 border-secondary border-t-transparent rounded-full"></div>
    </div>
  );
  if (!user) return <Redirect to="/entrar" />;
  if (user.role === "admin") return <Redirect to="/admin" />;
  return <Redirect to="/meus-chamados" />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <Toaster />
          <Router />
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
