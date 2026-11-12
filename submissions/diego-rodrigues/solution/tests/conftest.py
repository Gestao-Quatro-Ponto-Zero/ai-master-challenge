import json
from pathlib import Path

import pandas as pd
import pytest

from motor.carregar import carregar
from motor.pontuar import pontuar_em

DADOS = Path(__file__).parent.parent / "data"


@pytest.fixture(scope="session")
def dados():
    return carregar(DADOS)


@pytest.fixture(scope="session")
def s(dados, config, hoje):
    return pontuar_em(dados, config, hoje)


@pytest.fixture(scope="session")
def config():
    return json.loads((Path(__file__).parent.parent / "config.json").read_text())


@pytest.fixture(scope="session")
def hoje():
    return pd.Timestamp("2018-01-01")


@pytest.fixture
def dados_dir():
    return DADOS
