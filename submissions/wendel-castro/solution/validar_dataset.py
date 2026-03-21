"""
Validador de Qualidade de Dados — Data Health Report
Detecta datasets sintéticos, anomalias estatísticas e problemas de qualidade
antes de qualquer análise.

Nasceu de uma experiência real: uma IA processou 52K linhas de dados sintéticos
sem questionar e gerou recomendações baseadas em ruído estatístico.
Este script garante que isso não aconteça de novo.

Wendel Castro | G4 AI Master Challenge | Março 2026
"""

import pandas as pd
import numpy as np
import os
import sys
import re
import json
from datetime import datetime

# =====================================================
# CONFIGURAÇÃO
# =====================================================

# Padrões Faker conhecidos (sufixos de empresas geradas por Faker)
FAKER_COMPANY_SUFFIXES = [
    'LLC', 'Ltd', 'PLC', 'Inc', 'Group', 'and Sons', 'and Daughters',
    '-Smith', '-Johnson', '-Williams', '-Brown', '-Jones', '-Garcia',
    '-Miller', '-Davis', '-Rodriguez', '-Martinez'
]

# Limiar para considerar correlação como "suspeitamente baixa"
CORRELATION_THRESHOLD = 0.05

# Limiar para coeficiente de variação (CV) suspeitamente baixo
CV_THRESHOLD = 0.05

# Limiar para uniformidade de distribuição categórica
UNIFORMITY_THRESHOLD = 0.03  # desvio máximo de 3% da distribuição perfeita


