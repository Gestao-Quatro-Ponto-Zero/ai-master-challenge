"""Fixtures sintéticas pequenas. Nenhum resultado operacional vem destes dados."""

import itertools

import pandas as pd
import pytest

from supportops.analytics import diagnostic, group_stats
from supportops.dedup import near_groups
from supportops.ingest import SUPPORT_FIELDS, read_csv
from supportops.quality import timestamp_profile


def row(**changes):
    return {
        "Ticket ID": "1",
        "Ticket Type": "Refund request",
        "Ticket Priority": "Medium",
        "Ticket Channel": "Chat",
        "Ticket Status": "Closed",
        "Ticket Description": "Produto {produto}",
        "Ticket Subject": "Reembolso",
        "Resolution": "Análise encaminhada.",
        "First Response Time": "2024-01-01 12:00:00",
        "Time to Resolution": "2024-01-01 11:00:00",
        "Customer Satisfaction Rating": "5.0",
        **changes,
    }


@pytest.mark.parametrize(
    "data,error", [(b"", "vazio"), (b"wrong\nX", "ausentes"), (b"a\n", "sem registros")]
)
def test_csv_rejects_bad_schema(data, error):
    with pytest.raises(ValueError, match=error):
        read_csv(
            data,
            ("wrong",)
            if error == "vazio"
            else (("a",) if error == "sem registros" else SUPPORT_FIELDS),
        )


def test_no_duplicate_or_unverifiable_metrics():
    rows = [
        row(),
        row(),
        row(**{"Ticket ID": "", "Customer Satisfaction Rating": ""}),
        row(**{"Ticket ID": "2", "Ticket Status": "Open", "Customer Satisfaction Rating": ""}),
        row(**{"Ticket ID": "3", "Customer Satisfaction Rating": "6", "First Response Time": "-2"}),
        row(**{"Ticket ID": "4"}),
        row(**{"Ticket ID": "4", "Ticket Status": "Open"}),
    ]
    result = diagnostic(pd.DataFrame(rows), "fixture")
    total = result["total"]
    assert total["n"] == 3
    assert result["qualidade"]["exclusoes"] == {
        "sem_id": 1,
        "duplicatas_de_linha_com_id": 1,
        "linhas_restantes_com_id_conflitante": 2,
    }
    assert total["inversoes"] == 2
    assert total["nota_invalida"] == 1
    assert total["cobertura_notas"] == pytest.approx(1 / 3)
    assert total["proporcao_4_5"] == 1
    assert all(
        result["qualidade"]["tempo"][k] is None
        for k in ("frt_horas", "ttr_horas", "intervalo_parcial_horas")
    )
    status = {r["status"]: r for r in group_stats(result["cubo"], ("status",))}
    assert status["Open"]["proporcao_4_5"] is None
    assert status["Open"]["n_notas"] == 0


def test_datetime_formats_are_not_duration():
    values = pd.Series(
        ["-5", "0.5", "09:30:00", "2024-02-30 11:00:00", "2024-02-01 11:00:00", None]
    )
    _, stats = timestamp_profile(values)
    assert stats["timestamps_validos"] == 1
    assert stats["numericos_sem_unidade"] == 2
    assert stats["numericos_negativos_sem_unidade"] == 1
    assert stats["outros_ou_invalidos"] == 2


def test_near_duplicate_prefix_search_matches_brute_force():
    a = " ".join(f"token{n}" for n in range(36))
    b = a.replace("token0", "other").replace("token35", "another")
    c = b.replace("token1", "new").replace("token34", "different")
    keys = [a, b, c, "solitary key", "solitary key", "solitary lock"]
    sig = [set(zip(t, t[1:], t[2:])) for t in map(str.split, keys)]
    brute = [{i} for i in range(len(keys))]
    for i, j in itertools.combinations(range(len(keys)), 2):
        union = sig[i] | sig[j]
        if keys[i] == keys[j] or (union and len(sig[i] & sig[j]) / len(union) >= 0.85):
            merged = brute[i] | brute[j]
            for k in merged:
                brute[k] = merged
    groups = near_groups(keys)
    assert [set(j for j, g in enumerate(groups) if g == x) for x in groups] == brute
