import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import MyPriorities from "./pages/MyPriorities";
import Dashboard from "./pages/Index";
import DealDetail from "./pages/DealDetail";
import Manager from "./pages/Manager";

import Analytics from "./pages/Analytics";
import Premises from "./pages/Premises";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<MyPriorities />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/deal/:id" element={<DealDetail />} />
            <Route path="/manager" element={<Manager />} />
            
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/premissas" element={<Premises />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
