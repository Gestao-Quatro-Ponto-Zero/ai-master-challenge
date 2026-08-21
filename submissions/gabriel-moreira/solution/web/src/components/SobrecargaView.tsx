import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { ESTADO_LABELS, type OportunidadeSobrecarregada } from "../types";
import { FitCell } from "./FitDisplay";

interface Grupo {
  chave: string;
  sales_agent: string;
  regional_office: string | null;
  estado: string;
  contagem: number;
  media_escritorio: number;
  razao: number | null;
  itens: OportunidadeSobrecarregada[];
}

function agrupar(items: OportunidadeSobrecarregada[]): Grupo[] {
  const mapa = new Map<string, Grupo>();
  for (const item of items) {
    const chave = `${item.sales_agent}::${item.estado}`;
    let grupo = mapa.get(chave);
    if (!grupo) {
      grupo = {
        chave,
        sales_agent: item.sales_agent,
        regional_office: item.regional_office,
        estado: item.estado,
        contagem: item.contagem,
        media_escritorio: item.media_escritorio,
        razao: item.razao,
        itens: [],
      };
      mapa.set(chave, grupo);
    }
    grupo.itens.push(item);
  }
  return Array.from(mapa.values()).sort(
    (a, b) =>
      a.sales_agent.localeCompare(b.sales_agent, "pt-BR") || a.estado.localeCompare(b.estado, "pt-BR")
  );
}

/** Aba Sobrecarga — oportunidades de vendedores sobrecarregados,
 * agrupadas por (vendedor, estado), com a sugestão de redistribuição e o
 * fit lado a lado, visível sem abrir o detalhe (Requirement "Aba de
 * sobrecarga"). Nenhuma reatribuição é executada por esta tela. */
export function SobrecargaView({ onCarregado }: { onCarregado?: (total: number) => void }) {
  const [items, setItems] = useState<OportunidadeSobrecarregada[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    api
      .getSobrecarregados({ page_size: 500 })
      .then((data) => {
        if (cancelado) return;
        setItems(data.items);
        onCarregado?.(data.total);
      })
      .catch((err: unknown) => {
        if (!cancelado) setErro(err instanceof ApiError ? err.message : "erro desconhecido");
      });
    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (erro) {
    return (
      <p className="text-alert text-sm bg-alert/5 border border-alert rounded-xs px-3 py-2">
        Não foi possível carregar a sobrecarga: {erro}
      </p>
    );
  }

  if (items === null) {
    return <p className="text-muted">Carregando…</p>;
  }

  if (items.length === 0) {
    return (
      <div className="bg-white border border-border rounded-sm p-10 text-center">
        <p className="text-navy font-semibold">Distribuição equilibrada</p>
        <p className="text-sm text-muted mt-1 max-w-md mx-auto">
          Nenhum vendedor está com carga ≥1,5× a média do próprio escritório (com ao menos 5
          oportunidades) no momento.
        </p>
      </div>
    );
  }

  const grupos = agrupar(items);

  return (
    <div className="flex flex-col gap-6">
      <p className="text-xs text-muted bg-gold/10 border border-gold rounded-xs px-3 py-2">
        Sugestão informativa — nenhuma reatribuição é executada pelo sistema. O dono da
        oportunidade permanece inalterado.
      </p>
      {grupos.map((grupo) => (
        <GrupoSobrecarga key={grupo.chave} grupo={grupo} />
      ))}
    </div>
  );
}

function GrupoSobrecarga({ grupo }: { grupo: Grupo }) {
  return (
    <section className="bg-white border border-border rounded-sm overflow-hidden">
      <header className="flex flex-wrap items-baseline gap-3 px-4 py-3 bg-bg border-b border-border">
        <h3 className="text-sm font-bold text-navy">{grupo.sales_agent}</h3>
        <span className="text-xs text-muted">{grupo.regional_office ?? "—"}</span>
        <span className="text-xs font-semibold text-navy bg-gold/15 border border-gold rounded-full px-2 py-0.5">
          {ESTADO_LABELS[grupo.estado as keyof typeof ESTADO_LABELS] ?? grupo.estado}
        </span>
        <span className="text-xs text-muted">
          {grupo.contagem} contra média {grupo.media_escritorio.toFixed(2)} do escritório
          {grupo.razao !== null && ` (${grupo.razao.toFixed(2)}×)`}
        </span>
      </header>
      <div className="divide-y divide-border">
        {grupo.itens.map((item) => (
          <OportunidadeSobrecarregadaRow key={item.opportunity_id} item={item} />
        ))}
      </div>
    </section>
  );
}

function OportunidadeSobrecarregadaRow({ item }: { item: OportunidadeSobrecarregada }) {
  return (
    <div className="px-4 py-3 flex flex-col gap-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-navy">
          {item.product} {item.account && <span className="text-muted font-normal">· {item.account}</span>}
        </span>
        <span className="text-xs text-muted font-mono">{item.opportunity_id}</span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-1">
            Atual — {item.sales_agent}
          </p>
          <dl className="grid grid-cols-2 gap-2">
            <FitCell label="Produto" fit={item.fit_produto} />
            <FitCell label="Setor" fit={item.fit_setor} />
          </dl>
        </div>
        <div>
          {item.sugestao.disponivel ? (
            <>
              <p className="text-xs font-semibold text-navy uppercase tracking-wide mb-1">
                Sugerido — {item.sugestao.sales_agent}
              </p>
              <dl className="grid grid-cols-2 gap-2">
                <FitCell label="Produto" fit={item.sugestao.fit_produto!} />
                <FitCell label="Setor" fit={item.sugestao.fit_setor!} />
              </dl>
            </>
          ) : (
            <p className="text-sm text-muted italic mt-4">
              Nenhum candidato elegível no escritório para redistribuição.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
