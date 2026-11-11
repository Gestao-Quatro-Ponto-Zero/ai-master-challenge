"""Testes da regra do lead score contra os números do desenho (dataset limpo, sem banco).

Rodar a partir da pasta solution/:  python -m unittest scoring/test_regra.py -v
"""
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calcular_score as cs  # noqa: E402
import regra  # noqa: E402


class TestFaixas(unittest.TestCase):
    def test_heat(self):
        casos = {0: 100, 1: 100, 2: 85, 7: 85, 8: 70, 15: 70, 16: 55, 30: 55, 31: 40, 60: 40,
                 61: 25, 90: 25, 91: 10, 180: 10, 181: 0, 423: 0}
        for dias, pts in casos.items():
            self.assertEqual(regra.faixa_heat(dias)[0], pts, dias)
        self.assertEqual(regra.faixa_heat(None)[0], 50)

    def test_fator_contato(self):
        for dias, f in {None: 1.0, 0: 1.0, 7: 1.0, 8: 0.8, 14: 0.8, 15: 0.5, 30: 0.5, 31: 0.2}.items():
            self.assertEqual(regra.fator_contato(dias), f)


class TestDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = regra.preparar(*cs.ler_csv())
        cls.res = regra.calcular(d, cs.REFERENCIA)
        cls.deals = cls.res["deals"].set_index("opportunity_id")

    def test_abertos(self):
        self.assertEqual(len(self.deals), 2089)
        self.assertTrue(self.deals["nota"].between(0, 120).all())
        self.assertTrue(self.deals["fit"].between(0, 100).all())
        self.assertTrue(self.deals["heat"].between(0, 100).all())
        self.assertTrue(self.deals["bonus"].between(0, 20).all())

    def test_tres_exemplos(self):
        # FIT absoluto (O-51): conversão do vendedor no perfil, de 0 a 100
        for oid, nota, fit, heat, bonus in [("4ZQTMS3Z", 66.62, 63.74, 40, 10), ("1HD5JJM3", 68.60, 76.58, 50, 0),
                                            ("F5I33E1I", 47.69, 68.13, 0, 0)]:
            r = self.deals.loc[oid]
            self.assertAlmostEqual(r["nota"], nota, delta=0.01, msg=oid)
            self.assertAlmostEqual(r["fit"], fit, delta=0.01, msg=oid)
            self.assertEqual(r["heat"], heat, oid)
            self.assertEqual(r["bonus"], bonus, oid)

    def test_fit_absoluto(self):
        import numpy as np
        cel = self.res["celulas"]
        for _, r in self.deals.iterrows():
            f = r["detalhe_fit"]
            if f["usadas"]:
                esperado = 100 * float(np.mean([u["taxa_encolhida"] for u in f["usadas"]]))
            elif not f["sem_historico"]:
                esperado = 100 * cel.taxa_vendedor[r["vendedor_nome"]]
            else:
                esperado = 100 * cel.taxa_time
            self.assertAlmostEqual(r["fit"], esperado, places=9)
        f = self.deals["fit"]
        self.assertGreaterEqual(f.min(), 47.0)
        self.assertLessEqual(f.max(), 77.0)
        self.assertEqual(int((f >= 75).sum()), 17)

    def test_heat_por_faixa(self):
        self.assertEqual(self.deals["heat"].value_counts().to_dict(),
                         {0: 730, 10: 749, 25: 53, 40: 39, 50: 500, 55: 11, 70: 7})

    def test_bonus(self):
        self.assertEqual(self.deals["bonus"].value_counts().to_dict(), {0: 1651, 10: 230, 5: 208})
        self.assertEqual(int(self.res["padroes"]["na_janela"].sum()), 0)

    def test_top5(self):
        t5 = regra.top5(self.deals.reset_index())
        self.assertEqual(len(t5), 135)
        self.assertAlmostEqual(100 * t5["ativo"].mean(), 85.9, delta=0.05)

    def test_vendedores_sem_destaque(self):
        cel = self.res["celulas"]
        sem = sorted(v for v in cel.taxa_vendedor if not cel.tem_destaque(v))
        self.assertEqual(sem, ["Rosalina Dieter", "Wilburn Farren"])

    def test_motivos(self):
        n = self.deals["motivos"].map(len)
        self.assertTrue(n.between(2, 3).all())
        self.assertTrue(all(len(t) <= 280 for ms in self.deals["motivos"] for _, t in ms))

    def test_texto_dos_motivos(self):
        import re
        textos = [t for ms in self.deals["motivos"] for _, t in ms]
        segunda_pessoa = re.compile(r"\b(você|seu|sua|seus|suas)\b", re.IGNORECASE)
        self.assertFalse([t for t in textos if segunda_pessoa.search(t)])
        crus = re.compile(r"receita (media|pequena|grande)\b|funcionários (media|pequena|grande)|sede EUA\b|"
                          r"setor (" + "|".join(k for k, v in regra.SETORES.items() if k != v) + r")\b")
        self.assertFalse([t for t in textos if crus.search(t) and "de receita" not in t])
        self.assertEqual(self.deals.loc["4ZQTMS3Z", "motivos"][0][1],
                         "O vendedor fecha 64% dos leads com este perfil. Ponto forte do vendedor: série MG (67%).")

    def test_rotulos(self):
        casos = {("produto", "GTX Pro"): "produto GTX Pro", ("serie", "MG"): "série MG",
                 ("setor", "retail"): "setor varejo", ("receita", "media"): "empresa de receita média",
                 ("funcionarios", "pequena"): "empresa pequena em funcionários", ("empresa", "Kan-code"): "empresa Kan-code",
                 ("sede", "EUA"): "sede nos EUA", ("sede", "fora dos EUA"): "sede fora dos EUA"}
        for (dim, v), esperado in casos.items():
            self.assertEqual(regra._rot({"dim": dim, "valor": v}), esperado)

    def test_marcadores_e_acao(self):
        m = pd.Series([x for ms in self.deals["marcadores"] for x in ms]).value_counts().to_dict()
        self.assertEqual(m, {"esfriou": 1291, "risco_esfriar": 141})
        self.assertEqual(self.deals["acao_sugerida"].value_counts().to_dict(),
                         {"requalificar": 951, "focar": 798, "desistir": 340})


if __name__ == "__main__":
    unittest.main()
