import Link from "next/link";
import type { User } from "@/lib/types";
import { trocar } from "@/lib/actions";

export function Nav({ user, live }: { user: User | null; live: boolean }) {
  return (
    <header className="bg-navy text-offwhite">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        <Link href={user ? (user.papel === "manager" ? "/manager" : "/meu-dia") : "/"} className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/g4-logo.svg" alt="G4" className="h-7 w-auto" />
          <span className="font-extrabold tracking-tight border-l border-gold-dark pl-3">Lead Scorer</span>
          <span className={`tag ${live ? "tag-ok" : "tag-warn"}`}>{live ? "planilha conectada" : "modo snapshot"}</span>
        </Link>
        {user ? (
          <nav className="flex items-center gap-4 text-sm">
            {user.papel === "vendedor" && (
              <>
                <Link href="/meu-dia" className="hover:text-gold">Meu dia</Link>
                <Link href="/fila" className="hover:text-gold">Fila sem conta</Link>
              </>
            )}
            {user.papel === "manager" && <Link href="/manager" className="hover:text-gold">Meu time</Link>}
            <Link href="/revops" className="hover:text-gold">RevOps</Link>
            <Link href="/simulacao" className="hover:text-gold">Simulação</Link>
            <span className="text-grey hidden sm:inline">{user.nome}</span>
            <form action={trocar}><button className="btn-ghost text-offwhite border-gold-dark">Trocar</button></form>
          </nav>
        ) : (
          <Link href="/" className="btn-primary">Escolher vendedor</Link>
        )}
      </div>
    </header>
  );
}
