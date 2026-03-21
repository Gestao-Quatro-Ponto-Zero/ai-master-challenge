"use client";

import { useState } from "react";
import Image from "next/image";

interface Props {
  onAuth: () => void;
}

const DASHBOARD_PASSWORD = "g4social2024";

export function AuthGate({ onAuth }: Props) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === DASHBOARD_PASSWORD) {
      sessionStorage.setItem("sm_auth", "1");
      onAuth();
    } else {
      setError(true);
      setTimeout(() => setError(false), 2000);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F8FA] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-[#0F1B2D] to-[#1A2D47] p-8 text-center">
            <Image src="/logo-g4.png" alt="G4" width={120} height={66} className="h-10 w-auto mx-auto mb-4" priority />
            <h1 className="text-lg font-semibold text-white">Social Metrics</h1>
            <p className="text-xs text-white/60 mt-1">Painel de análise de mídias sociais</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label htmlFor="password" className="block text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
                Senha de acesso
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Digite a senha"
                className={`w-full px-4 py-3 rounded-xl border text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-[#E8734A]/30 focus:border-[#E8734A] ${
                  error ? "border-red-400 bg-red-50" : "border-slate-200 bg-slate-50"
                }`}
                autoFocus
              />
              {error && (
                <p className="text-xs text-red-500 mt-2">Senha incorreta. Tente novamente.</p>
              )}
            </div>
            <button
              type="submit"
              className="w-full py-3 bg-[#E8734A] hover:bg-[#d4613b] text-white font-medium rounded-xl text-sm transition-colors"
            >
              Acessar Painel
            </button>
          </form>
        </div>

        <p className="text-center text-[10px] text-slate-400 mt-4">
          Challenge 004 — Estratégia Social Media
        </p>
      </div>
    </div>
  );
}
