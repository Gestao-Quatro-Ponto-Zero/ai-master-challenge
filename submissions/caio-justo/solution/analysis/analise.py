"""Gera os números da ferramenta e do relatório, todos a partir dos dados reais.

Uso: python3 analysis/analise.py  (leva alguns minutos; a semente é fixa)
"""
import json
import random
import statistics
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from prova.dados import HOJE, carregar  # noqa: E402
from prova.estatistica import estimativa_estratificada, tamanho_por_braco  # noqa: E402
from prova.porteiro import FATORES, avaliar  # noqa: E402
from prova.prioridade import Curva  # noqa: E402
from prova.sorteio import alocar_por_produto, sortear_checagem  # noqa: E402

GERADOR = random.Random(20171231)


def mapa_do_pipeline(negocios, curva):
    engajando = [n for n in negocios if n.estagio == "Engaging"]
    parados = [n for n in engajando if n.idade() > curva.limite]
    fechados = [n for n in negocios if n.fechado]
    return {
        "total": len(negocios),
        "ganhos": sum(n.ganho for n in fechados),
        "perdidos": sum(not n.ganho for n in fechados),
        "engajando": len(engajando),
        "prospeccao": sum(n.estagio == "Prospecting" for n in negocios),
        "limite_dias": curva.limite,
        "parados": len(parados),
        "parados_pct": len(parados) / len(engajando),
        "parados_valor": sum(n.preco for n in parados),
        "engajando_valor": sum(n.preco for n in engajando),
        "ativos": len(engajando) - len(parados),
        "abertos_sem_conta_pct": sum(1 for n in negocios if not n.fechado and not n.conta)
        / sum(1 for n in negocios if not n.fechado),
    }


def calendario(fechados):
    grupos = defaultdict(list)
    for negocio in fechados:
        grupos[(negocio.fim.month - 1) % 3 + 1].append(negocio)
    return {
        str(posicao): {
            "n": len(lista),
            "vitoria": sum(n.ganho for n in lista) / len(lista),
            "ciclo_max": max(n.ciclo for n in lista),
            "ciclo_mediana": statistics.median(n.ciclo for n in lista),
        }
        for posicao, lista in sorted(grupos.items())
    }


def vitoria_por_idade_no_mes(fechados):
    faixas = ((0, 14), (15, 60), (61, 100), (101, 140))
    saida = {}
    for posicao in (2, 3):
        linha = {}
        for baixo, alto in faixas:
            lista = [
                n
                for n in fechados
                if (n.fim.month - 1) % 3 + 1 == posicao and baixo <= n.ciclo <= alto
            ]
            linha[f"{baixo}-{alto}"] = {
                "n": len(lista),
                "vitoria": sum(n.ganho for n in lista) / len(lista) if lista else None,
            }
        saida[str(posicao)] = linha
    return saida


def porteiro(fechados):
    return {
        nome: avaliar(fechados, fator, 200, GERADOR) for nome, fator in FATORES.items()
    }


