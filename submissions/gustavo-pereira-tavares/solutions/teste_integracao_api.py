"""
Testes de Integração para API FastAPI
Exemplo de como integrar a API com sistemas externos
"""

import requests
import json
import pandas as pd
from typing import List, Dict

class ClienteAPIChurn:
    """Cliente Python para integração com API de Análise de Churn"""
    
    def __init__(self, url_base: str = "http://localhost:8000"):
        self.url_base = url_base
        self.sessao = requests.Session()
    
    def verificar_saude(self) -> bool:
        """Verifica se a API está operacional"""
        try:
            response = self.sessao.get(f"{self.url_base}/saude", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao verificar saúde: {e}")
            return False
    
    def prever_churn(self, 
                    account_id: int,
                    industry: str,
                    country: str,
                    plan_tier: str,
                    mrr_amount: float,
                    adoption_rate: float,
                    support_quality_score: float,
                    support_ticket_count: int,
                    avg_resolution_time: float,
                    avg_satisfaction_score: float,
                    days_since_signup: int,
                    is_trial: bool = False) -> Dict:
        """
        Faz predição de churn para uma conta
        
        Retorna:
        {
            'account_id': int,
            'probabilidade_churn': float,
            'tier_risco': str,
            'drivers_primarios': List[str],
            'acoes_recomendadas': List[str],
            'confianca_predicao': float
        }
        """
        dados = {
            "account_id": account_id,
            "industry": industry,
            "country": country,
            "plan_tier": plan_tier,
            "mrr_amount": mrr_amount,
            "adoption_rate": adoption_rate,
            "support_quality_score": support_quality_score,
            "support_ticket_count": support_ticket_count,
            "avg_resolution_time": avg_resolution_time,
            "avg_satisfaction_score": avg_satisfaction_score,
            "days_since_signup": days_since_signup,
            "is_trial": is_trial
        }
        
        response = self.sessao.post(
            f"{self.url_base}/api/v1/prever-churn",
            json=dados
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro: {response.status_code} - {response.text}")
            return None
    
    def simular_cenario(self, conta_base: Dict, modificacoes: Dict) -> Dict:
        """
        Simula um cenário what-if
        
        conta_base: Dados originais da conta
        modificacoes: Features a modificar
        """
        dados = {
            "conta_base": conta_base,
            "cenario": modificacoes
        }
        
        response = self.sessao.post(
            f"{self.url_base}/api/v1/simular-cenario",
            json=dados
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro: {response.status_code} - {response.text}")
            return None
    
    def obter_registros_risco(self, tier_risco: str = None, limite: int = 100) -> Dict:
        """
        Obtém registros de risco
        
        tier_risco: 'Critical', 'High', 'Medium', 'Low'
        limite: Número máximo de resultados
        """
        params = {"limite": limite}
        if tier_risco:
            params["tier_risco"] = tier_risco
        
        response = self.sessao.get(
            f"{self.url_base}/api/v1/registros-risco",
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro: {response.status_code}")
            return None
    
    def obter_estatisticas(self) -> Dict:
        """Obtém estatísticas gerais"""
        response = self.sessao.get(f"{self.url_base}/api/v1/estatisticas")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro: {response.status_code}")
            return None
    
    def gerar_relatorio_pdf(self, industry: str = None, caminho_saida: str = "relatorio.pdf"):
        """Gera relatório PDF"""
        params = {}
        if industry:
            params["industry"] = industry
        
        response = self.sessao.get(
            f"{self.url_base}/api/v1/gerar-relatorio",
            params=params
        )
        
        if response.status_code == 200:
            with open(caminho_saida, 'wb') as f:
                f.write(response.content)
            print(f"Relatório salvo em: {caminho_saida}")
            return True
        else:
            print(f"Erro ao gerar relatório: {response.status_code}")
            return False
    
    def processar_arquivo_csv(self, caminho_csv: str) -> List[Dict]:
        """
        Processa arquivo CSV com múltiplas contas
        
        CSV esperado com colunas:
        account_id, industry, country, plan_tier, mrr_amount, adoption_rate,
        support_quality_score, support_ticket_count, avg_resolution_time,
        avg_satisfaction_score, days_since_signup, is_trial
        """
        df = pd.read_csv(caminho_csv)
        resultados = []
        
        for idx, row in df.iterrows():
            print(f"[{idx+1}/{len(df)}] Processando conta {row['account_id']}...", end=" ")
            
            resultado = self.prever_churn(
                account_id=int(row['account_id']),
                industry=str(row['industry']),
                country=str(row['country']),
                plan_tier=str(row['plan_tier']),
                mrr_amount=float(row['mrr_amount']),
                adoption_rate=float(row['adoption_rate']),
                support_quality_score=float(row['support_quality_score']),
                support_ticket_count=int(row['support_ticket_count']),
                avg_resolution_time=float(row['avg_resolution_time']),
                avg_satisfaction_score=float(row['avg_satisfaction_score']),
                days_since_signup=int(row['days_since_signup']),
                is_trial=bool(row.get('is_trial', False))
            )
            
            if resultado:
                resultados.append(resultado)
                print(f"[OK] {resultado['tier_risco']}")
            else:
                print("[ERRO] Erro na predicao")
        
        return resultados
    
    def salvar_resultados(self, resultados: List[Dict], caminho_saida: str = "predicoes.csv"):
        """Salva resultados em CSV"""
        df = pd.DataFrame(resultados)
        df.to_csv(caminho_saida, index=False)
        print(f"\nResultados salvos em: {caminho_saida}")
        
        # Estatísticas
        print(f"\nResumo:")
        print(f"  Total de contas: {len(df)}")
        print(f"  Risco Critico: {len(df[df['tier_risco'] == 'Crítico'])}")
        print(f"  Risco Alto: {len(df[df['tier_risco'] == 'Alto'])}")
        print(f"  Risco Medio: {len(df[df['tier_risco'] == 'Médio'])}")
        print(f"  Risco Baixo: {len(df[df['tier_risco'] == 'Baixo'])}")
        
        return df


# ============================================================
# EXEMPLOS DE USO
# ============================================================

if __name__ == "__main__":
    # Inicializar cliente
    cliente = ClienteAPIChurn("http://localhost:8000")
    
    # Teste 1: Verificar saúde da API
    print("[TESTE 1] Verificando saude da API...")
    if cliente.verificar_saude():
        print("[OK] API esta operacional\n")
    else:
        print("[ERRO] API nao esta respondendo")
        exit(1)
    
    # Teste 2: Prever churn de uma conta individual
    print("[TESTE 2] Predição de churn individual...")
    resultado = cliente.prever_churn(
        account_id=12345,
        industry="FinTech",
        country="BR",
        plan_tier="Pro",
        mrr_amount=5000,
        adoption_rate=35,
        support_quality_score=3.8,
        support_ticket_count=5,
        avg_resolution_time=24,
        avg_satisfaction_score=4.0,
        days_since_signup=180,
        is_trial=False
    )
    
    if resultado:
        print(f"[OK] Conta {resultado['account_id']}")
        print(f"  Probabilidade de Churn: {resultado['probabilidade_churn']:.2%}")
        print(f"  Tier de Risco: {resultado['tier_risco']}")
        print(f"  Drivers: {', '.join(resultado['drivers_primarios'])}")
        print()
    
    # Teste 3: Simular cenário what-if
    print("[TESTE 3] Simulação de cenário (what-if)...")
    conta_original = {
        "account_id": 12345,
        "industry": "FinTech",
        "country": "BR",
        "plan_tier": "Pro",
        "mrr_amount": 5000,
        "adoption_rate": 35,
        "support_quality_score": 3.8,
        "support_ticket_count": 5,
        "avg_resolution_time": 24,
        "avg_satisfaction_score": 4.0,
        "days_since_signup": 180,
        "is_trial": False
    }
    
    cenario = {
        "adoption_rate": 65,  # Aumentar para 65%
        "support_quality_score": 4.5  # Melhorar qualidade
    }
    
    simulacao = cliente.simular_cenario(conta_original, cenario)
    if simulacao:
        print(f"[OK] Simulacao realizada")
        print(f"  Prob original: {simulacao['probabilidade_original']:.2%}")
        print(f"  Prob simulada: {simulacao['probabilidade_simulada']:.2%}")
        print(f"  Mudanca: {simulacao['mudanca_percentual']:+.1f}%")
        print(f"  Novo tier: {simulacao['novo_tier_risco']}")
        print()
    
    # Teste 4: Obter contas em risco crítico
    print("[TESTE 4] Contas em risco critico...")
    registros = cliente.obter_registros_risco(tier_risco="Critical", limite=5)
    if registros:
        print(f"[OK] Total de contas em risco critico: {registros['total']}")
        print(f"  Mostrando primeiras {len(registros['contas'])} contas")
        for conta in registros['contas'][:2]:
            print(f"    - {conta['account_name']}: {conta['churn_probability']:.2%}")
        print()
    
    # Teste 5: Obter estatísticas gerais
    print("[TESTE 5] Estatisticas gerais...")
    stats = cliente.obter_estatisticas()
    if stats:
        print(f"[OK] Estatisticas carregadas")
        print(f"  Total de contas: {stats['total_contas']:,}")
        print(f"  Risco critico: {stats['risco_critico']} contas (${stats['arr_em_risco_critico']:,.0f})")
        print(f"  Risco alto: {stats['risco_alto']} contas (${stats['arr_em_risco_alto']:,.0f})")
        print(f"  Churn medio: {stats['probabilidade_churn_media']:.2%}")
        print()
    
    print("[OK] Todos os testes completados com sucesso!")
    
    # Opcional: Processar arquivo CSV
    # print("[OPCIONAL] Processando arquivo CSV...")
    # resultados = cliente.processar_arquivo_csv("contas.csv")
    # cliente.salvar_resultados(resultados, "predicoes_churn.csv")
