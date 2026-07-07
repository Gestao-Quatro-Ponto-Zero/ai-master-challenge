"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Crown,
  LineChart,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { agents, managers } from "@/lib/data";
import { useAuth } from "@/lib/hooks/useAuth";
import { avatarBg, cn, formatPercent, initials } from "@/lib/utils";
import type { Role } from "@/lib/types";

const GESTOR_NAME = "Head de RevOps";

export default function LoginPage() {
  const router = useRouter();
  const { user, setUser, hydrated } = useAuth();
  const [step, setStep] = useState<"role" | "seller" | "manager">("role");

  const sellerOptions = useMemo(
    () =>
      [...agents]
        .filter((a) => a.openDeals > 0)
        .sort((a, b) => b.overallWr - a.overallWr),
    [],
  );
  const managerOptions = useMemo(
    () => [...managers].sort((a, b) => b.totalDeals - a.totalDeals),
    [],
  );

  useEffect(() => {
    if (hydrated && user) router.push("/pipeline");
  }, [hydrated, user, router]);

  function pick(role: Role, name: string) {
    setUser({ role, name });
    router.push("/pipeline");
  }

  return (
    <main
      className="min-h-screen flex items-center justify-center px-4 py-10 relative"
      style={{
        background:
          "radial-gradient(ellipse at top, #162540 0%, #0a1628 45%, #06101f 100%)",
      }}
    >
      <div className="w-full max-w-4xl relative">
        <div className="mb-10 flex flex-col items-center text-center">
          <Image
            src="/logo-g4.png"
            alt="G4"
            width={72}
            height={72}
            className="h-[72px] w-[72px] mb-5 rounded-lg object-cover"
            priority
          />
          <h1 className="text-3xl font-semibold tracking-tight text-white">
            G4 Lead Scorer
          </h1>
          <p className="mt-2 text-sm text-slate-400 max-w-md">
            Priorização inteligente de pipeline com pontuação composta e
            remanejamento automático por especialização setorial.
          </p>
        </div>

        {step === "role" && (
          <div className="grid gap-4 sm:grid-cols-3">
            <RoleCard
              icon={<Crown className="h-6 w-6" />}
              title="Gestor"
              description="Visão completa de todos os times, com análises consolidadas e ranking de gerentes."
              onClick={() => pick("gestor", GESTOR_NAME)}
              cta="Entrar direto"
            />
            <RoleCard
              icon={<LineChart className="h-6 w-6" />}
              title="Gerente"
              description="Gestão do seu time de vendedores: pipeline, remanejamentos e desempenho."
              onClick={() => setStep("manager")}
              cta="Selecionar gerente"
            />
            <RoleCard
              icon={<Users className="h-6 w-6" />}
              title="Vendedor"
              description="Seus leads, tarefas do dia, setores fortes e desempenho pessoal."
              onClick={() => setStep("seller")}
              cta="Selecionar vendedor"
            />
          </div>
        )}

        {(step === "seller" || step === "manager") && (
          <Card className="p-2 border-slate-200 max-w-2xl mx-auto shadow-[var(--shadow-login)]">
            <div className="flex items-center gap-2 px-3 pt-2 pb-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setStep("role")}
                className="gap-1 text-slate-500"
              >
                <ArrowLeft className="h-4 w-4" />
                Voltar
              </Button>
              <div className="ml-auto text-sm text-slate-500">
                {step === "seller"
                  ? `${sellerOptions.length} vendedores com pipeline ativo`
                  : `${managerOptions.length} gerentes`}
              </div>
            </div>

            <ScrollArea className="h-[420px] px-1">
              <div className="divide-y divide-slate-100 pr-2">
                {step === "seller"
                  ? sellerOptions.map((a) => (
                      <button
                        key={a.name}
                        onClick={() => pick("seller", a.name)}
                        className="w-full flex items-center gap-3 py-2.5 px-2 rounded-md hover:bg-slate-50 text-left transition-colors duration-150"
                      >
                        <div
                          className={cn(
                            "h-10 w-10 shrink-0 rounded-full grid place-items-center text-white text-sm font-semibold",
                            avatarBg(a.name),
                          )}
                        >
                          {initials(a.name)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-slate-900">
                            {a.name}
                          </div>
                          <div className="text-xs text-slate-500 truncate">
                            {a.manager} · {a.region} · {a.openDeals} negociações
                          </div>
                        </div>
                        <Badge
                          variant="secondary"
                          className="bg-blue-50 text-blue-700 border border-blue-100"
                        >
                          Conv. {formatPercent(a.overallWr)}
                        </Badge>
                        <ArrowRight className="h-4 w-4 text-slate-400 ml-2" />
                      </button>
                    ))
                  : managerOptions.map((m) => (
                      <button
                        key={m.manager}
                        onClick={() => pick("manager", m.manager)}
                        className="w-full flex items-center gap-3 py-2.5 px-2 rounded-md hover:bg-slate-50 text-left transition-colors duration-150"
                      >
                        <div
                          className={cn(
                            "h-10 w-10 shrink-0 rounded-full grid place-items-center text-white text-sm font-semibold",
                            avatarBg(m.manager),
                          )}
                        >
                          {initials(m.manager)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-slate-900">
                            {m.manager}
                          </div>
                          <div className="text-xs text-slate-500 truncate">
                            {m.agents} vendedores · {m.totalDeals} negociações
                            abertas · {m.reallocations} remanejamentos
                          </div>
                        </div>
                        <ArrowRight className="h-4 w-4 text-slate-400 ml-2" />
                      </button>
                    ))}
              </div>
            </ScrollArea>
          </Card>
        )}

        <p className="mt-8 text-center text-xs text-slate-500 max-w-lg mx-auto leading-relaxed">
          Login simulado para demonstração — em produção, autenticação segura
          com controle por hierarquia.
        </p>
      </div>
    </main>
  );
}

function RoleCard({
  icon,
  title,
  description,
  onClick,
  cta,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick: () => void;
  cta: string;
}) {
  return (
    <button
      onClick={onClick}
      className="group text-left p-6 rounded-xl border border-white/10 bg-white/5 hover:border-[color:var(--brand-gold-500)] hover:bg-white/[0.08] transition-colors duration-150"
    >
      <div className="h-11 w-11 rounded-lg bg-white/10 text-[color:var(--brand-gold-400)] grid place-items-center mb-4 group-hover:bg-[color:var(--brand-gold-500)] group-hover:text-[color:var(--brand-navy-900)] transition-colors duration-150">
        {icon}
      </div>
      <div className="font-semibold text-white">{title}</div>
      <p className="mt-1.5 text-sm text-slate-400">{description}</p>
      <div className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-[color:var(--brand-gold-400)] group-hover:text-[color:var(--brand-gold-300)]">
        {cta}
        <ArrowRight className="h-4 w-4" />
      </div>
    </button>
  );
}
