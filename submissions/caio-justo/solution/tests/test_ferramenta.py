import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import replace
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from prova import prioridade as pri  # noqa: E402
from prova.banco import Banco  # noqa: E402
from prova.dados import carregar  # noqa: E402
from prova.estatistica import auc, diferenca_newcombe, tamanho_por_braco, teste_sinal, wilson  # noqa: E402
from prova.porteiro import FATORES, avaliar, dobras  # noqa: E402
from prova.servico import ErroDeEntrada, Servico  # noqa: E402
from prova.sorteio import alocar_por_produto, sortear_checagem, sortear_destaque  # noqa: E402
from prova.sugestao import ErroDaSugestao, Sugestor, regra_de_palavras  # noqa: E402

NEGOCIOS = carregar()
SERVICO = Servico(RAIZ / "analysis" / "resultados.json")


class Dados(unittest.TestCase):
    def test_todo_negocio_tem_preco(self):
        self.assertEqual(len(NEGOCIOS), 8800)
        self.assertTrue(all(n.preco > 0 for n in NEGOCIOS))
        self.assertNotIn("GTXPro", {n.produto for n in NEGOCIOS})

    def test_numeros_do_relatorio(self):
        curva = pri.Curva.de(NEGOCIOS)
        self.assertEqual(curva.limite, 138)
        self.assertEqual(len(SERVICO.parados), 1291)
        self.assertEqual(sum(n.preco for n in SERVICO.parados), 3198664)
        self.assertEqual(len(SERVICO.ativos), 298)


class Prioridade(unittest.TestCase):
    def test_nota_nao_usa_o_resultado(self):
        negocio = SERVICO.ativos[0]
        alterado = replace(negocio, valor=999999, fim=date(2017, 12, 30))
        curva = SERVICO.curva
        self.assertEqual(pri.situacao(negocio, curva), pri.situacao(alterado, curva))

    def test_parado_nao_recebe_nota(self):
        self.assertTrue(all(n.id not in SERVICO.notas for n in SERVICO.parados))

    def test_nota_cresce_com_preco(self):
        ativos = sorted(SERVICO.ativos, key=lambda n: SERVICO.notas[n.id])
        self.assertLessEqual(ativos[0].preco, ativos[-1].preco)

    def test_motivo_explica_com_fatos(self):
        negocio = next(n for n in SERVICO.ativos if not n.conta)
        texto = " ".join(pri.motivos(negocio, SERVICO.curva, SERVICO.notas[negocio.id]))
        self.assertIn("Sem conta", texto)
        self.assertIn(str(negocio.idade()), texto)


class Sorteios(unittest.TestCase):
    def test_checagem_tem_cem_e_todo_produto(self):
        amostra = sortear_checagem(SERVICO.parados)
        self.assertEqual(len(amostra), 100)
        produtos = {SERVICO.negocios[i].produto for i in amostra}
        self.assertEqual(produtos, {n.produto for n in SERVICO.parados})

    def test_sorteios_sao_reprodutiveis(self):
        self.assertEqual(sortear_checagem(SERVICO.parados), sortear_checagem(SERVICO.parados))
        self.assertEqual(
            sortear_destaque(SERVICO.ativos, SERVICO.notas),
            sortear_destaque(SERVICO.ativos, SERVICO.notas),
        )

    def test_alocacao_soma_cem(self):
        self.assertEqual(sum(alocar_por_produto(SERVICO.parados).values()), 100)

    def test_alocacao_segue_o_valor(self):
        alocacao = alocar_por_produto(SERVICO.parados)
        self.assertGreater(alocacao["GTX Pro"], alocacao["MG Special"])
        self.assertGreaterEqual(alocacao["GTK 500"], 10)
        self.assertGreaterEqual(min(alocacao.values()), 2)

    def test_grupos_equilibrados_em_preco(self):
        grupos = SERVICO.grupos
        destaque = [SERVICO.negocios[i].preco for i, g in grupos.items() if g == "destaque"]
        controle = [SERVICO.negocios[i].preco for i, g in grupos.items() if g == "controle"]
        self.assertLessEqual(abs(len(destaque) - len(controle)), 27)
        media_d, media_c = sum(destaque) / len(destaque), sum(controle) / len(controle)
        self.assertLess(abs(media_d - media_c) / max(media_d, media_c), 0.25)

    def test_todo_ativo_foi_sorteado(self):
        self.assertEqual(set(SERVICO.grupos), {n.id for n in SERVICO.ativos})


