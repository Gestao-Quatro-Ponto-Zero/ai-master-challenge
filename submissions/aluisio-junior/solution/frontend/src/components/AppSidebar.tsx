import {
  LayoutDashboard, MessageSquare, LogOut, ShieldAlert, Sparkles,
  Kanban, Lightbulb, MessageCircle, Settings,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useAuth } from "@/contexts/AuthContext";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarFooter, useSidebar,
} from "@/components/ui/sidebar";
import { Activity } from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Risco de Churn", url: "/churn-risk", icon: ShieldAlert },
  { title: "Insights", url: "/insights", icon: Lightbulb },
  { title: "Recomendações", url: "/recommendations", icon: Sparkles },
  { title: "Kanban", url: "/kanban", icon: Kanban },
  { title: "WhatsApp", url: "/whatsapp", icon: MessageCircle },
  { title: "Chat IA", url: "/chat", icon: MessageSquare },
  { title: "Configurações", url: "/settings", icon: Settings },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const { user, logout } = useAuth();

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        <div className="flex items-center gap-2 px-4 py-5">
          <Activity className="h-6 w-6 text-sidebar-primary shrink-0" />
          {!collapsed && (
            <span className="font-bold text-sm text-sidebar-foreground tracking-tight">
              Churn Intelligence
            </span>
          )}
        </div>

        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end={item.url === "/"}
                      className="hover:bg-sidebar-accent/50"
                      activeClassName="bg-sidebar-accent text-sidebar-primary font-medium"
                    >
                      <item.icon className="mr-2 h-4 w-4 shrink-0" />
                      {!collapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-3">
        {!collapsed && user && (
          <div className="text-xs text-sidebar-muted-foreground mb-2 px-2 truncate">
            {user.email}
            <span className="ml-1 text-sidebar-primary capitalize">({user.role})</span>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start text-sidebar-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent"
          onClick={() => logout()}
        >
          <LogOut className="h-4 w-4 mr-2 shrink-0" />
          {!collapsed && "Sair"}
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}
