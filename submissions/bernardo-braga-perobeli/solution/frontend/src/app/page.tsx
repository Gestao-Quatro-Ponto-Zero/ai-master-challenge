"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Loader2 } from "lucide-react";
import Image from "next/image";

export default function LoginPage() {
  const { user, login, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace(user.perfil === "agente" ? "/agente" : "/gestor");
    }
  }, [user, loading, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    if (!email.trim() || !senha.trim()) {
      setErro("Preencha email e senha.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.login(email.trim(), senha.trim());
      login(res.token, { nome: res.nome, email: res.email, perfil: res.perfil });
      if (res.perfil === "agente") {
        api.definirStatusAgente(res.nome, "online").catch(() => {});
      }
      router.replace(res.perfil === "agente" ? "/agente" : "/gestor");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "";
      setErro(msg || "Email ou senha inválidos.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl overflow-hidden mb-4">
            <Image src="/logo-g4.png" alt="G4" width={80} height={80} className="object-contain" />
          </div>
          <h1 className="text-3xl font-bold text-white">G4 IA</h1>
          <p className="text-blue-300 mt-1">Inteligência de Suporte</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-1">Acesso ao Sistema</h2>
          <p className="text-sm text-gray-500 mb-6">Acesso à ferramenta de inteligência para suporte do G4</p>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email corporativo</label>
              <input
                type="email"
                className="input"
                placeholder="seu.nome@g4suporte.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Senha</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
              />
            </div>

            {erro && (
              <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg">{erro}</div>
            )}

            <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={submitting}>
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {submitting ? "Autenticando..." : "Entrar"}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-100">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3">Contas de demonstração</p>
            <div className="space-y-2 text-xs text-gray-500">
              <div className="flex justify-between"><span className="font-medium text-gray-700">Agente</span><code className="text-blue-600">agente1@g4suporte.com / agente123</code></div>
              <div className="flex justify-between"><span className="font-medium text-gray-700">Gestor</span><code className="text-blue-600">gestor@g4suporte.com / gestor123</code></div>
              <div className="flex justify-between"><span className="font-medium text-gray-700">Diretor</span><code className="text-blue-600">diretor@g4suporte.com / diretor123</code></div>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-blue-400/60 mt-6">Criado por Bernardo Braga Perobeli</p>
      </div>
    </div>
  );
}