class Estatistica(unittest.TestCase):
    def test_wilson_valor_conhecido(self):
        baixo, alto = wilson(10, 100)
        self.assertAlmostEqual(baixo, 0.0552, places=3)
        self.assertAlmostEqual(alto, 0.1744, places=3)

    def test_newcombe_exemplo_do_artigo(self):
        # Newcombe (1998), caso 56/70 contra 48/80: 0,2 com IC [0,0524; 0,3339].
        d, baixo, alto = diferenca_newcombe(56, 70, 48, 80)
        self.assertAlmostEqual(d, 0.2, places=4)
        self.assertAlmostEqual(baixo, 0.0524, places=3)
        self.assertAlmostEqual(alto, 0.3339, places=3)

    def test_auc(self):
        self.assertEqual(auc([0, 0, 1, 1], [1, 2, 3, 4]), 1.0)
        self.assertEqual(auc([1, 1, 0, 0], [1, 2, 3, 4]), 0.0)
        self.assertEqual(auc([0, 1, 0, 1], [5, 5, 5, 5]), 0.5)

    def test_tamanho(self):
        self.assertGreater(tamanho_por_braco(0.39, 0.05), tamanho_por_braco(0.39, 0.10))

    def test_sinal(self):
        self.assertAlmostEqual(teste_sinal(5, 5), 1.0)
        self.assertLess(teste_sinal(20, 2), 0.01)


class Porteiro(unittest.TestCase):
    def test_nao_olha_o_futuro(self):
        fechados = [n for n in NEGOCIOS if n.fechado]
        base = dobras(fechados, FATORES["vendedor"])[0]
        corte = date(2017, 6, 1)
        # Mudar o que acontece depois do primeiro mês de teste não muda as notas dele.
        rotulo = lambda n: (not n.ganho) if n.fim >= date(2017, 7, 1) else n.ganho
        trocado = dobras(fechados, FATORES["vendedor"], rotulo)[0]
        self.assertEqual(base[1], trocado[1])
        self.assertLess(corte, date(2017, 7, 1))

    def test_abre_com_sinal_forte(self):
        import random

        fechados = [n for n in NEGOCIOS if n.fechado]
        bons = sorted({n.vendedor for n in fechados})[:10]
        gerador = random.Random(1)
        ganhos = {n.id: gerador.random() < (0.85 if n.vendedor in bons else 0.45) for n in fechados}
        resultado = avaliar(fechados, FATORES["vendedor"], 40, gerador, rotulo=lambda n: ganhos[n.id])
        self.assertTrue(resultado["aberto"])


