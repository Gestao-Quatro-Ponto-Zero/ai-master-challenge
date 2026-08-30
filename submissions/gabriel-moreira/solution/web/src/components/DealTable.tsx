import { ESTADO_BADGE, SOBRECARGA_BADGE_CLASSES } from "../estadoColors";
import { formatIdade, formatUsd } from "../format";
import type { Oportunidade, SortKey, SortOrder } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";

/** Fila de trabalho — SCORE, ESTADO, produto, conta, vendedor, VALOR,
 * estágio, idade e CONFIANÇA. PRIORIDADE em dólares não aparece aqui nem como
 * critério de ordenação — é um valor intermediário auditável, visível só
 * no painel de detalhe (Requirement "Ausência de PRIORIDADE em dólares
 * nas superfícies de leitura"). A decomposição, a razão de confiança e o
 * plano de ação ficam no painel de detalhe, não na linha (Requirement
 * "Justificativa visível e plano de ação"). Ordenação é resolvida no
 * servidor via `sort`/`order`, não mais no cliente. */
export function DealTable({
  oportunidades,
  sort,
  order,
  total,
  page,
  totalPages,
  onSortChange,
  onOpenDetail,
  onNavigateToSobrecarga,
}: {
  oportunidades: Oportunidade[];
  sort: SortKey;
  order: SortOrder;
  total: number;
  page: number;
  totalPages: number;
  onSortChange: (key: SortKey) => void;
  onOpenDetail: (opportunityId: string) => void;
  /** Conduz o usuário à aba Sobrecarga — o marcador nunca exibe o
   * vendedor sugerido aqui (Requirement "Alerta de sobrecarga na
   * listagem de oportunidades"). */
  onNavigateToSobrecarga?: () => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs text-muted">
        {total.toLocaleString("pt-BR")} oportunidade{total === 1 ? "" : "s"} no recorte · página{" "}
        {totalPages === 0 ? 0 : page} de {totalPages}
      </div>

      {oportunidades.length === 0 ? (
        <p className="text-muted text-sm py-8 text-center">
          Nenhuma oportunidade encontrada para os filtros atuais.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="text-left text-xs text-muted uppercase tracking-wide border-b border-border">
                <th className="py-2 px-2">ID</th>
                <SortableHeader label="Score" active={sort === "score"} order={order} onClick={() => onSortChange("score")} />
                <SortableHeader label="Estado" active={sort === "estado"} order={order} onClick={() => onSortChange("estado")} />
                <th className="py-2 px-2">Produto</th>
                <th className="py-2 px-2">Conta</th>
                <th className="py-2 px-2">Vendedor</th>
                <th className="py-2 px-2">Valor</th>
                <th className="py-2 px-2">Estágio</th>
                <SortableHeader label="Idade" active={sort === "age_days"} order={order} onClick={() => onSortChange("age_days")} />
                <SortableHeader label="Confiança" active={sort === "confianca"} order={order} onClick={() => onSortChange("confianca")} />
                <th className="py-2 px-2 sr-only">Detalhe</th>
              </tr>
            </thead>
            <tbody>
              {oportunidades.map((o) => (
                <DealRow
                  key={o.opportunity_id}
                  oportunidade={o}
                  onOpenDetail={onOpenDetail}
                  onNavigateToSobrecarga={onNavigateToSobrecarga}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SortableHeader({
  label,
  active,
  order,
  onClick,
}: {
  label: string;
  active: boolean;
  order: SortOrder;
  onClick: () => void;
}) {
  return (
    <th className="py-2 px-2">
      <button
        type="button"
        onClick={onClick}
        className={"flex items-center gap-1 " + (active ? "text-navy font-bold" : "hover:text-navy")}
      >
        {label}
        {active && <span>{order === "desc" ? "↓" : "↑"}</span>}
      </button>
    </th>
  );
}

function DealRow({
  oportunidade: o,
  onOpenDetail,
  onNavigateToSobrecarga,
}: {
  oportunidade: Oportunidade;
  onOpenDetail: (opportunityId: string) => void;
  onNavigateToSobrecarga?: () => void;
}) {
  return (
    <tr
      className="border-b border-border align-top hover:bg-bg cursor-pointer"
      onClick={() => onOpenDetail(o.opportunity_id)}
    >
      <td className="py-3 px-2 text-muted font-mono text-xs">{o.opportunity_id}</td>
      <td className="py-3 px-2 font-bold text-navy">{o.score.toFixed(1)}</td>
      <td className="py-3 px-2">
        <div className="flex flex-col gap-1 items-start">
          <span className={"text-xs font-semibold px-2 py-0.5 rounded-full border " + ESTADO_BADGE[o.estado]}>
            {o.estado_label}
          </span>
          {o.sobrecarregado && (
            <button
              type="button"
              title="Vendedor sobrecarregado neste estado — ver aba Sobrecarga"
              onClick={(e) => {
                e.stopPropagation();
                onNavigateToSobrecarga?.();
              }}
              className={
                "text-xs font-semibold px-2 py-0.5 rounded-full border " + SOBRECARGA_BADGE_CLASSES
              }
            >
              Sobrecarga
            </button>
          )}
        </div>
      </td>
      <td className="py-3 px-2 font-medium">{o.product}</td>
      <td className="py-3 px-2 text-muted">{o.account ?? "—"}</td>
      <td className="py-3 px-2 text-muted">{o.sales_agent}</td>
      <td className="py-3 px-2 font-medium">{formatUsd(o.preco_tabela)}</td>
      <td className="py-3 px-2 text-muted">{o.deal_stage}</td>
      <td className="py-3 px-2 text-muted">{formatIdade(o.age_days)}</td>
      <td className="py-3 px-2" onClick={(e) => e.stopPropagation()}>
        <ConfidenceBadge
          confianca={o.confianca}
          completude={o.completude}
          suporte={o.suporte}
          razao={o.razao_confianca}
        />
      </td>
      <td className="py-3 px-2">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onOpenDetail(o.opportunity_id);
          }}
          aria-label={`Ver detalhe da oportunidade ${o.opportunity_id}`}
          className="text-navy/50 hover:text-navy bg-transparent border-0 p-0"
        >
          ›
        </button>
      </td>
    </tr>
  );
}
