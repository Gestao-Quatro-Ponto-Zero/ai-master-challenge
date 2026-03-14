"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { Usuario } from "@/types";
import { UserPlus, Shield, User, Crown, Trash2, Check, X, Loader2 } from "lucide-react";

export default function EquipePage() {
  const { user: currentUser } = useAuth();
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nome: "", email: "", senha: "", perfil: "agente" });
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState<{ tipo: "ok" | "erro"; texto: string } | null>(null);

  const podeExcluir = (alvo: Usuario): boolean => {
    if (!currentUser) return false;
    if (currentUser.perfil === "diretor") return true;
    if (currentUser.perfil === "gestor" && alvo.perfil === "agente") return true;
    return false;
  };

  const carregar = async () => {
    try {
      const data = await api.listarUsuarios();
      setUsuarios(data);
    } catch {
      setMsg({ tipo: "erro", texto: "Erro ao carregar usuários" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { carregar(); }, []);

  const criar = async () => {
    if (!form.nome || !form.email || !form.senha) return;
    setSubmitting(true);
    try {
      await api.criarUsuario(form.nome, form.email, form.senha, form.perfil);
      setMsg({ tipo: "ok", texto: `Usuário ${form.nome} criado com sucesso` });
      setForm({ nome: "", email: "", senha: "", perfil: "agente" });
      setShowForm(false);
      carregar();
    } catch (e: unknown) {
      setMsg({ tipo: "erro", texto: e instanceof Error ? e.message : "Erro ao criar usuário" });
    } finally {
      setSubmitting(false);
    }
  };

  const desativar = async (email: string) => {
    try {
      await api.desativarUsuario(email);
      setMsg({ tipo: "ok", texto: `Usuário ${email} desativado` });
      carregar();
    } catch {
      setMsg({ tipo: "erro", texto: "Erro ao desativar usuário" });
    }
  };

  const toggleAtivo = async (u: Usuario) => {
    try {
      await api.atualizarUsuario(u.email, { ativo: !u.ativo });
      carregar();
    } catch {
      setMsg({ tipo: "erro", texto: "Erro ao atualizar status" });
    }
  };

  if (loading) return <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Gestão de Equipe</h1>
          <p className="text-sm text-gray-500 mt-1">Gerenciar contas de agentes, gestores e diretores</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <UserPlus className="w-4 h-4" /> Novo Usuário
        </button>
      </div>

      {msg && (
        <div className={`mb-4 p-3 rounded-lg text-sm flex items-center gap-2 ${msg.tipo === "ok" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          {msg.tipo === "ok" ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
          {msg.texto}
          <button onClick={() => setMsg(null)} className="ml-auto text-gray-400 hover:text-gray-600"><X className="w-3 h-3" /></button>
        </div>
      )}

      {showForm && (
        <div className="card mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Criar Novo Usuário</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input className="input-field" placeholder="Nome completo" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
            <input className="input-field" placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input className="input-field" placeholder="Senha" type="password" value={form.senha} onChange={(e) => setForm({ ...form, senha: e.target.value })} />
            <select className="input-field" value={form.perfil} onChange={(e) => setForm({ ...form, perfil: e.target.value })}>
              <option value="agente">Agente</option>
              <option value="gestor">Gestor</option>
              {currentUser?.perfil === "diretor" && <option value="diretor">Diretor</option>}
            </select>
          </div>
          <div className="mt-4 flex gap-2">
            <button onClick={criar} disabled={submitting} className="btn-primary text-sm">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Criar"}
            </button>
            <button onClick={() => setShowForm(false)} className="btn-secondary text-sm">Cancelar</button>
          </div>
        </div>
      )}

      <div className="card">
        <table className="w-full">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase border-b">
              <th className="pb-3 pr-4">Nome</th>
              <th className="pb-3 pr-4">Email</th>
              <th className="pb-3 pr-4">Perfil</th>
              <th className="pb-3 pr-4">Status</th>
              <th className="pb-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u) => (
              <tr key={u.email} className="border-b last:border-0 hover:bg-gray-50">
                <td className="py-3 pr-4">
                  <div className="flex items-center gap-2">
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white ${u.perfil === "diretor" ? "bg-purple-600" : u.perfil === "gestor" ? "bg-emerald-600" : "bg-blue-600"}`}>
                      {u.nome.split(" ").map(n => n[0]).join("").slice(0, 2)}
                    </div>
                    <span className="text-sm font-medium text-gray-800">{u.nome}</span>
                  </div>
                </td>
                <td className="py-3 pr-4 text-sm text-gray-600">{u.email}</td>
                <td className="py-3 pr-4">
                  <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
                    u.perfil === "diretor" ? "bg-purple-100 text-purple-700" :
                    u.perfil === "gestor" ? "bg-emerald-100 text-emerald-700" :
                    "bg-blue-100 text-blue-700"
                  }`}>
                    {u.perfil === "diretor" ? <Crown className="w-3 h-3" /> : u.perfil === "gestor" ? <Shield className="w-3 h-3" /> : <User className="w-3 h-3" />}
                    {u.perfil === "diretor" ? "Diretor" : u.perfil === "gestor" ? "Gestor" : "Agente"}
                  </span>
                </td>
                <td className="py-3 pr-4">
                  <button onClick={() => toggleAtivo(u)} className={`text-xs font-medium px-2 py-0.5 rounded-full cursor-pointer ${u.ativo ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                    {u.ativo ? "Ativo" : "Inativo"}
                  </button>
                </td>
                <td className="py-3 text-right">
                  {podeExcluir(u) ? (
                    <button onClick={() => desativar(u.email)} className="text-red-400 hover:text-red-600 transition-colors" title="Desativar">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  ) : (
                    <span className="text-gray-300"><Trash2 className="w-4 h-4" /></span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {usuarios.length === 0 && (
          <p className="text-center text-gray-400 py-8">Nenhum usuário cadastrado</p>
        )}
      </div>
    </div>
  );
}
