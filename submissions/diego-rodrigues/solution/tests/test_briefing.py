import json

import pytest

from build import construir
from ia.briefing import gerar


@pytest.fixture
def scored(dados_dir, config, tmp_path_factory):
    saida = tmp_path_factory.mktemp("scored_briefing")
    construir(dados_dir, config, saida=saida, hoje="2018-01-01")
    return json.loads((saida / "scored.json").read_text(encoding="utf-8"))


def test_gerar_sem_ia_usa_template(scored):
    b = gerar(scored, sem_ia=True)
    assert len(b["vendedores"]) == 35
    assert all(v["origem"] == "template" for v in b["vendedores"].values())
