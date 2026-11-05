"""Regras do produto: monta as telas e calcula a checagem e o placar."""
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from . import prioridade as pri
from .dados import HOJE, carregar
from .estatistica import diferenca_newcombe, estimativa_estratificada, tamanho_por_braco, teste_sinal, wilson
from .sorteio import sortear_checagem, sortear_destaque

RESPOSTAS_CHECAGEM = {"vivo", "depois", "perdido", "errado"}
RESPOSTAS_REAIS = {"vivo", "depois"}
RESULTADOS = {"ganhou", "perdeu"}
FOCO_POR_VENDEDOR = 5
LIMITE_LIMPEZA = 0.10
EFEITO_MINIMO = 0.10
DIAS_ACOMPANHAMENTO = 90


class ErroDeEntrada(ValueError):
    """Pedido inválido; o servidor responde com erro 400."""


class Servico:
    def __init__(self, resultados_analise: Path, pasta_dados: Path = None):
        negocios = carregar(pasta_dados) if pasta_dados else carregar()
        self.negocios = {n.id: n for n in negocios}
        self.curva = pri.Curva.de(negocios)
        self.abertos = [n for n in negocios if not n.fechado]
        self.notas = pri.montar_notas(self.abertos, self.curva)
        self.ativos = [n for n in self.abertos if pri.situacao(n, self.curva) == pri.ATIVO]
        self.parados = [n for n in self.abertos if pri.situacao(n, self.curva) == pri.PARADO]
        self.qualificar = [n for n in self.abertos if pri.situacao(n, self.curva) == pri.QUALIFICAR]
        self.amostra = sortear_checagem(self.parados)
        self.grupos = sortear_destaque(self.ativos, self.notas)
        self.analise = json.loads(resultados_analise.read_text(encoding="utf-8"))
        self.base_90d = self.analise["experimento"]["base_ganho_90d"]
        self.meta_por_grupo = tamanho_por_braco(self.base_90d, EFEITO_MINIMO)
        self.times = sorted(
            {(n.vendedor, n.manager, n.regiao) for n in negocios}, key=lambda t: t[0]
        )

    def filtros(self) -> dict:
        com_abertos = {n.vendedor for n in self.abertos}
        ativos = defaultdict(int)
        for negocio in self.ativos:
            ativos[negocio.vendedor] += 1
        return {
            "hoje": HOJE.isoformat(),
            "vendedores": [
                {"nome": v, "manager": m, "regiao": r, "ativos": ativos[v]}
                for v, m, r in self.times
                if v in com_abertos
            ],
            "managers": sorted({m for _, m, _ in self.times}),
            "regioes": sorted({r for _, _, r in self.times}),
        }

    def _cartao(self, negocio, banco_adiados=frozenset()) -> dict:
        nota = self.notas.get(negocio.id)
        return {
            "id": negocio.id,
            "produto": negocio.produto,
            "conta": negocio.conta,
            "preco": negocio.preco,
            "idade": negocio.idade(),
            "nota": nota,
            "motivos": pri.motivos(negocio, self.curva, nota),
            "acao": pri.proxima_acao(negocio, self.curva),
            "adiado": negocio.id in banco_adiados,
        }

    def semana(self, vendedor: str, banco) -> dict:
        if vendedor not in {t[0] for t in self.times}:
            raise ErroDeEntrada("Vendedor não encontrado")
        checagens = banco.checagens()
        resultados = banco.resultados()
        adiados = banco.adiados()
        meus = [n for n in self.ativos if n.vendedor == vendedor and n.id not in resultados]
        ordem = lambda n: (n.id in adiados, -self.notas[n.id], n.id)
        destaque = sorted((n for n in meus if self.grupos[n.id] == "destaque"), key=ordem)
        demais = sorted((n for n in meus if self.grupos[n.id] == "controle"), key=ordem)
        extras = destaque[FOCO_POR_VENDEDOR:]
        checar = sorted(
            (n for n in self.parados if n.vendedor == vendedor and n.id in self.amostra),
            key=lambda n: (-n.preco, n.id),
        )
        return {
            "vendedor": vendedor,
            "foco": [self._cartao(n, adiados) for n in destaque[:FOCO_POR_VENDEDOR]],
            "mais_foco": [self._cartao(n, adiados) for n in extras],
            "demais": [self._cartao(n, adiados) for n in demais],
            "checar": [
                {**self._cartao(n), "resposta": checagens.get(n.id)} for n in checar
            ],
            "qualificar": [
                self._cartao(n)
                for n in sorted(
                    (n for n in self.qualificar if n.vendedor == vendedor),
                    key=lambda n: (-n.preco, n.id),
                )[:FOCO_POR_VENDEDOR]
            ],
            "qualificar_total": sum(1 for n in self.qualificar if n.vendedor == vendedor),
            "parados_total": sum(1 for n in self.parados if n.vendedor == vendedor),
            "limite": self.curva.limite,
        }

    def responder_checagem(self, banco, negocio: str, resposta, vendedor: str) -> None:
        if negocio not in self.amostra:
            raise ErroDeEntrada("Esse negócio não está na amostra")
        if self.negocios[negocio].vendedor != vendedor:
            raise ErroDeEntrada("Esse negócio é de outro vendedor")
        if resposta is None:
            banco.desfazer_checagem(negocio)
            return
        if resposta not in RESPOSTAS_CHECAGEM:
            raise ErroDeEntrada("Resposta inválida")
        banco.responder_checagem(negocio, resposta, vendedor)

    def sugerir(self, banco, sugestor, negocio: str, nota: str, vendedor: str) -> dict:
        """Pede uma sugestão à LLM. Quem confirma a resposta é o vendedor."""
        if negocio not in self.amostra:
            raise ErroDeEntrada("Esse negócio não está na amostra")
        if self.negocios[negocio].vendedor != vendedor:
            raise ErroDeEntrada("Esse negócio é de outro vendedor")
        sugestao = sugestor.sugerir(nota)
        banco.registrar_sugestao(negocio, sugestao["resposta"], sugestao["modelo"])
        return {k: sugestao[k] for k in ("resposta", "motivo", "modelo")}

    def uso_da_ia(self, banco) -> dict:
        sugestoes = banco.sugestoes()
        checagens = banco.checagens()
        decididas = [n for n in sugestoes if n in checagens]
        return {
            "sugestoes": len(sugestoes),
            "decididas": len(decididas),
            "aceitas": sum(sugestoes[n] == checagens[n] for n in decididas),
        }

    def registrar_resultado(self, banco, negocio: str, resultado, vendedor: str) -> None:
        if negocio not in self.grupos:
            raise ErroDeEntrada("Esse negócio não está no teste")
        if self.negocios[negocio].vendedor != vendedor:
            raise ErroDeEntrada("Esse negócio é de outro vendedor")
        if resultado is None:
            banco.desfazer_resultado(negocio)
            return
        if resultado not in RESULTADOS:
            raise ErroDeEntrada("Resultado inválido")
        banco.registrar_resultado(negocio, resultado, vendedor)

    def adiar(self, banco, negocio: str, adiado: bool, vendedor: str) -> None:
        if negocio not in self.grupos:
            raise ErroDeEntrada("Esse negócio não está na lista")
        if self.negocios[negocio].vendedor != vendedor:
            raise ErroDeEntrada("Esse negócio é de outro vendedor")
        banco.adiar(negocio, vendedor, adiado)

    def checagem(self, banco) -> dict:
        """Estima quanto do valor parado ainda é real, a partir da amostra sorteada."""
        respostas = {k: v for k, v in banco.checagens().items() if k in self.amostra}
        contagem = {r: 0 for r in RESPOSTAS_CHECAGEM}
        for resposta in respostas.values():
            contagem[resposta] += 1
        estratos = defaultdict(lambda: {"valor": 0, "N": 0, "n": 0, "s": 0})
        for negocio in self.parados:
            estrato = estratos[negocio.produto]
            estrato["valor"] += negocio.preco
            estrato["N"] += 1
            resposta = respostas.get(negocio.id)
            if resposta:
                estrato["n"] += 1
                estrato["s"] += resposta in RESPOSTAS_REAIS
        estimativa = estimativa_estratificada(list(estratos.values()))
        total_valor = sum(n.preco for n in self.parados)
        decisao = "aguardando"
        respondidos = len(respostas)
        if respondidos >= len(self.amostra) and estimativa["parcela"] is not None:
            if estimativa["alto"] < LIMITE_LIMPEZA:
                decisao = "limpar"
            elif estimativa["baixo"] >= LIMITE_LIMPEZA:
                decisao = "recuperar"
            else:
                decisao = "inconclusivo"
        return {
            "amostra": len(self.amostra),
            "respondidos": respondidos,
            "contagem": contagem,
            "parados": len(self.parados),
            "valor_total": total_valor,
            "estimativa": estimativa,
            "valor_real": {
                chave: round(estimativa[chave] * total_valor) if estimativa[chave] is not None else None
                for chave in ("parcela", "baixo", "alto")
            },
            "limite_limpeza": LIMITE_LIMPEZA,
            "decisao": decisao,
        }

    def _linhas_placar(self, banco, hoje: date) -> list:
        """Só conta quem completou o acompanhamento; quem não ganhou no prazo conta como não ganho.

        Contar apenas os encerrados enviesaria o teste, porque o destaque pode mudar
        quais negócios encerram. Por isso o denominador é todo negócio sorteado.
        """
        simuladas = banco.placar_simulado()
        if simuladas:
            return [(l["grupo"], l["vendedor"], bool(l["ganhou"])) for l in simuladas]
        if hoje < HOJE + timedelta(days=DIAS_ACOMPANHAMENTO):
            return []
        resultados = banco.resultados()
        return [
            (grupo, self.negocios[negocio].vendedor, resultados.get(negocio) == "ganhou")
            for negocio, grupo in self.grupos.items()
        ]

    def placar(self, banco, hoje: date = HOJE) -> dict:
        """Compara os grupos. Sem veredito antes da meta, para não decidir espiando."""
        linhas = self._linhas_placar(banco, hoje)
        grupos = {"destaque": [0, 0], "controle": [0, 0]}
        por_vendedor = defaultdict(lambda: {"destaque": [0, 0], "controle": [0, 0]})
        for grupo, vendedor, ganhou in linhas:
            grupos[grupo][0] += ganhou
            grupos[grupo][1] += 1
            por_vendedor[vendedor][grupo][0] += ganhou
            por_vendedor[vendedor][grupo][1] += 1
        ganhos_d, n_d = grupos["destaque"]
        ganhos_c, n_c = grupos["controle"]
        meta = self.meta_por_grupo
        completo = n_d >= meta and n_c >= meta
        favor = contra = 0
        for valores in por_vendedor.values():
            d, c = valores["destaque"], valores["controle"]
            if d[1] and c[1]:
                diferenca = d[0] / d[1] - c[0] / c[1]
                favor += diferenca > 0
                contra += diferenca < 0
        saida = {
            "meta_por_grupo": meta,
            "efeito_minimo": EFEITO_MINIMO,
            "base": self.base_90d,
            "dias_acompanhamento": DIAS_ACOMPANHAMENTO,
            "sorteados": {
                "destaque": sum(1 for g in self.grupos.values() if g == "destaque"),
                "controle": sum(1 for g in self.grupos.values() if g == "controle"),
            },
            "registrados": len(banco.resultados()),
            "destaque": {"n": n_d},
            "controle": {"n": n_c},
            "completo": completo,
            "veredito": "aguardando",
        }
        if not completo:
            return saida
        diferenca, baixo, alto = diferenca_newcombe(ganhos_d, n_d, ganhos_c, n_c)
        saida["destaque"] = {"n": n_d, "ganhos": ganhos_d, "taxa": ganhos_d / n_d, "ic": wilson(ganhos_d, n_d)}
        saida["controle"] = {"n": n_c, "ganhos": ganhos_c, "taxa": ganhos_c / n_c, "ic": wilson(ganhos_c, n_c)}
        saida["diferenca"] = {"valor": diferenca, "baixo": baixo, "alto": alto}
        saida["vendedores"] = {"favor": favor, "contra": contra, "p": teste_sinal(favor, contra)}
        saida["veredito"] = "ajuda" if baixo > 0 else ("atrapalha" if alto < 0 else "sem_diferenca")
        return saida

    def visao_head(self, banco, manager: str = None, regiao: str = None) -> dict:
        def passa(n):
            return (not manager or n.manager == manager) and (not regiao or n.regiao == regiao)

        ativos = [n for n in self.ativos if passa(n)]
        parados = [n for n in self.parados if passa(n)]
        qualificar = [n for n in self.qualificar if passa(n)]
        return {
            "pipeline": {
                "ativos": len(ativos),
                "ativos_valor": sum(n.preco for n in ativos),
                "parados": len(parados),
                "parados_valor": sum(n.preco for n in parados),
                "qualificar": len(qualificar),
                "qualificar_valor": sum(n.preco for n in qualificar),
                "limite": self.curva.limite,
            },
            "checagem": self.checagem(banco),
            "uso_da_ia": self.uso_da_ia(banco),
            "placar": self.placar(banco),
            "porteiro": self.analise["porteiro"],
            "porteiro_plantado": self.analise["porteiro_plantado"],
            "replay": self.analise["replay"],
            "cenarios": self.analise["experimento"]["cenarios"],
            "poder_entre_vendedores": self.analise["poder_entre_vendedores"],
        }

    def limpeza_csv(self, banco) -> str:
        """Lista para o RevOps revisar. A ferramenta não altera o CRM sozinha."""
        checagens = banco.checagens()
        linhas = ["id,vendedor,manager,regiao,produto,conta,preco,dias_aberto,resposta"]
        for negocio in sorted(self.parados, key=lambda n: (n.vendedor, -n.preco, n.id)):
            campos = (
                negocio.id,
                negocio.vendedor,
                negocio.manager,
                negocio.regiao,
                negocio.produto,
                negocio.conta or "",
                str(negocio.preco),
                str(negocio.idade()),
                checagens.get(negocio.id, ""),
            )
            linhas.append(",".join('"' + c.replace('"', '""') + '"' for c in campos))
        return "\n".join(linhas) + "\n"

    def simular(self, banco, parcela_viva: float, efeito: float, semente: int = 7) -> None:
        """Preenche o banco de demonstração. Nunca toca no banco real."""
        if not 0 <= parcela_viva <= 1 or not 0 <= abs(efeito) <= 0.5:
            raise ErroDeEntrada("Parâmetros de simulação fora do intervalo")
        gerador = random.Random(semente)
        banco.limpar()
        for negocio_id in sorted(self.amostra):
            negocio = self.negocios[negocio_id]
            if gerador.random() < parcela_viva:
                resposta = gerador.choice(["vivo", "depois"])
            else:
                resposta = gerador.choices(["perdido", "errado"], weights=[4, 1])[0]
            banco.responder_checagem(negocio_id, resposta, negocio.vendedor)
        vendedores = sorted({n.vendedor for n in self.ativos})
        linhas = []
        for i in range(2 * self.meta_por_grupo):
            grupo = "destaque" if i % 2 == 0 else "controle"
            chance = self.base_90d + (efeito if grupo == "destaque" else 0)
            linhas.append((grupo, vendedores[i // 2 % len(vendedores)], int(gerador.random() < chance)))
        banco.gravar_placar_simulado(linhas)
