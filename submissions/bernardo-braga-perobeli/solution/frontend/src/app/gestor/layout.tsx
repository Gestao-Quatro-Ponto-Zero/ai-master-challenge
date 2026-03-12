"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { BarChart3, TrendingUp, Tag, Bell, Users, Activity, LogOut, Loader2, UserCog, Upload } from "lucide-react";
import Image from "next/image";

const NAV = [
  { href: "/gestor", label: "Dashboard", icon: BarChart3 },
  { href: "/gestor/volume", label: "Volume por Nível", icon: TrendingUp },
  { href: "/gestor/motivos", label: "Motivos por Nível", icon: Tag },
  { href: "/gestor/alertas", label: "Alertas", icon: Bell },
  { href: "/gestor/agentes", label: "Agentes Online", icon: Users },
  { href: "/gestor/equipe", label: "Gestão de Equipe", icon: UserCog },
  { href: "/gestor/importar", label: "Importar Dados", icon: Upload },
  { href: "/gestor/diagnostico", label: "Diagnóstico", icon: Activity },
];

export default function GestorLayout({ children }: { children: React.ReactNode }) {
  const { user, logout, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) router.replace("/");
    if (!loading && user && user.perfil !== "gestor" && user.perfil !== "diretor") router.replace("/agente");
  }, [user, loading, router]);

  if (loading || !user) {
    return <div className="min-h-screen flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  }

  const handleLogout = () => {
    logout();
    router.replace("/");
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-64 bg-sidebar flex flex-col shrink-0">
        <div className="p-5 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg overflow-hidden">
            <Image src="/logo-g4.png" alt="G4" width={36} height={36} className="object-contain" />
          </div>
          <div>
            <p className="text-sm font-bold text-white leading-tight">G4 IA</p>
            <p className="text-[10px] text-blue-400">Inteligência de Suporte</p>
          </div>
        </div>

        <nav className="flex-1 px-3 space-y-1 mt-4">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} className={active ? "sidebar-link-active" : "sidebar-link"}>
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center text-xs font-bold text-white">
              {user.nome.split(" ").map((n) => n[0]).join("")}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.nome}</p>
              <p className="text-[10px] text-gray-400 truncate">{user.email}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-colors w-full">
            <LogOut className="w-3.5 h-3.5" /> Sair do sistema
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  );
}
