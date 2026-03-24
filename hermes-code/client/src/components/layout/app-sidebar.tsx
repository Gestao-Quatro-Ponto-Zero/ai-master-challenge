import { Link, useLocation } from "wouter";
import { 
  LayoutDashboard, 
  Ticket,
  MessageSquarePlus,
  Inbox,
  BarChart3, 
  BookOpen, 
  Settings, 
  ShieldCheck,
  LogOut,
  Users
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
  SidebarHeader
} from "@/components/ui/sidebar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/context/auth";

const adminNavItems = [
  { title: "Painel", url: "/admin", icon: LayoutDashboard },
  { title: "Chamados", url: "/admin/chamados", icon: Ticket },
  { title: "Analytics", url: "/analytics", icon: BarChart3 },
  { title: "Base de Conhecimento", url: "/base-conhecimento", icon: BookOpen },
];

const userNavItems = [
  { title: "Meus Chamados", url: "/meus-chamados", icon: Inbox },
  { title: "Abrir Chamado", url: "/abrir-chamado", icon: MessageSquarePlus },
  { title: "Base de Conhecimento", url: "/base-conhecimento", icon: BookOpen },
];

const adminSettingsItems = [
  { title: "Configurações", url: "/configuracoes", icon: Settings },
];

export function AppSidebar() {
  const [location] = useLocation();
  const { user, logout } = useAuth();

  const isAdmin = user?.role === "admin";
  const navItems = isAdmin ? adminNavItems : userNavItems;
  const initials = user?.name ? user.name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() : "U";

  return (
    <Sidebar className="border-r border-secondary/20 bg-primary">
      <SidebarHeader className="p-4 border-b border-secondary/20">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-md bg-secondary flex items-center justify-center shadow-lg shadow-black/20">
            <ShieldCheck className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="font-display font-bold text-sidebar-foreground text-lg leading-tight tracking-wide" data-testid="text-app-name">HERMES</h2>
            <p className="text-[10px] text-secondary uppercase tracking-[0.2em]">Suporte IA</p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="pt-6">
        <SidebarGroup>
          <SidebarGroupLabel className="text-sidebar-foreground/50 uppercase text-[10px] tracking-widest font-semibold mb-2">
            {isAdmin ? "Administração" : "Suporte"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const isActive = location === item.url || (item.url !== "/" && item.url !== "/meus-chamados" && item.url !== "/abrir-chamado" && location.startsWith(item.url)) || location === item.url;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton 
                      asChild 
                      isActive={isActive}
                      className={`
                        transition-all duration-300 ease-out mb-1 py-5
                        ${isActive 
                          ? 'bg-secondary/15 text-secondary' 
                          : 'text-sidebar-foreground/70'}
                      `}
                    >
                      <Link href={item.url} className="flex items-center gap-3 px-3" data-testid={`link-nav-${item.title.toLowerCase().replace(/\s+/g, '-')}`}>
                        <item.icon className={`w-4 h-4 ${isActive ? 'text-secondary' : ''}`} />
                        <span className="font-medium">{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {isAdmin && (
          <SidebarGroup className="mt-8">
            <SidebarGroupLabel className="text-sidebar-foreground/50 uppercase text-[10px] tracking-widest font-semibold mb-2">Sistema</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {adminSettingsItems.map((item) => {
                  const isActive = location === item.url;
                  return (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton 
                        asChild 
                        isActive={isActive}
                        className={`
                          transition-all duration-300 ease-out py-5
                          ${isActive 
                            ? 'bg-secondary/15 text-secondary' 
                            : 'text-sidebar-foreground/70'}
                        `}
                      >
                        <Link href={item.url} className="flex items-center gap-3 px-3" data-testid={`link-nav-${item.title.toLowerCase()}`}>
                          <item.icon className="w-4 h-4" />
                          <span className="font-medium">{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter className="border-t border-secondary/20 p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton 
              className="h-auto py-2 w-full justify-start text-sidebar-foreground/80 cursor-pointer"
              onClick={logout}
              data-testid="button-logout"
            >
              <Avatar className="w-8 h-8 border border-secondary/30 mr-2">
                <AvatarFallback className="bg-primary-foreground text-primary font-display font-bold text-xs">{initials}</AvatarFallback>
              </Avatar>
              <div className="flex flex-col flex-1 text-left min-w-0">
                <span className="text-sm font-semibold leading-tight truncate" data-testid="text-user-name">{user?.name || "Usuário"}</span>
                <span className="text-[10px] text-secondary">{isAdmin ? "Administrador" : "Usuário"}</span>
              </div>
              <LogOut className="w-4 h-4 text-sidebar-foreground/50 ml-auto shrink-0" />
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
