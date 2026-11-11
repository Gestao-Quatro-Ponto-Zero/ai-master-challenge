"use client";
// Cadastro de lead novo. Vendedor cadastra para si; manager e admin escolhem o vendedor ou deixam o CRM distribuir.
import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { dinheiro } from "@/lib/calculos";
import type { Papel } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { Dialogo, ErroFormulario } from "./Dialogo";
import { Botao } from "./ui/Botao";
import { Campo } from "./ui/Campo";
import { Seletor } from "./ui/Seletor";

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
      <Botao nivel="primario" icone="mais" onClick={() => setAberto(true)}>
        Novo lead
      </Botao>
      {aberto ? (
        <Dialogo titulo="Novo lead" onFechar={fechar}>
          <form onSubmit={salvar} className="grid gap-3">
            <div className="grid gap-1 text-sm font-semibold">
              <span aria-hidden>Produto</span>
              <Seletor
                rotulo="Produto"
                valor={produto}
                onMudar={setProduto}
                textoVazio="Escolha o produto"
                autoFoco
                className="w-full font-normal"
                opcoes={produtos.map((p) => ({ valor: p.nome, rotulo: `${p.nome} (${dinheiro(p.preco)})` }))}
              />
            </div>
            <label className="grid gap-1 text-sm font-semibold">
              Empresa (opcional)
              <Campo list="lista-empresas" value={conta} onChange={(e) => setConta(e.target.value)} placeholder="Digite para buscar" />
              <datalist id="lista-empresas">
                {empresas.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
            </label>
            {papel === "vendedor" ? null : (
              <div className="grid gap-1 text-sm font-semibold">
                <span aria-hidden>Vendedor</span>
                <Seletor
                  rotulo="Vendedor"
                  valor={vendedor}
                  onMudar={setVendedor}
                  className="w-full font-normal"
                  opcoes={[{ valor: "", rotulo: "Distribuir automaticamente" }, ...vendedores.map((v) => ({ valor: v, rotulo: v }))]}
                />
                <span className="text-xs font-normal text-texto-2">
                  A distribuição usa o encaixe do lead com cada vendedor. Enquanto a nota não existe, o lead vai para quem tem menos deals abertos.
                </span>
              </div>
            )}
            <div className="grid gap-1 text-sm font-semibold">
              <span aria-hidden>Estágio</span>
              <Seletor
                rotulo="Estágio"
                valor={estagio}
                onMudar={(v) => setEstagio(v as "Prospecting" | "Engaging")}
                className="w-full font-normal"
                opcoes={[
                  { valor: "Prospecting", rotulo: "Novo lead" },
                  { valor: "Engaging", rotulo: "Em negociação (abre hoje)" },
                ]}
              />
            </div>
            <label className="grid gap-1 text-sm font-semibold">
              Nome do deal (opcional)
              <Campo value={nome} maxLength={120} onChange={(e) => setNome(e.target.value)} placeholder="Se vazio: Empresa · Produto" />
            </label>
            <ErroFormulario texto={erro} />
            <div className="flex justify-end gap-2">
              <Botao nivel="secundario" onClick={fechar}>
                Cancelar
              </Botao>
              <Botao type="submit" nivel="primario" disabled={enviando}>
                {enviando ? "Cadastrando…" : "Cadastrar lead"}
              </Botao>
            </div>
          </form>
        </Dialogo>
      ) : null}
    </>
  );
}
