import Image from "next/image";

export default function LoginPage() {
  return (
    <main className="page flex items-center justify-center">
      <section className="card mx-auto w-full max-w-xl p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <Image src="/logo-g4.png" alt="Logo G4" width={28} height={28} />
          <p className="m-0 text-xs uppercase tracking-[0.2em] text-[hsl(var(--accent))]">G4 Educação</p>
        </div>
        <h1 className="mt-2 text-3xl font-semibold text-[hsl(var(--primary))]">G4 Help</h1>
        <p className="mt-3 text-sm text-slate-600">
          Acesso ao dashboard de admin ou área de cliente para tickets.
        </p>

        <div className="mt-8 flex flex-col gap-3">
          <a
            href="/api/auth/demo?role=customer&next=/customer/new"
            className="w-full rounded-xl border border-[hsl(var(--accent))] bg-[hsl(var(--accent))] px-4 py-3 text-center text-sm font-semibold hover:brightness-95"
            style={{ color: "#ffffff" }}
          >
            Entrar como Cliente
          </a>
          <a
            href="/api/auth/demo?role=admin&next=/admin"
            className="w-full rounded-xl border border-[hsl(var(--primary))] bg-[hsl(var(--primary))] px-4 py-3 text-center text-sm font-semibold hover:brightness-95"
            style={{ color: "#ffffff" }}
          >
            Entrar como Administrador
          </a>
        </div>

        <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600">
          <p className="font-semibold text-slate-900">Nota explicativa</p>
          <p className="mt-1">
            Procuramos não implantar sistema de autenticação meramente por conveniência, visando agregar mais valor na demonstração do que em outros aspectos de praxe.
          </p>
        </div>
      </section>
    </main>
  );
}
