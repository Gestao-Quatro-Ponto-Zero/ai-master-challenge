#!/usr/bin/env python3
"""
CLI & HTML Report Generator - Lead Scorer
Gera relatórios executivos e operacionais priorizados com Explainability completa.
"""

import sys
import argparse
import json
from pathlib import Path
import pandas as pd
from scoring_engine import load_and_prepare_data, score_pipeline

def generate_html_report(scored_df: pd.DataFrame, output_file: Path, filter_agent: str = None, filter_office: str = None):
    filtered_df = scored_df.copy()
    if filter_agent and filter_agent != "Todos":
        filtered_df = filtered_df[filtered_df['sales_agent'] == filter_agent]
    if filter_office and filter_office != "Todas":
        filtered_df = filtered_df[filtered_df['regional_office'] == filter_office]

    # Prepara dados para JSON embutido na aplicação web
    records = []
    for _, r in filtered_df.iterrows():
        records.append({
            'id': str(r['opportunity_id']),
            'agent': str(r['sales_agent']),
            'manager': str(r['manager']),
            'office': str(r['regional_office']),
            'account': str(r['account']) if pd.notnull(r['account']) else "— (Sem conta cadastrada)",
            'sector': str(r['sector']) if pd.notnull(r['sector']) else "Não informado",
            'product': str(r['product_clean']),
            'price': float(r['sales_price']) if pd.notnull(r['sales_price']) else 0.0,
            'stage': str(r['deal_stage']),
            'days': int(r['days_in_pipeline']),
            'score': int(r['score']),
            'tier': str(r['tier']),
            'expected_value': float(r['expected_value']),
            'positives': r['reasons_positive'],
            'negatives': r['reasons_negative'],
            'alerts': r['alerts'],
            'action': str(r['recommended_action'])
        })

    total_opps = len(records)
    high_count = sum(1 for x in records if x['tier'] == 'Prioridade Alta')
    med_count = sum(1 for x in records if x['tier'] == 'Prioridade Média')
    low_count = sum(1 for x in records if x['tier'] == 'Prioridade Baixa')
    risk_count = sum(1 for x in records if x['tier'] == 'Em Risco')
    total_pipeline_val = sum(x['price'] for x in records)
    total_expected_val = sum(x['expected_value'] for x in records)

    agents = sorted(list(set(scored_df['sales_agent'].dropna().unique())))
    offices = sorted(list(set(scored_df['regional_office'].dropna().unique())))

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>G4 AI Master — Lead Scorer & Prioritization Hub</title>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --high-color: #22c55e;
            --med-color: #eab308;
            --risk-color: #ef4444;
            --low-color: #64748b;
            --border-color: #334155;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ background-color: var(--bg-primary); color: var(--text-primary); padding: 24px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid var(--border-color); padding-bottom: 16px; }}
        .header h1 {{ font-size: 24px; font-weight: 700; color: #fff; }}
        .header .subtitle {{ color: var(--text-secondary); font-size: 14px; margin-top: 4px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .kpi-card {{ background-color: var(--bg-card); padding: 18px; border-radius: 10px; border: 1px solid var(--border-color); }}
        .kpi-label {{ font-size: 12px; text-transform: uppercase; color: var(--text-secondary); font-weight: 600; letter-spacing: 0.5px; }}
        .kpi-value {{ font-size: 26px; font-weight: 700; margin-top: 8px; }}
        .kpi-desc {{ font-size: 11px; color: var(--text-secondary); margin-top: 4px; }}
        .filters {{ background-color: var(--bg-card); padding: 16px 20px; border-radius: 10px; border: 1px solid var(--border-color); margin-bottom: 24px; display: flex; flex-wrap: wrap; gap: 16px; align-items: center; }}
        .filter-group {{ display: flex; flex-direction: column; gap: 6px; }}
        .filter-group label {{ font-size: 12px; font-weight: 600; color: var(--text-secondary); }}
        select, input {{ background: #0f172a; border: 1px solid var(--border-color); color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 14px; outline: none; }}
        select:focus, input:focus {{ border-color: var(--accent); }}
        .table-container {{ background-color: var(--bg-card); border-radius: 10px; border: 1px solid var(--border-color); overflow: hidden; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }}
        th {{ background-color: #172033; color: var(--text-secondary); padding: 12px 14px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color); }}
        td {{ padding: 14px; border-bottom: 1px solid var(--border-color); vertical-align: top; }}
        tr:hover {{ background-color: rgba(255,255,255,0.02); }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }}
        .badge-high {{ background-color: rgba(34, 197, 94, 0.15); color: var(--high-color); border: 1px solid rgba(34,197,94,0.3); }}
        .badge-med {{ background-color: rgba(234, 179, 8, 0.15); color: var(--med-color); border: 1px solid rgba(234,179,8,0.3); }}
        .badge-risk {{ background-color: rgba(239, 68, 68, 0.15); color: var(--risk-color); border: 1px solid rgba(239,68,68,0.3); }}
        .badge-low {{ background-color: rgba(100, 116, 139, 0.15); color: var(--low-color); border: 1px solid rgba(100,116,139,0.3); }}
        .score-box {{ font-size: 16px; font-weight: 800; display: flex; align-items: center; gap: 8px; }}
        .action-box {{ background: #0f172a; padding: 8px 10px; border-radius: 6px; font-size: 12px; border-left: 3px solid var(--accent); margin-top: 6px; }}
        .explain-tag {{ font-size: 11px; margin-top: 4px; line-height: 1.4; }}
        .pos-tag {{ color: #4ade80; }}
        .neg-tag {{ color: #f87171; }}
        .alert-pill {{ display: inline-block; background: rgba(239,68,68,0.2); color: #fca5a5; font-size: 10px; padding: 2px 6px; border-radius: 3px; margin-top: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>G4 AI Master — Lead Scorer & Prioritization Hub</h1>
            <div class="subtitle">RevOps Intelligent Deal Scoring — Solução Funcional com Explainability e Priorização em Tempo Real</div>
        </div>
        <div>
            <span style="font-size: 12px; color: var(--text-secondary); background: var(--bg-card); padding: 8px 14px; border-radius: 6px; border: 1px solid var(--border-color);">
                Dataset: <strong>8.800 Oportunidades</strong> | Pipeline Ativo: <strong id="header-active-count">{total_opps}</strong>
            </span>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Prioridade Alta</div>
            <div class="kpi-value" style="color: var(--high-color);" id="kpi-high">{high_count}</div>
            <div class="kpi-desc">Foco de fechamento imediato</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Prioridade Média</div>
            <div class="kpi-value" style="color: var(--med-color);" id="kpi-med">{med_count}</div>
            <div class="kpi-desc">Qualificação e avanço</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Oportunidades em Risco</div>
            <div class="kpi-value" style="color: var(--risk-color);" id="kpi-risk">{risk_count}</div>
            <div class="kpi-desc">>90 dias / risco de estagnação</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Pipeline Bruto Ativo</div>
            <div class="kpi-value" style="color: var(--accent);" id="kpi-pipeline">${total_pipeline_val:,.0f}</div>
            <div class="kpi-desc">Valor de catálogo total</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Receita Ponderada (EV)</div>
            <div class="kpi-value" style="color: #38bdf8;" id="kpi-ev">${total_expected_val:,.0f}</div>
            <div class="kpi-desc">Expectativa real ponderada</div>
        </div>
    </div>

    <div class="filters">
        <div class="filter-group">
            <label>Filtrar por Vendedor</label>
            <select id="agentSelect" onchange="applyFilters()">
                <option value="Todos">Todos os Vendedores ({len(agents)})</option>
                {"".join([f'<option value="{a}">{a}</option>' for a in agents])}
            </select>
        </div>
        <div class="filter-group">
            <label>Filtrar por Região</label>
            <select id="officeSelect" onchange="applyFilters()">
                <option value="Todas">Todas as Regiões</option>
                {"".join([f'<option value="{o}">{o}</option>' for o in offices])}
            </select>
        </div>
        <div class="filter-group">
            <label>Filtrar por Tier</label>
            <select id="tierSelect" onchange="applyFilters()">
                <option value="Todos">Todos os Tiers</option>
                <option value="Prioridade Alta">Prioridade Alta</option>
                <option value="Prioridade Média">Prioridade Média</option>
                <option value="Em Risco">Em Risco</option>
                <option value="Prioridade Baixa">Prioridade Baixa</option>
            </select>
        </div>
        <div class="filter-group">
            <label>Buscar Oportunidade / Conta</label>
            <input type="text" id="searchInput" placeholder="Nome da conta ou ID..." oninput="applyFilters()" style="min-width: 200px;">
        </div>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th style="width: 80px;">Score</th>
                    <th style="width: 120px;">Prioridade</th>
                    <th style="width: 200px;">Deal / Conta</th>
                    <th style="width: 150px;">Vendedor & Região</th>
                    <th style="width: 140px;">Produto & Valor</th>
                    <th style="width: 100px;">Estágio & Idade</th>
                    <th>Explainability (Por Que Este Score?) & Próximo Passo</th>
                </tr>
            </thead>
            <tbody id="dealsTableBody">
                <!-- Preenchido via JavaScript -->
            </tbody>
        </table>
    </div>

    <script>
        const rawData = {json.dumps(records, ensure_ascii=False)};

        function formatCurrency(val) {{
            return '$' + Math.round(val).toLocaleString('en-US');
        }}

        function getTierBadge(tier) {{
            if (tier === 'Prioridade Alta') return '<span class="badge badge-high">Alta</span>';
            if (tier === 'Prioridade Média') return '<span class="badge badge-med">Média</span>';
            if (tier === 'Em Risco') return '<span class="badge badge-risk">Em Risco</span>';
            return '<span class="badge badge-low">Baixa</span>';
        }}

        function renderRows(items) {{
            const tbody = document.getElementById('dealsTableBody');
            if (items.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 40px; color: var(--text-secondary);">Nenhuma oportunidade encontrada com os filtros selecionados.</td></tr>';
                return;
            }}

            tbody.innerHTML = items.map(d => `
                <tr>
                    <td>
                        <div class="score-box" style="color: ${{d.score >= 70 ? 'var(--high-color)' : (d.score >= 50 ? 'var(--med-color)' : 'var(--risk-color)')}}">
                            ${{d.score}}
                        </div>
                        <div style="font-size: 10px; color: var(--text-secondary); margin-top:2px;">EV: ${{formatCurrency(d.expected_value)}}</div>
                    </td>
                    <td>${{getTierBadge(d.tier)}}</td>
                    <td>
                        <strong style="color: #fff; font-size: 14px;">${{d.account}}</strong>
                        <div style="font-size: 11px; color: var(--text-secondary); margin-top: 2px;">ID: ${{d.id}} | Setor: ${{d.sector}}</div>
                    </td>
                    <td>
                        <div>${{d.agent}}</div>
                        <div style="font-size: 11px; color: var(--text-secondary);">${{d.office}} (Mgr: ${{d.manager}})</div>
                    </td>
                    <td>
                        <div style="font-weight: 600;">${{d.product}}</div>
                        <div style="font-size: 12px; color: var(--accent); font-weight: 600;">${{formatCurrency(d.price)}}</div>
                    </td>
                    <td>
                        <div style="font-size: 12px;">${{d.stage}}</div>
                        <div style="font-size: 11px; color: ${{d.days > 90 ? 'var(--risk-color)' : 'var(--text-secondary)'}};">${{d.days}} dias</div>
                        ${{d.alerts.map(a => `<div class="alert-pill">⚠️ ${{a}}</div>`).join('')}}
                    </td>
                    <td>
                        <div class="explain-tag pos-tag">▲ ${{d.positives.join(' • ')}}</div>
                        ${{d.negatives.length > 0 ? `<div class="explain-tag neg-tag">▼ ${{d.negatives.join(' • ')}}</div>` : ''}}
                        <div class="action-box"><strong>Próximo Passo Recomendado:</strong> ${{d.action}}</div>
                    </td>
                </tr>
            `).join('');
        }}

        function applyFilters() {{
            const agent = document.getElementById('agentSelect').value;
            const office = document.getElementById('officeSelect').value;
            const tier = document.getElementById('tierSelect').value;
            const search = document.getElementById('searchInput').value.toLowerCase().trim();

            const filtered = rawData.filter(d => {{
                if (agent !== 'Todos' && d.agent !== agent) return false;
                if (office !== 'Todas' && d.office !== office) return false;
                if (tier !== 'Todos' && d.tier !== tier) return false;
                if (search && !d.account.toLowerCase().includes(search) && !d.id.toLowerCase().includes(search) && !d.agent.toLowerCase().includes(search)) return false;
                return true;
            }});

            // Ordena por Score decrescente
            filtered.sort((a, b) => b.score - a.score || b.price - a.price);

            // Atualiza KPIs
            document.getElementById('header-active-count').innerText = filtered.length;
            document.getElementById('kpi-high').innerText = filtered.filter(x => x.tier === 'Prioridade Alta').length;
            document.getElementById('kpi-med').innerText = filtered.filter(x => x.tier === 'Prioridade Média').length;
            document.getElementById('kpi-risk').innerText = filtered.filter(x => x.tier === 'Em Risco').length;

            const totalVal = filtered.reduce((acc, curr) => acc + curr.price, 0);
            const evVal = filtered.reduce((acc, curr) => acc + curr.expected_value, 0);
            document.getElementById('kpi-pipeline').innerText = formatCurrency(totalVal);
            document.getElementById('kpi-ev').innerText = formatCurrency(evVal);

            renderRows(filtered);
        }}

        // Inicialização
        applyFilters();
    </script>
</body>
</html>
"""
    output_file.write_text(html_content, encoding="utf-8")
    print(f"Relatório Interativo gerado com sucesso em: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Lead Scorer CLI & Report Generator — Case 003 G4 AI Master")
    parser.add_argument("--agent", type=str, default="Todos", help="Filtrar por vendedor")
    parser.add_argument("--office", type=str, default="Todas", help="Filtrar por regional office")
    parser.add_argument("--top", type=int, default=10, help="Quantidade de oportunidades no ranking de console")
    parser.add_argument("--export-html", type=str, default=None, help="Caminho do arquivo HTML a ser gerado")
    parser.add_argument("--export-csv", type=str, default=None, help="Caminho do CSV de saída com scores")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"

    print("================================================================")
    print("   G4 AI Master — Lead Scorer & Prioritization Engine (Case 003)")
    print("================================================================")
    print(f"Carregando e integrando dados do CRM em: {data_dir}")
    df, benchmarks = load_and_prepare_data(data_dir)

    active = df[df['deal_stage'].isin(['Prospecting', 'Engaging'])].copy()
    print(f"Processando scoring para {len(active)} oportunidades ativas no pipeline...")
    scored = score_pipeline(active, benchmarks)

    # Filtros
    filtered = scored.copy()
    if args.agent != "Todos":
        filtered = filtered[filtered['sales_agent'] == args.agent]
    if args.office != "Todas":
        filtered = filtered[filtered['regional_office'] == args.office]

    filtered = filtered.sort_values(by=['score', 'sales_price'], ascending=[False, False])

    print(f"\nResumo da Priorização ({len(filtered)} oportunidades):")
    print(filtered['tier'].value_counts())

    print(f"\n--- TOP {min(args.top, len(filtered))} OPORTUNIDADES PARA ATUAÇÃO IMEDIATA ---")
    for i, (_, row) in enumerate(filtered.head(args.top).iterrows(), 1):
        acct = row['account'] if pd.notnull(row['account']) else "[Sem Conta Associada]"
        print(f"\n#{i:02d} [{row['tier'].upper()}] - Score: {row['score']}/100 | EV: ${row['expected_value']:,.0f}")
        print(f"     Oportunidade: {row['opportunity_id']} | Conta: {acct} ({row['sector']})")
        print(f"     Vendedor: {row['sales_agent']} ({row['regional_office']}) | Produto: {row['product_clean']} (${row['sales_price']:,.0f})")
        print(f"     Estágio: {row['deal_stage']} | Idade no Pipeline: {row['days_in_pipeline']} dias")
        print(f"     Explainability: {row['explainability_text']}")
        print(f"     Ação Recomendada: {row['recommended_action']}")

    # Exportações
    html_out = Path(args.export_html) if args.export_html else base_dir / "lead_scorer_dashboard.html"
    generate_html_report(scored, html_out, args.agent, args.office)

    if args.export_csv:
        csv_path = Path(args.export_csv)
        scored.to_csv(csv_path, index=False)
        print(f"Arquivo CSV exportado com sucesso: {csv_path}")

if __name__ == "__main__":
    main()
