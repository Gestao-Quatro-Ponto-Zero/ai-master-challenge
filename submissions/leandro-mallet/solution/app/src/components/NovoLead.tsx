"use client";
// Cadastro de lead novo. Vendedor cadastra para si; manager e admin escolhem o vendedor ou deixam o CRM distribuir.
import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { dinheiro } from "@/lib/calculos";
import type { Papel } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { botaoNeutro, botaoPrincipal, campo, Dialogo, ErroFormulario } from "./Dialogo";

interface Props {
  papel: Papel;
  produtos: { nome: string; preco: number }[];
  empresas: string[];
  vendedores: string[];
}

export function NovoLead({ papel, produtos, empresas, vendedores }: Props) {
  const avisos = useAvisos();
  const router = useRouter();
  const [aberto, setAberto] = useState(false);
  const [produto, setProduto] = useState("");
  const [conta, setConta] = useState("");
  const [vendedor, setVendedor] = useState("");
  const [estagio, setEstagio] = useState<"Prospecting" | "Engaging">("Prospecting");
  const [nome, setNome] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const fechar = useCallback(() => setAberto(false), []);

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!produto) return setErro("Escolha o produto.");
    if (conta && !empresas.includes(conta)) return setErro("Esta empresa não está cadastrada. Escolha uma da lista ou cadastre na aba Contas.");
    setEnviando(true);
    setErro(null);
    const r = await pedir<{ id: string }>("/api/deals", "POST", { produto, conta: conta || null, vendedor: vendedor || null, estagio, nome: nome || null });
    setEnviando(false);
    if (!r.ok || !r.dados) return setErro(r.erro ?? "Não foi possível cadastrar. Tente de novo.");
    setAberto(false);
    setProduto("");
    setConta("");
    setNome("");
    avisos.ok("Lead cadastrado. A nota aparece na próxima rodada do score.");
    avisos.atualizar();
    router.push(`/leads?deal=${encodeURIComponent(r.dados.id)}`, { scroll: false });
  }

  return (
    <>
      <button onClick={() => setAberto(true)} className={botaoPrincipal}>
        Novo lead
      </button>
      {aberto ? (
        <Dialogo titulo="Novo lead" onFechar={fechar}>
          <form onSubmit={salvar} className="grid gap-3">
            <label className="text-sm font-semibold">
              Produto
              <select value={produto} onChange={(e) => setProduto(e.target.value)} className={campo} autoFocus>
                <option value="">Escolha o produto</option>
                {produtos.map((p) => (
                  <option key={p.nome} value={p.nome}>
                    {p.nome} ({dinheiro(p.preco)})
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm font-semibold">
              Empresa (opcional)
              <input list="lista-empresas" value={conta} onChange={(e) => setConta(e.target.value)} placeholder="Digite para buscar" className={campo} />
              <datalist id="lista-empresas">
                {empresas.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
            </label>
            {papel === "vendedor" ? null : (
              <label className="text-sm font-semibold">
                Vendedor
                <select value={vendedor} onChange={(e) => setVendedor(e.target.value)} className={campo}>
                  <option value="">Distribuir automaticamente</option>
                  {vendedores.map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
                </select>
                <span className="mt-1 block text-xs font-normal text-texto-2">
                  A distribuição usa o encaixe com o vendedor (FIT). Enquanto a nota não existe, o lead vai para quem tem menos deals abertos.
                </span>
              </label>
            )}
            <label className="text-sm font-semibold">
              Estágio
              <select value={estagio} onChange={(e) => setEstagio(e.target.value as "Prospecting" | "Engaging")} className={campo}>
                <option value="Prospecting">Prospecção</option>
                <option value="Engaging">Em negociação (abre hoje)</option>
              </select>
            </label>
            <label className="text-sm font-semibold">
              Nome do deal (opcional)
              <input value={nome} maxLength={120} onChange={(e) => setNome(e.target.value)} placeholder="Se vazio: Empresa · Produto" className={campo} />
            </label>
            <ErroFormulario texto={erro} />
            <div className="flex justify-end gap-2">
              <button type="button" onClick={fechar} className={botaoNeutro}>
                Cancelar
              </button>
              <button type="submit" disabled={enviando} className={botaoPrincipal}>
                {enviando ? "Cadastrando…" : "Cadastrar lead"}
              </button>
            </div>
          </form>
        </Dialogo>
      ) : null}
    </>
  );
}