class DataHealthReport:
    """Gera um relatório de saúde do dataset com score de confiabilidade."""

    def __init__(self, df, dataset_name="Dataset"):
        self.df = df
        self.dataset_name = dataset_name
        self.findings = []  # Lista de (severidade, categoria, mensagem)
        self.score = 100  # Começa perfeito, perde pontos por problema

    # -------------------------------------------------
    # TESTE 1: Variância e Distribuição Numérica
    # -------------------------------------------------
    def check_numeric_variance(self):
        """Detecta colunas numéricas com variância suspeitamente baixa."""
        print("  [1/7] Verificando variância numérica...")
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = self.df[col].dropna()
            if len(series) < 10:
                continue

            mean = series.mean()
            std = series.std()
            data_range = series.max() - series.min()

            # Coeficiente de variação
            if mean != 0:
                cv = std / abs(mean)
            else:
                cv = 0

            # CV muito baixo = dados uniformes demais
            if cv < CV_THRESHOLD and len(series) > 100:
                self.findings.append((
                    'CRITICO',
                    'VARIANCIA',
                    f'Coluna "{col}": CV={cv:.4f} (muito baixo). '
                    f'Média={mean:.2f}, Std={std:.2f}, Range={data_range:.2f}. '
                    f'Em {len(series)} registros, a variação é suspeitamente pequena.'
                ))
                self.score -= 15

            # Range muito pequeno relativo à média
            if mean != 0 and data_range / abs(mean) < 0.1 and len(series) > 100:
                self.findings.append((
                    'ALERTA',
                    'RANGE',
                    f'Coluna "{col}": Range de apenas {data_range:.2f} '
                    f'para média de {mean:.2f} ({data_range/abs(mean)*100:.1f}% da média). '
                    f'Dados reais costumam ter range muito maior.'
                ))
                self.score -= 5

            # Verificar se parece distribuição uniforme (sem outliers)
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            outliers = ((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum()
            outlier_pct = outliers / len(series)

            if outlier_pct == 0 and len(series) > 1000:
                self.findings.append((
                    'ALERTA',
                    'OUTLIERS',
                    f'Coluna "{col}": ZERO outliers em {len(series)} registros. '
                    f'Dados reais quase sempre têm outliers.'
                ))
                self.score -= 3

    # -------------------------------------------------
    # TESTE 2: Correlações entre métricas relacionadas
    # -------------------------------------------------
    def check_correlations(self):
        """Detecta ausência de correlação entre métricas que deveriam correlacionar."""
        print("  [2/7] Verificando correlações entre métricas...")
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) < 2:
            return

        # Calcular matriz de correlação
        corr_matrix = self.df[numeric_cols].corr()

        # Pares que tipicamente correlacionam em dados reais
        engagement_keywords = ['view', 'like', 'share', 'comment', 'click',
                               'impression', 'reach', 'engagement', 'follower',
                               'subscriber', 'reaction']

        engagement_cols = [c for c in numeric_cols
                           if any(kw in c.lower() for kw in engagement_keywords)]

        if len(engagement_cols) >= 2:
            low_corr_pairs = []
            for i, col1 in enumerate(engagement_cols):
                for col2 in engagement_cols[i+1:]:
                    corr = abs(corr_matrix.loc[col1, col2])
                    if corr < CORRELATION_THRESHOLD:
                        low_corr_pairs.append((col1, col2, corr))

            if low_corr_pairs:
                pairs_str = "; ".join(
                    [f'{c1} x {c2} = {c:.4f}' for c1, c2, c in low_corr_pairs[:5]]
                )
                self.findings.append((
                    'CRITICO',
                    'CORRELACAO',
                    f'Métricas de engajamento com correlação ~0: {pairs_str}. '
                    f'Em dados reais, views e likes tipicamente correlacionam >0.5.'
                ))
                self.score -= 20

        # Verificar se TODAS as correlações são baixas
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        all_corrs = upper_triangle.stack().abs()
        if len(all_corrs) > 3 and all_corrs.mean() < CORRELATION_THRESHOLD:
            self.findings.append((
                'CRITICO',
                'CORRELACAO_GERAL',
                f'Correlação média entre TODAS as variáveis numéricas: '
                f'{all_corrs.mean():.4f}. Isso é estatisticamente improvável '
                f'em dados reais com {len(self.df)} registros.'
            ))
            self.score -= 15

    # -------------------------------------------------
    # TESTE 3: Distribuição Categórica (uniformidade)
    # -------------------------------------------------
    def check_categorical_distribution(self):
        """Detecta distribuições categóricas uniformes demais."""
        print("  [3/7] Verificando distribuições categóricas...")
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns

        for col in cat_cols:
            value_counts = self.df[col].value_counts(normalize=True)
            n_categories = len(value_counts)

            if n_categories < 2 or n_categories > 50:
                continue

            # Distribuição perfeita seria 1/n para cada categoria
            expected_pct = 1.0 / n_categories
            max_deviation = (value_counts - expected_pct).abs().max()

            if max_deviation < UNIFORMITY_THRESHOLD and n_categories >= 3:
                self.findings.append((
                    'ALERTA',
                    'UNIFORMIDADE',
                    f'Coluna "{col}": {n_categories} categorias com distribuição '
                    f'quase perfeita (desvio máximo: {max_deviation:.4f}). '
                    f'Valores: {", ".join(f"{k}: {v:.4f}" for k, v in value_counts.items())}. '
                    f'Dados reais raramente são tão uniformes.'
                ))
                self.score -= 8

    # -------------------------------------------------
    # TESTE 4: Padrões de dados gerados (Faker, etc.)
    # -------------------------------------------------
    def check_faker_patterns(self):
        """Detecta padrões típicos de bibliotecas de geração de dados."""
        print("  [4/7] Verificando padrões de dados gerados (Faker)...")
        text_cols = self.df.select_dtypes(include=['object']).columns

        for col in text_cols:
            sample = self.df[col].dropna().head(500)

            if len(sample) == 0:
                continue

            # Verificar sufixos de empresas Faker
            faker_matches = 0
            for val in sample:
                val_str = str(val)
                if any(suffix in val_str for suffix in FAKER_COMPANY_SUFFIXES):
                    faker_matches += 1

            if faker_matches > len(sample) * 0.1:
                self.findings.append((
                    'CRITICO',
                    'FAKER',
                    f'Coluna "{col}": {faker_matches}/{len(sample)} valores '
                    f'contêm padrões típicos de Faker (LLC, Ltd, PLC, Inc, etc.). '
                    f'Alta probabilidade de dados gerados por biblioteca.'
                ))
                self.score -= 15

            # Verificar lorem ipsum
            lorem_count = sum(1 for val in sample
                              if 'lorem' in str(val).lower()
                              or 'ipsum' in str(val).lower()
                              or 'dolor sit' in str(val).lower())
            if lorem_count > 0:
                self.findings.append((
                    'CRITICO',
                    'LOREM_IPSUM',
                    f'Coluna "{col}": {lorem_count} valores contêm Lorem Ipsum. '
                    f'Dados definitivamente sintéticos.'
                ))
                self.score -= 20

    # -------------------------------------------------
    # TESTE 5: Integridade e Consistência
    # -------------------------------------------------
    def check_data_integrity(self):
        """Verifica problemas de integridade dos dados."""
        print("  [5/7] Verificando integridade dos dados...")

        # Valores nulos
        null_pcts = (self.df.isnull().sum() / len(self.df) * 100)
        high_null = null_pcts[null_pcts > 50]
        if len(high_null) > 0:
            cols_str = ", ".join([f'{c} ({v:.0f}%)' for c, v in high_null.items()])
            self.findings.append((
                'ALERTA',
                'NULOS',
                f'Colunas com >50% nulos: {cols_str}. '
                f'Considere se essas colunas são confiáveis para análise.'
            ))
            self.score -= 3

        # Duplicatas exatas
        n_dupes = self.df.duplicated().sum()
        if n_dupes > 0:
            dupe_pct = n_dupes / len(self.df) * 100
            self.findings.append((
                'ALERTA' if dupe_pct < 5 else 'CRITICO',
                'DUPLICATAS',
                f'{n_dupes} linhas duplicadas ({dupe_pct:.1f}%). '
                f'Verificar se são duplicatas reais ou erro de coleta.'
            ))
            self.score -= min(10, int(dupe_pct))

        # IDs únicos
        for col in self.df.columns:
            if 'id' in col.lower() and self.df[col].dtype in ['int64', 'object']:
                n_unique = self.df[col].nunique()
                if n_unique == len(self.df):
                    continue  # OK, IDs únicos
                elif n_unique < len(self.df) * 0.9:
                    self.findings.append((
                        'INFO',
                        'IDS',
                        f'Coluna "{col}" parece ser ID mas tem apenas '
                        f'{n_unique}/{len(self.df)} valores únicos.'
                    ))

    # -------------------------------------------------
    # TESTE 6: Análise Temporal
    # -------------------------------------------------
    def check_temporal_patterns(self):
        """Verifica padrões temporais suspeitos."""
        print("  [6/7] Verificando padrões temporais...")
        date_cols = self.df.select_dtypes(include=['datetime64']).columns

        # Tentar converter colunas que parecem datas
        for col in self.df.columns:
            if any(kw in col.lower() for kw in ['date', 'time', 'created', 'posted']):
                if col not in date_cols:
                    try:
                        self.df[col] = pd.to_datetime(self.df[col], format='mixed')
                        date_cols = self.df.select_dtypes(include=['datetime64']).columns
                    except (ValueError, TypeError):
                        pass

        for col in date_cols:
            series = self.df[col].dropna()
            if len(series) < 100:
                continue

            # Verificar distribuição por dia da semana
            dow_dist = series.dt.dayofweek.value_counts(normalize=True)
            expected = 1.0 / 7
            max_dow_dev = (dow_dist - expected).abs().max()

            if max_dow_dev < 0.02:
                self.findings.append((
                    'ALERTA',
                    'TEMPORAL',
                    f'Coluna "{col}": distribuição por dia da semana é quase '
                    f'perfeitamente uniforme (desvio máximo: {max_dow_dev:.4f}). '
                    f'Dados reais mostram padrões de dias úteis vs fins de semana.'
                ))
                self.score -= 5

            # Verificar distribuição por hora (se disponível)
            if series.dt.hour.nunique() > 1:
                hour_dist = series.dt.hour.value_counts(normalize=True)
                expected_hour = 1.0 / hour_dist.index.nunique()
                max_hour_dev = (hour_dist - expected_hour).abs().max()

                if max_hour_dev < 0.02 and hour_dist.index.nunique() >= 12:
                    self.findings.append((
                        'ALERTA',
                        'TEMPORAL_HORA',
                        f'Coluna "{col}": distribuição por hora uniforme demais. '
                        f'Dados reais têm picos e vales claros.'
                    ))
                    self.score -= 3

    # -------------------------------------------------
    # TESTE 7: Consistência entre colunas
    # -------------------------------------------------
    def check_cross_column_consistency(self):
        """Verifica se relações lógicas entre colunas fazem sentido."""
        print("  [7/7] Verificando consistência entre colunas...")
        cols_lower = {c.lower(): c for c in self.df.columns}

        # Verificar se views > likes (faz sentido na maioria dos contextos)
        view_cols = [c for c in self.df.columns if 'view' in c.lower()]
        like_cols = [c for c in self.df.columns if 'like' in c.lower()]

        if view_cols and like_cols:
            view_col = view_cols[0]
            like_col = like_cols[0]
            anomaly = (self.df[like_col] > self.df[view_col]).sum()
            if anomaly > 0:
                pct = anomaly / len(self.df) * 100
                self.findings.append((
                    'ALERTA' if pct < 5 else 'CRITICO',
                    'LOGICA',
                    f'{anomaly} posts ({pct:.1f}%) onde likes > views. '
                    f'Isso é fisicamente impossível na maioria das plataformas.'
                ))
                self.score -= min(10, int(pct))

        # Verificar follower_count = 0 com alto engagement
        follower_cols = [c for c in self.df.columns if 'follower' in c.lower()]
        if follower_cols:
            fc = follower_cols[0]
            zero_followers = self.df[self.df[fc] == 0]
            if len(zero_followers) > len(self.df) * 0.01:
                self.findings.append((
                    'INFO',
                    'SEGUIDORES',
                    f'{len(zero_followers)} registros com 0 seguidores '
                    f'({len(zero_followers)/len(self.df)*100:.1f}%). '
                    f'Verificar se são contas deletadas ou erro de coleta.'
                ))

    # -------------------------------------------------
    # GERAR RELATÓRIO
    # -------------------------------------------------
    def run_all_checks(self):
        """Executa todos os testes e retorna o relatório."""
        print(f"\n{'='*60}")
        print(f"  VALIDAÇÃO DE QUALIDADE — {self.dataset_name}")
        print(f"  {len(self.df)} registros | {self.df.shape[1]} colunas")
        print(f"{'='*60}\n")

        self.check_numeric_variance()
        self.check_correlations()
        self.check_categorical_distribution()
        self.check_faker_patterns()
        self.check_data_integrity()
        self.check_temporal_patterns()
        self.check_cross_column_consistency()

        # Garantir score entre 0 e 100
        self.score = max(0, min(100, self.score))

        return self.generate_report()

    def get_verdict(self):
        """Retorna o veredito baseado no score."""
        if self.score >= 80:
            return "SAUDAVEL", "Dataset aparenta ser confiável para análise."
        elif self.score >= 60:
            return "ATENCAO", "Dataset tem problemas que merecem investigação antes de analisar."
        elif self.score >= 40:
            return "SUSPEITO", "Dataset tem sinais fortes de problemas. Investigar antes de prosseguir."
        else:
            return "SINTETICO/COMPROMETIDO", "Dataset muito provavelmente é sintético ou tem problemas graves."

    def generate_report(self):
        """Gera o relatório formatado."""
        verdict, verdict_desc = self.get_verdict()

        # Agrupar findings por severidade
        criticos = [f for f in self.findings if f[0] == 'CRITICO']
        alertas = [f for f in self.findings if f[0] == 'ALERTA']
        infos = [f for f in self.findings if f[0] == 'INFO']

        report_lines = []
        report_lines.append(f"# Data Health Report — {self.dataset_name}")
        report_lines.append(f"*Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

        # Score visual
        report_lines.append("## Score de Confiabilidade\n")
        bar_filled = int(self.score / 5)
        bar_empty = 20 - bar_filled
        bar = '█' * bar_filled + '░' * bar_empty
        report_lines.append(f"```")
        report_lines.append(f"  [{bar}] {self.score}/100")
        report_lines.append(f"  Veredito: {verdict}")
        report_lines.append(f"```\n")
        report_lines.append(f"**{verdict_desc}**\n")

        # Resumo do dataset
        report_lines.append("## Resumo do Dataset\n")
        report_lines.append(f"| Métrica | Valor |")
        report_lines.append(f"|---------|-------|")
        report_lines.append(f"| Registros | {len(self.df):,} |")
        report_lines.append(f"| Colunas | {self.df.shape[1]} |")
        report_lines.append(f"| Colunas numéricas | {len(self.df.select_dtypes(include=[np.number]).columns)} |")
        report_lines.append(f"| Colunas texto | {len(self.df.select_dtypes(include=['object']).columns)} |")
        report_lines.append(f"| Valores nulos (total) | {self.df.isnull().sum().sum():,} ({self.df.isnull().sum().sum()/self.df.size*100:.1f}%) |")
        report_lines.append(f"| Linhas duplicadas | {self.df.duplicated().sum():,} |")
        report_lines.append("")

        # Findings
        if criticos:
            report_lines.append("## Problemas Críticos\n")
            for sev, cat, msg in criticos:
                report_lines.append(f"- **[{cat}]** {msg}\n")

        if alertas:
            report_lines.append("## Alertas\n")
            for sev, cat, msg in alertas:
                report_lines.append(f"- **[{cat}]** {msg}\n")

        if infos:
            report_lines.append("## Informações\n")
            for sev, cat, msg in infos:
                report_lines.append(f"- **[{cat}]** {msg}\n")

        if not self.findings:
            report_lines.append("## Resultado\n")
            report_lines.append("Nenhum problema detectado. Dataset parece saudável.\n")

        # Recomendação
        report_lines.append("## Recomendação\n")
        if self.score < 40:
            report_lines.append(
                "**NÃO prossiga com análise sem investigar.** Os dados apresentam "
                "sinais consistentes de geração sintética. Qualquer insight extraído "
                "será baseado em ruído estatístico, não em padrões reais. "
                "Recomendação: validar a origem dos dados antes de investir tempo em análise.\n"
            )
        elif self.score < 60:
            report_lines.append(
                "**Investigue antes de analisar.** Os dados têm anomalias que podem "
                "comprometer suas conclusões. Valide a origem e o processo de coleta "
                "antes de tomar decisões baseadas nestes dados.\n"
            )
        elif self.score < 80:
            report_lines.append(
                "**Prossiga com cautela.** Alguns alertas merecem atenção, mas o "
                "dataset parece utilizável. Documente as limitações encontradas "
                "em qualquer relatório derivado.\n"
            )
        else:
            report_lines.append(
                "**Dataset aparenta ser confiável.** Nenhum sinal significativo "
                "de dados sintéticos ou problemas de qualidade. Prossiga com a análise.\n"
            )

        report_text = "\n".join(report_lines)

        # Print no terminal
        print(f"\n{'='*60}")
        print(f"  RESULTADO DA VALIDAÇÃO")
        print(f"{'='*60}")
        print(f"\n  Score: {self.score}/100 — {verdict}")
        print(f"  {verdict_desc}\n")

        if criticos:
            print(f"  Problemas críticos: {len(criticos)}")
        if alertas:
            print(f"  Alertas: {len(alertas)}")
        if infos:
            print(f"  Informações: {len(infos)}")

        print(f"\n{'='*60}\n")

        return report_text, self.score, verdict


# =====================================================
# EXECUÇÃO STANDALONE
# =====================================================

def validate_file(file_path, output_dir=None):
    """Valida um arquivo CSV/Excel e gera o relatório."""
    if not os.path.exists(file_path):
        print(f"Erro: arquivo não encontrado: {file_path}")
        sys.exit(1)

    # Carregar dados
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif ext == '.json':
        df = pd.read_json(file_path)
    elif ext == '.parquet':
        df = pd.read_parquet(file_path)
    else:
        print(f"Erro: formato não suportado: {ext}")
        print("Formatos aceitos: .csv, .xlsx, .xls, .json, .parquet")
        sys.exit(1)

    dataset_name = os.path.basename(file_path)

    # Tentar converter colunas de data
    for col in df.columns:
        if any(kw in col.lower() for kw in ['date', 'time', 'created', 'posted', 'updated']):
            try:
                df[col] = pd.to_datetime(df[col], format='mixed')
            except (ValueError, TypeError):
                pass

    # Rodar validação
    validator = DataHealthReport(df, dataset_name)
    report_text, score, verdict = validator.run_all_checks()

    # Salvar relatório
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(file_path))

    report_path = os.path.join(output_dir, 'data_health_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"Relatório salvo em: {report_path}")

    return score, verdict


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python validar_dataset.py <caminho-do-arquivo>")
        print("")
        print("Formatos aceitos: .csv, .xlsx, .xls, .json, .parquet")
        print("")
        print("Exemplo:")
        print("  python validar_dataset.py dataset/social_media_dataset.csv")
        sys.exit(1)

    file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    score, verdict = validate_file(file_path, output_dir)

    # Exit code baseado no score (útil para CI/CD)
    if score < 40:
        sys.exit(2)  # Dados comprometidos
    elif score < 60:
        sys.exit(1)  # Dados suspeitos
    else:
        sys.exit(0)  # Dados OK