def porteiro_com_efeito_plantado(fechados, repeticoes=30):
    """O porteiro abre quando existe efeito? E fica fechado quando não existe?"""
    vendedores = sorted({n.vendedor for n in fechados})
    saida = []
    for virada in (0.0, 0.05, 0.10, 0.20, 0.30):
        abriu, diferencas = 0, []
        for _ in range(repeticoes):
            bons = set(GERADOR.sample(vendedores, len(vendedores) // 3))
            ganhos = {}
            for negocio in fechados:
                sorte = GERADOR.random()
                ganho = negocio.ganho
                if negocio.vendedor in bons and not ganho and sorte < virada:
                    ganho = True
                elif negocio.vendedor not in bons and ganho and sorte < virada / 2:
                    ganho = False
                ganhos[negocio.id] = ganho
            bom = [ganhos[n.id] for n in fechados if n.vendedor in bons]
            ruim = [ganhos[n.id] for n in fechados if n.vendedor not in bons]
            diferencas.append(sum(bom) / len(bom) - sum(ruim) / len(ruim))
            abriu += avaliar(
                fechados, FATORES["vendedor"], 60, GERADOR, rotulo=lambda n: ganhos[n.id]
            )["aberto"]
        saida.append(
            {
                "diferenca_real_pp": 100 * statistics.mean(diferencas),
                "abriu": abriu,
                "repeticoes": repeticoes,
            }
        )
    return saida


def retrato_em(negocios, dia):
    """Negócios engajados que estavam abertos em `dia`."""
    return [
        n
        for n in negocios
        if n.inicio and n.inicio <= dia and (n.fim is None or n.fim > dia)
    ]


def replay_de_politicas(negocios, por_vendedor=5, repeticoes_aleatorio=200):
    """Reconstrói a fila aberta em cada mês e compara formas de escolher os deals.

    Conta o valor ganho nos 60 dias seguintes pelos `por_vendedor` primeiros de cada
    vendedor. Mede só valor capturado no histórico, nunca o efeito de agir diferente.
    """
    datas = [date(2017, mes, 1) for mes in range(6, 11)]
    fechados = [n for n in negocios if n.fechado]

    def ganho_nos_60(negocio, dia):
        fim = negocio.fim
        return negocio.valor if negocio.ganho and fim and fim <= dia + timedelta(days=60) else 0

    politicas = {
        "preço": lambda n, dia, curva: n.preco,
        "preço sem parados": lambda n, dia, curva: n.preco if (dia - n.inicio).days <= curva.limite else -1,
        "preço x janela": lambda n, dia, curva: n.preco * curva.janela((dia - n.inicio).days),
        # Regra escolhida: preço sem parados, e no empate vem o negócio mais antigo.
        "preço sem parados, mais antigo no empate": lambda n, dia, curva: (
            n.preco + (dia - n.inicio).days / 1000 if (dia - n.inicio).days <= curva.limite else -1
        ),
    }
    totais = defaultdict(float)
    aleatorio = 0.0
    capturas_ativos = defaultdict(int)
    for dia in datas:
        curva = Curva.de(fechados, ate=dia)
        fila = retrato_em(negocios, dia)
        grupos = defaultdict(list)
        for negocio in fila:
            grupos[negocio.vendedor].append(negocio)
        for nome, regra in politicas.items():
            for lista in grupos.values():
                escolhidos = sorted(lista, key=lambda n: (-regra(n, dia, curva), n.id))[:por_vendedor]
                totais[nome] += sum(ganho_nos_60(n, dia) for n in escolhidos)
                capturas_ativos[nome] += sum(1 for n in escolhidos if ganho_nos_60(n, dia))
        for _ in range(repeticoes_aleatorio):
            for lista in grupos.values():
                escolhidos = GERADOR.sample(lista, min(por_vendedor, len(lista)))
                aleatorio += sum(ganho_nos_60(n, dia) for n in escolhidos) / repeticoes_aleatorio
    return {
        "datas": len(datas),
        "por_vendedor": por_vendedor,
        "valor_ganho": {**{k: round(v) for k, v in totais.items()}, "sorteio": round(aleatorio)},
        "deals_ganhos": dict(capturas_ativos),
    }


def tamanho_do_experimento(negocios):
    """Métrica principal: ganho em até 90 dias, entre todos os sorteados."""
    coorte = [
        n
        for n in negocios
        if n.inicio and date(2017, 3, 1) <= n.inicio <= HOJE - timedelta(days=90)
    ]
    ganhos = [n for n in coorte if n.ganho and n.ciclo <= 90]
    base = len(ganhos) / len(coorte)
    entradas = defaultdict(int)
    for negocio in negocios:
        if negocio.inicio and date(2017, 3, 1) <= negocio.inicio <= date(2017, 9, 30):
            entradas[negocio.inicio.isocalendar()[:2]] += 1
    por_semana = statistics.mean(entradas.values())
    saida = {"coorte": len(coorte), "base_ganho_90d": base, "novos_por_semana": por_semana, "cenarios": {}}
    for efeito in (0.03, 0.05, 0.10):
        n = tamanho_por_braco(base, efeito)
        saida["cenarios"][f"+{round(efeito * 100)}pp"] = {
            "por_grupo": n,
            "total": 2 * n,
            "semanas_de_entrada": 2 * n / por_semana,
            "semanas_com_90d": 2 * n / por_semana + 90 / 7,
        }
    return saida


def poder_entre_vendedores(negocios, repeticoes=400, permutacoes=200):
    """Metade dos vendedores usa a ferramenta: dá para ver receita total subir?

    Soma a receita real de cada vendedor numa janela, planta um ganho nos sorteados e
    aplica um teste de permutação. Controla pela receita do mesmo vendedor antes.
    """
    ganhos = [n for n in negocios if n.ganho]
    vendedores = sorted({n.vendedor for n in ganhos})
    semanas = sorted({n.fim - timedelta(days=n.fim.weekday()) for n in ganhos})
    receita = defaultdict(lambda: defaultdict(float))
    for negocio in ganhos:
        semana = negocio.fim - timedelta(days=negocio.fim.weekday())
        receita[negocio.vendedor][semana] += negocio.valor
    saida = {}
    for duracao in (13, 20):
        linha = {}
        for lift in (0.10, 0.20, 0.30, 0.50):
            acertos = 0
            for _ in range(repeticoes):
                inicio = GERADOR.randrange(duracao, len(semanas) - duracao + 1)
                antes = semanas[inicio - duracao : inicio]
                depois = semanas[inicio : inicio + duracao]
                base = {v: sum(receita[v][s] for s in antes) for v in vendedores}
                final = {v: sum(receita[v][s] for s in depois) for v in vendedores}
                tratados = set(GERADOR.sample(vendedores, len(vendedores) // 2))
                mudanca = {
                    v: final[v] * (1 + lift if v in tratados else 1) - base[v] for v in vendedores
                }

                def efeito(grupo):
                    t = [mudanca[v] for v in vendedores if v in grupo]
                    c = [mudanca[v] for v in vendedores if v not in grupo]
                    return sum(t) / len(t) - sum(c) / len(c)

                observado = efeito(tratados)
                extremos = sum(
                    abs(efeito(set(GERADOR.sample(vendedores, len(vendedores) // 2)))) >= abs(observado)
                    for _ in range(permutacoes)
                )
                acertos += extremos / permutacoes < 0.05
            linha[f"+{round(lift * 100)}%"] = acertos / repeticoes
        saida[f"{duracao} semanas"] = linha
    return saida


def cobertura_da_checagem(negocios, curva, repeticoes=4000):
    """A margem da checagem acerta 95% das vezes? Testa com verdades conhecidas."""
    parados = [n for n in negocios if n.estagio == "Engaging" and n.idade() > curva.limite]
    por_id = {n.id: n for n in parados}
    amostra = [por_id[i] for i in sorted(sortear_checagem(parados))]
    totais = defaultdict(lambda: {"valor": 0, "N": 0})
    for negocio in parados:
        totais[negocio.produto]["valor"] += negocio.preco
        totais[negocio.produto]["N"] += 1
    valor_total = sum(n.preco for n in parados)
    saida = {"alocacao": alocar_por_produto(parados), "cenarios": {}}
    for viva in (0.05, 0.10, 0.20, 0.50):
        acertos, larguras = 0, []
        for _ in range(repeticoes):
            vivos = {n.id for n in parados if GERADOR.random() < viva}
            real = sum(n.preco for n in parados if n.id in vivos) / valor_total
            estratos = {p: {**v, "n": 0, "s": 0} for p, v in totais.items()}
            for negocio in amostra:
                estratos[negocio.produto]["n"] += 1
                estratos[negocio.produto]["s"] += negocio.id in vivos
            r = estimativa_estratificada(list(estratos.values()))
            acertos += r["baixo"] <= real <= r["alto"]
            larguras.append(r["alto"] - r["baixo"])
        saida["cenarios"][f"{round(viva * 100)}%"] = {
            "cobertura": acertos / repeticoes,
            "margem_pontos": 100 * statistics.mean(larguras) / 2,
        }
    return saida


def main():
    negocios = carregar()
    fechados = [n for n in negocios if n.fechado]
    curva = Curva.de(negocios)
    resultados = {
        "gerado_com_semente": 20171231,
        "pipeline": mapa_do_pipeline(negocios, curva),
        "calendario": calendario(fechados),
        "vitoria_por_idade_no_mes": vitoria_por_idade_no_mes(fechados),
        "porteiro": porteiro(fechados),
        "porteiro_plantado": porteiro_com_efeito_plantado(fechados),
        "replay": replay_de_politicas(negocios),
        "experimento": tamanho_do_experimento(negocios),
        "poder_entre_vendedores": poder_entre_vendedores(negocios),
        "cobertura_checagem": cobertura_da_checagem(negocios, curva),
    }
    destino = RAIZ / "analysis" / "resultados.json"
    destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultados, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
