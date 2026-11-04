import hashlib
import sys

from comum import DATA_DIR, DS1_ARQUIVO, DS2_ARQUIVO, ler_ds1, ler_ds2, salvar_json

ESPERADO = {
    DS1_ARQUIVO: {
        "linhas": 8469,
        "colunas": ["Ticket ID", "Ticket Type", "Ticket Description", "Ticket Status", "Resolution",
                    "Ticket Priority", "Ticket Channel", "First Response Time", "Time to Resolution",
                    "Customer Satisfaction Rating"],
    },
    DS2_ARQUIVO: {"linhas": 47837, "colunas": ["Document", "Topic_group"]},
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def main():
    leitores = {DS1_ARQUIVO: ler_ds1, DS2_ARQUIVO: lambda: ler_ds2().drop(columns="id")}
    saida, problemas = {"data_dir": "$DATA_DIR (padrão ../../../data relativo à submissão)", "arquivos": []}, []
    for nome, esp in ESPERADO.items():
        p = DATA_DIR / nome
        df = leitores[nome]()
        with open(p, "rb") as f:
            linhas_fisicas = sum(1 for _ in f)
        faltando = [c for c in esp["colunas"] if c not in df.columns]
        info = {
            "nome": nome, "bytes": p.stat().st_size, "sha256": sha256(p),
            "linhas_dados": len(df), "linhas_fisicas_arquivo": linhas_fisicas,
            "linhas_esperadas": esp["linhas"], "colunas": list(df.columns), "colunas_faltando": faltando,
        }
        saida["arquivos"].append(info)
        if len(df) != esp["linhas"]:
            problemas.append(f"{nome}: {len(df)} linhas, esperado {esp['linhas']}")
        if faltando:
            problemas.append(f"{nome}: faltam colunas {faltando}")
        print(f"{nome}: {len(df)} linhas de dados ({linhas_fisicas} físicas), {len(df.columns)} colunas, sha256 {info['sha256'][:12]}…")
    saida["ok"] = not problemas
    saida["problemas"] = problemas
    salvar_json(saida, "f1_dados.json")
    if problemas:
        print("PARAR:", *problemas, sep="\n  ")
        sys.exit(1)
    print("OK: linhas e colunas conferem.")


if __name__ == "__main__":
    main()
