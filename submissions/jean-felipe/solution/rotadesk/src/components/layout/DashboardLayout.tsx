"use client";

import { Sidebar } from "./Sidebar";

export function DashboardLayout({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <div className="hidden md:flex">
        <Sidebar />
      </div>
      <div className="flex flex-1 flex-col">
        <header className="border-b border-border bg-card px-4 py-4 md:hidden">
          <p className="font-bold">RotaDesk</p>
          <nav className="mt-2 flex gap-2 overflow-x-auto text-sm">
            <a href="/">Dashboard</a>
            <a href="/simulador">Simulador</a>
            <a href="/chat">Chat</a>
            <a href="/kanban">Kanban</a>
          </nav>
        </header>
        <main className="flex-1">
          <div className="border-b border-border bg-card px-6 py-4">
            <h2 className="text-2xl font-semibold">{title}</h2>
          </div>
          <div className="mx-auto max-w-7xl px-4 py-6 md:px-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
