"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [showPass, setShowPass] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    setLoading(false);
    if (res.ok) {
      router.push("/");
      router.refresh();
    } else {
      setError("Token inválido. Verifique suas credenciais.");
    }
  }

  return (
    <div className="min-h-screen flex bg-gray-950">

      {/* ── Left: login form ── */}
      <div className="flex-1 flex flex-col justify-center items-center px-8 py-12">
        <div className="w-full max-w-sm">

          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
              <span className="text-amber-400 font-black text-sm tracking-widest">G4</span>
            </div>
            <div>
              <div className="text-white font-bold text-lg leading-tight tracking-tight">Lead Scorer</div>
              <div className="text-gray-500 text-xs">Pipeline inteligente de vendas B2B</div>
            </div>
          </div>

          <h1 className="text-white text-2xl font-bold mb-1">Acessar Dashboard</h1>
          <p className="text-gray-500 text-sm mb-8">
            Use o token fornecido pelo administrador para entrar.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-400 uppercase tracking-wider mb-1.5">
                Token de acesso
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </span>
                <input
                  type={showPass ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Digite seu token de acesso"
                  required
                  className="w-full bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-xl pl-10 pr-10 py-3 focus:border-amber-500/60 focus:outline-none placeholder-gray-600 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPass ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/25 text-red-400 text-sm rounded-xl px-4 py-3">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !password}
              className="w-full py-3.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-gray-950 font-bold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
                  Verificando...
                </>
              ) : (
                "Acessar Dashboard →"
              )}
            </button>
          </form>

          <p className="text-center text-gray-600 text-xs mt-8">
            Não possui acesso?{" "}
            <span className="text-gray-400">Entre em contato com o administrador</span>
          </p>
        </div>
      </div>

      {/* ── Right: showcase panel ── */}
      <div className="hidden lg:flex flex-1 flex-col justify-center items-center bg-gray-900 border-l border-gray-800 px-12 py-12">
        <div className="mb-8 text-amber-400">
          <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>

        <h2 className="text-white text-2xl font-bold text-center mb-2 leading-tight">
          Inteligência comercial para{" "}
          <span className="text-amber-400">vendedores e gestores</span>
        </h2>
        <p className="text-gray-500 text-sm text-center mb-12 max-w-xs">
          Priorize os leads certos e feche mais negócios com scoring baseado em dados históricos reais da sua equipe.
        </p>

        <div className="grid grid-cols-3 gap-6 w-full max-w-sm">
          <div className="text-center">
            <div className="text-2xl font-black text-amber-400 mb-1">0–100</div>
            <div className="text-gray-500 text-xs">Score de prioridade</div>
          </div>
          <div className="text-center border-x border-gray-800">
            <div className="text-2xl font-black text-emerald-400 mb-1">4</div>
            <div className="text-gray-500 text-xs">Componentes de análise</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-black text-amber-400 mb-1">∞</div>
            <div className="text-gray-500 text-xs">Deals monitorados</div>
          </div>
        </div>

        <div className="mt-12 space-y-3 w-full max-w-xs">
          {[
            "Pipeline priorizado por score de dados",
            "Insights de sazonalidade e win rate",
            "Ações diretas sobre os deals",
            "Gestão completa da equipe de vendas",
          ].map((f) => (
            <div key={f} className="flex items-center gap-3 text-sm">
              <span className="text-amber-400 flex-shrink-0">✓</span>
              <span className="text-gray-400">{f}</span>
            </div>
          ))}
        </div>

        <div className="mt-12 text-gray-600 text-xs">
          Powered by Lucas de Paula · G4 Educação AI Master
        </div>
      </div>
    </div>
  );
}