class Fluxo(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.banco = Banco(Path(self.pasta.name) / "t.db")

    def tearDown(self):
        self.banco.conexao.close()
        self.pasta.cleanup()

    def _um_da_amostra(self):
        return SERVICO.negocios[sorted(SERVICO.amostra)[0]]

    def test_responder_e_desfazer(self):
        n = self._um_da_amostra()
        SERVICO.responder_checagem(self.banco, n.id, "vivo", n.vendedor)
        self.assertEqual(SERVICO.checagem(self.banco)["respondidos"], 1)
        SERVICO.responder_checagem(self.banco, n.id, None, n.vendedor)
        self.assertEqual(SERVICO.checagem(self.banco)["respondidos"], 0)

    def test_nao_aceita_negocio_de_outro_vendedor(self):
        n = self._um_da_amostra()
        with self.assertRaises(ErroDeEntrada):
            SERVICO.responder_checagem(self.banco, n.id, "vivo", "Outra Pessoa")

    def test_nao_aceita_resposta_invalida(self):
        n = self._um_da_amostra()
        with self.assertRaises(ErroDeEntrada):
            SERVICO.responder_checagem(self.banco, n.id, "talvez", n.vendedor)

    def test_decisao_limpar_e_recuperar(self):
        for i in sorted(SERVICO.amostra):
            n = SERVICO.negocios[i]
            SERVICO.responder_checagem(self.banco, i, "perdido", n.vendedor)
        self.assertEqual(SERVICO.checagem(self.banco)["decisao"], "limpar")
        for i in sorted(SERVICO.amostra):
            n = SERVICO.negocios[i]
            SERVICO.responder_checagem(self.banco, i, "vivo", n.vendedor)
        self.assertEqual(SERVICO.checagem(self.banco)["decisao"], "recuperar")

    def test_placar_nao_da_veredito_antes_da_meta(self):
        ativo = SERVICO.ativos[0]
        SERVICO.registrar_resultado(self.banco, ativo.id, "ganhou", ativo.vendedor)
        placar = SERVICO.placar(self.banco)
        self.assertEqual(placar["veredito"], "aguardando")
        self.assertNotIn("diferenca", placar)
        self.assertNotIn("taxa", placar["destaque"])

    def test_placar_conta_quem_nao_ganhou_depois_do_prazo(self):
        ativo = SERVICO.ativos[0]
        SERVICO.registrar_resultado(self.banco, ativo.id, "ganhou", ativo.vendedor)
        depois = SERVICO.placar(self.banco, date(2018, 4, 1))
        self.assertEqual(depois["destaque"]["n"] + depois["controle"]["n"], len(SERVICO.grupos))
        antes = SERVICO.placar(self.banco, date(2018, 3, 1))
        self.assertEqual(antes["destaque"]["n"] + antes["controle"]["n"], 0)

    def test_simulacao_detecta_efeito_grande_e_nao_inventa_sem_efeito(self):
        SERVICO.simular(self.banco, 0.2, 0.2)
        self.assertEqual(SERVICO.placar(self.banco)["veredito"], "ajuda")
        SERVICO.simular(self.banco, 0.2, 0.0, semente=3)
        self.assertEqual(SERVICO.placar(self.banco)["veredito"], "sem_diferenca")

    def test_adiado_vai_para_o_fim_sem_mudar_o_grupo(self):
        vendedor = max(
            {n.vendedor for n in SERVICO.ativos},
            key=lambda v: sum(1 for n in SERVICO.ativos if n.vendedor == v),
        )
        semana = SERVICO.semana(vendedor, self.banco)
        primeiro = semana["foco"][0]["id"]
        grupo = SERVICO.grupos[primeiro]
        SERVICO.adiar(self.banco, primeiro, True, vendedor)
        depois = SERVICO.semana(vendedor, self.banco)
        self.assertNotEqual(depois["foco"][0]["id"], primeiro)
        self.assertEqual(SERVICO.grupos[primeiro], grupo)


def provedor_falso(conteudo, chamadas=None):
    def transporte(chave, corpo):
        if chamadas is not None:
            chamadas.append((chave, corpo))
        return {"choices": [{"message": {"content": conteudo}}], "usage": {"cost": 0.0001}}

    return transporte


class Sugestao(unittest.TestCase):
    def test_sem_chave_fica_desligada(self):
        sugestor = Sugestor(None)
        self.assertFalse(sugestor.disponivel)
        with self.assertRaises(ErroDaSugestao):
            sugestor.sugerir("cliente respondeu")

    def test_resposta_valida(self):
        conteudo = json.dumps({"resposta": "depois", "motivo": "pediu março"})
        r = Sugestor("k", transporte=provedor_falso(conteudo)).sugerir("voltar em março")
        self.assertEqual((r["resposta"], r["motivo"]), ("depois", "pediu março"))

    def test_recusa_resposta_fora_das_opcoes(self):
        conteudo = json.dumps({"resposta": "fechar_agora", "motivo": "x"})
        with self.assertRaises(ErroDaSugestao):
            Sugestor("k", transporte=provedor_falso(conteudo)).sugerir("nota")

    def test_recusa_formato_quebrado(self):
        for conteudo in ("não é json", "[]", json.dumps({"motivo": "sem resposta"})):
            with self.assertRaises(ErroDaSugestao):
                Sugestor("k", transporte=provedor_falso(conteudo)).sugerir("nota")

    def test_nota_vazia_ou_longa_nao_chama_o_provedor(self):
        chamadas = []
        sugestor = Sugestor("k", transporte=provedor_falso("{}", chamadas))
        for nota in ("", "   ", "x" * 501):
            with self.assertRaises(ErroDaSugestao):
                sugestor.sugerir(nota)
        self.assertEqual(chamadas, [])

    def test_so_envia_a_nota_e_nao_salva_o_texto(self):
        chamadas = []
        conteudo = json.dumps({"resposta": "vivo", "motivo": "reunião"})
        negocio = SERVICO.negocios[sorted(SERVICO.amostra)[0]]
        with tempfile.TemporaryDirectory() as pasta:
            banco = Banco(Path(pasta) / "t.db")
            sugestor = Sugestor("chave-secreta", transporte=provedor_falso(conteudo, chamadas))
            SERVICO.sugerir(banco, sugestor, negocio.id, "texto sigiloso", negocio.vendedor)
            enviado = json.dumps(chamadas[0][1], ensure_ascii=False)
            self.assertIn("texto sigiloso", enviado)
            self.assertNotIn(negocio.vendedor, enviado)
            self.assertNotIn(negocio.id, enviado)
            self.assertNotIn("chave-secreta", enviado)
            salvo = [tuple(l) for t in ("sugestoes", "checagens") for l in banco.conexao.execute(f"SELECT * FROM {t}")]
            self.assertNotIn("texto sigiloso", str(salvo))
            banco.conexao.close()

    def test_sugestao_nao_responde_sozinha(self):
        conteudo = json.dumps({"resposta": "perdido", "motivo": "fechou com outro"})
        negocio = SERVICO.negocios[sorted(SERVICO.amostra)[0]]
        with tempfile.TemporaryDirectory() as pasta:
            banco = Banco(Path(pasta) / "t.db")
            sugestor = Sugestor("k", transporte=provedor_falso(conteudo))
            SERVICO.sugerir(banco, sugestor, negocio.id, "nota", negocio.vendedor)
            self.assertEqual(SERVICO.checagem(banco)["respondidos"], 0)
            self.assertEqual(SERVICO.uso_da_ia(banco), {"sugestoes": 1, "decididas": 0, "aceitas": 0})
            SERVICO.responder_checagem(banco, negocio.id, "perdido", negocio.vendedor)
            self.assertEqual(SERVICO.uso_da_ia(banco)["aceitas"], 1)
            banco.conexao.close()

    def test_negocio_de_outro_vendedor_nao_chama_o_provedor(self):
        chamadas = []
        negocio = SERVICO.negocios[sorted(SERVICO.amostra)[0]]
        with tempfile.TemporaryDirectory() as pasta:
            banco = Banco(Path(pasta) / "t.db")
            with self.assertRaises(ErroDeEntrada):
                SERVICO.sugerir(banco, Sugestor("k", transporte=provedor_falso("{}", chamadas)), negocio.id, "nota", "Outra Pessoa")
            banco.conexao.close()
        self.assertEqual(chamadas, [])

    def test_limite_por_minuto(self):
        conteudo = json.dumps({"resposta": "vivo", "motivo": "x"})
        agora = [0.0]
        sugestor = Sugestor("k", transporte=provedor_falso(conteudo), relogio=lambda: agora[0])
        for _ in range(60):
            sugestor.sugerir("nota")
        with self.assertRaises(ErroDaSugestao):
            sugestor.sugerir("nota")
        agora[0] = 61.0
        self.assertEqual(sugestor.sugerir("nota")["resposta"], "vivo")

    def test_regra_de_palavras(self):
        self.assertEqual(regra_de_palavras("Fecharam com o concorrente"), "perdido")
        self.assertEqual(regra_de_palavras("Reunião na terça"), "vivo")


class Servidor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server

        cls.pasta = tempfile.TemporaryDirectory()
        conteudo = json.dumps({"resposta": "depois", "motivo": "pediu março"})
        cls.app = server.Aplicacao(Path(cls.pasta.name), Sugestor("k", transporte=provedor_falso(conteudo)))
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.criar_manipulador(cls.app))
        cls.url = f"http://127.0.0.1:{cls.http.server_address[1]}"
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        for banco in cls.app.bancos.values():
            banco.conexao.close()
        cls.pasta.cleanup()

    def _pegar(self, caminho):
        abridor = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        return abridor.open(self.url + caminho, timeout=10)

    def _post(self, caminho, dados):
        pedido = urllib.request.Request(
            self.url + caminho, json.dumps(dados).encode(), {"Content-Type": "application/json"}
        )
        return urllib.request.build_opener(urllib.request.ProxyHandler({})).open(pedido, timeout=10)

    def test_telas_respondem(self):
        filtros = json.load(self._pegar("/api/filtros"))
        vendedor = filtros["vendedores"][0]["nome"]
        semana = json.load(self._pegar("/api/semana?vendedor=" + urllib.parse.quote(vendedor)))
        self.assertEqual(semana["vendedor"], vendedor)
        head = json.load(self._pegar("/api/head"))
        self.assertEqual(head["pipeline"]["parados"], 1291)

    def test_sugestao_pela_api(self):
        negocio = SERVICO.negocios[sorted(SERVICO.amostra)[0]]
        filtros = json.load(self._pegar("/api/filtros"))
        self.assertTrue(filtros["ia"]["disponivel"])
        self.assertNotIn("k", filtros["ia"].get("chave", ""))
        r = json.load(self._post("/api/sugestao", {"modo": "demo", "negocio": negocio.id, "vendedor": negocio.vendedor, "nota": "voltar em março"}))
        self.assertEqual(r["resposta"], "depois")

    def test_vendedor_inexistente_vira_erro_claro(self):
        with self.assertRaises(urllib.error.HTTPError) as erro:
            self._pegar("/api/semana?vendedor=Ninguem")
        self.assertEqual(erro.exception.code, 400)

    def test_demonstracao_nao_contamina_o_real(self):
        self._post("/api/demo/simular", {"viva": 0.2, "efeito": 0.1})
        real = json.load(self._pegar("/api/head?modo=real"))
        demo = json.load(self._pegar("/api/head?modo=demo"))
        self.assertEqual(real["checagem"]["respondidos"], 0)
        self.assertEqual(demo["checagem"]["respondidos"], 100)

    def test_nao_serve_arquivo_fora_da_pasta_web(self):
        with self.assertRaises(urllib.error.HTTPError) as erro:
            self._pegar("/../server.py")
        self.assertEqual(erro.exception.code, 404)
        with self.assertRaises(urllib.error.HTTPError) as erro:
            self._pegar("/%2e%2e/server.py")
        self.assertEqual(erro.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
