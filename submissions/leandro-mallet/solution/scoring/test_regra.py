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

    def test_tres_exemplos_do_html(self):
        for oid, nota, fit, heat, bonus in [("4ZQTMS3Z", 72.8, 72.6, 40, 10), ("1HD5JJM3", 85.0, 100.0, 50, 0),
                                            ("F5I33E1I", 67.1, 95.8, 0, 0)]:
            r = self.deals.loc[oid]
            self.assertAlmostEqual(r["nota"], nota, delta=0.05, msg=oid)
            self.assertAlmostEqual(r["fit"], fit, delta=0.05, msg=oid)
            self.assertEqual(r["heat"], heat, oid)
            self.assertEqual(r["bonus"], bonus, oid)

    def test_distribuicao_fit(self):
        f = self.deals["fit"]
        esperado = {"0-20": 174, "20-40": 423, "40-50": 353, "50": 98, "50-60": 349, "60-75": 400, "75+": 292}
        obtido = {"0-20": int((f <= 20).sum()), "20-40": int(((f > 20) & (f <= 40)).sum()),
                  "40-50": int(((f > 40) & (f < 50)).sum()), "50": int((f == 50).sum()),
                  "50-60": int(((f > 50) & (f <= 60)).sum()), "60-75": int(((f > 60) & (f < 75)).sum()),
                  "75+": int((f >= 75).sum())}
        self.assertEqual(obtido, esperado)

    def test_heat_por_faixa(self):
        self.assertEqual(self.deals["heat"].value_counts().to_dict(),
                         {0: 730, 10: 749, 25: 53, 40: 39, 50: 500, 55: 11, 70: 7})

    def test_bonus(self):
        self.assertEqual(self.deals["bonus"].value_counts().to_dict(), {0: 1651, 10: 230, 5: 208})
        self.assertEqual(int(self.res["padroes"]["na_janela"].sum()), 0)

    def test_top5(self):
        t5 = regra.top5(self.deals.reset_index())
        self.assertEqual(len(t5), 135)
        self.assertAlmostEqual(100 * t5["ativo"].mean(), 77.8, delta=0.05)
        self.assertAlmostEqual(100 * t5["conta_nome"].notna().mean(), 38.5, delta=0.05)
        self.assertEqual(int((t5["dias"] >= 181).sum()), 6)

    def test_vendedores_sem_destaque(self):
        cel = self.res["celulas"]
        sem = sorted(v for v in cel.taxa_vendedor if not cel.tem_destaque(v))
        self.assertEqual(sem, ["Rosalina Dieter", "Wilburn Farren"])

    def test_motivos(self):
        n = self.deals["motivos"].map(len)
        self.assertTrue(n.between(2, 3).all())
        self.assertTrue(all(len(t) <= 280 for ms in self.deals["motivos"] for _, t in ms))

    def test_marcadores_e_acao(self):
        m = pd.Series([x for ms in self.deals["marcadores"] for x in ms]).value_counts().to_dict()
        self.assertEqual(m, {"esfriou": 1291, "risco_esfriar": 141})
        self.assertEqual(self.deals["acao_sugerida"].value_counts().to_dict(),
                         {"requalificar": 951, "focar": 798, "desistir": 340})


if __name__ == "__main__":
    unittest.main()
