from fastapi import APIRouter
from core.scorer import get_scored_pipeline

router = APIRouter()

@router.get("/deals")
def get_deals(agent: str = None):
    deals = get_scored_pipeline(agent_name=agent)
    return {"deals": deals}

@router.get("/dashboard")
def get_dashboard_metrics(agent: str = None):
    deals = get_scored_pipeline(agent_name=agent)
    
    total_esperado = sum([d.get('valor_esperado', 0) * (d.get('pontuacao', 0) / 100) for d in deals])
    total_bruto = sum([d.get('valor_esperado', 0) for d in deals])
    
    estagnados = sum(1 for d in deals if "🚨 ESTAGNADO" in d.get('tags', []))
    sem_resposta = sum(1 for d in deals if "🚨 SEM RESPOSTA" in d.get('tags', []))
    sinais_quentes = sum(1 for d in deals if "🔥 SINAL QUENTE" in d.get('tags', []))
    
    # Adicionando contadores extras para os gráficos Donut
    leads_por_setor = {}
    leads_por_status = {"Quentes": sinais_quentes, "Frios/Estagnados": estagnados, "Mornos": len(deals) - sinais_quentes - estagnados}
    
    for d in deals:
        setor = str(d.get('sector') or 'Outro').capitalize()
        leads_por_setor[setor] = leads_por_setor.get(setor, 0) + 1
        
    return {
        "metrics": {
            "valor_esperado_total": total_esperado,
            "valor_funil_total": total_bruto,
            "oportunidades_ativas": len(deals),
            "estagnados": estagnados,
            "sem_resposta": sem_resposta,
            "sinais_quentes": sinais_quentes,
            "leads_por_setor": leads_por_setor,
            "leads_por_status": leads_por_status
        }
    }
