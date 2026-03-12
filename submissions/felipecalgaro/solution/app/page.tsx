import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { LoginForm } from "@/app/components/login-form";
import { getSalesAgentOptions } from "@/utils/sales-team";

const SALES_AGENT_COOKIE = "lead-scorer-sales-agent";

export default async function Home() {
  const salesAgents = await getSalesAgentOptions();

  async function login(formData: FormData) {
    "use server";

    const selectedAgent = String(formData.get("salesAgent") ?? "").trim();
    const isValidAgent = salesAgents.some((agent) => agent.name === selectedAgent);

    if (!isValidAgent) {
      redirect("/");
    }

    const cookieStore = await cookies();

    cookieStore.set(SALES_AGENT_COOKIE, selectedAgent, {
      httpOnly: true,
      maxAge: 60 * 60 * 24 * 30,
      path: "/",
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
    });

    redirect("/pipeline");
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#fff8ea,_#f4ede2_40%,_#e7dfd4_100%)] px-6 py-10 text-stone-900 sm:px-10 lg:px-16">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl items-center justify-center">
        <section className="grid w-full overflow-hidden rounded-[2rem] border border-stone-900/10 bg-white/85 shadow-[0_30px_90px_rgba(76,61,43,0.16)] backdrop-blur sm:grid-cols-[1.1fr_0.9fr]">
          <div className="flex flex-col justify-between gap-10 bg-stone-950 px-8 py-10 text-stone-100 sm:px-10 sm:py-12">
            <div className="space-y-6">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-amber-300/80">
                Desafio 003
              </p>
              <div className="space-y-4">
                <h1 className="max-w-lg text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
                  Comece pela sua lista de negócios, não por um dashboard vazio.
                </h1>
                <p className="max-w-md text-base leading-7 text-stone-300">
                  Escolha seu perfil de vendedor para carregar o pipeline correto e
                  manter o contexto de pontuação ligado a essa seleção.
                </p>
              </div>
            </div>

            <div className="grid gap-4 text-sm text-stone-300 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-medium text-stone-50">Priorização transparente</p>
                <p className="mt-2 leading-6">
                  Cada negócio ranqueado pode explicar os fatores positivos e
                  negativos mais fortes por tras da sua pontuação.
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-medium text-stone-50">Dados reais de CRM</p>
                <p className="mt-2 leading-6">
                  A lista de vendedores e carregada do CSV da equipe comercial, sem
                  dados fixos na interface.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center bg-[linear-gradient(180deg,_rgba(255,255,255,0.92),_rgba(245,239,231,0.98))] px-8 py-10 sm:px-10 sm:py-12">
            <div className="w-full space-y-8">
              <div className="space-y-3">
                <p className="text-sm font-medium uppercase tracking-[0.24em] text-stone-500">
                  Acesso
                </p>
                <div className="space-y-2">
                  <h2 className="text-3xl font-semibold tracking-tight text-stone-950">
                    Selecione seu vendedor
                  </h2>
                  <p className="max-w-md text-sm leading-6 text-stone-600">
                    Filtre por gestor ou região e depois escolha o vendedor para
                    carregar o pipeline ranqueado.
                  </p>
                </div>
              </div>

              <LoginForm action={login} salesAgents={salesAgents} />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
