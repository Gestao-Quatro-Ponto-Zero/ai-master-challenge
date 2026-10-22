"""Motor da Triagem: lê o ticket, decide e redige. Junta sinais, regras e redação.

Uso (da pasta submissions/vinicius-alves):
    python3 solution/motor/motor.py              roda nos 80 tickets, mede contra o gabarito e gera a tela
    python3 solution/motor/motor.py --sem-tela   só mede
    python3 solution/motor/motor.py --novos      roda nos 30 tickets novos (teste cego) e mede contra a referência

Sem dependências além do Python. Sem chave de API.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from redacao import rascunho, resumo, trava  # noqa: E402
from regras import decide  # noqa: E402
from sinais import le  # noqa: E402

SOLUCAO = AQUI.parent
CASOS = SOLUCAO / "teste/casos_teste.csv"
GABARITO = SOLUCAO / "teste/gabarito_preenchido.csv"
SAIDA = SOLUCAO / "teste/resultado_motor.csv"
# Teste cego: 30 tickets escritos depois das regras. O resultado da versão 1 fica em resultado_motor_novos_v1.csv.
CASOS_NOVOS = SOLUCAO / "teste/casos_novos.csv"
REFERENCIA_NOVOS = SOLUCAO / "teste/referencia_novos.csv"
SAIDA_NOVOS = SOLUCAO / "teste/resultado_motor_novos.csv"
TELA = SOLUCAO / "interface/dados.js"

# Nomes fictícios, fixos e sem repetir. O Dataset 1 tem nomes inventados em inglês.
PRIMEIROS = ["Camila", "Rafael", "Bruno", "Larissa", "Juliana", "Ricardo", "Paulo", "Fernanda", "Anderson", "Sueli",
             "Gustavo", "Helena", "Marcos", "Patrícia", "Diego", "Renata", "Thiago", "Aline", "Eduardo", "Mariana",
             "Felipe", "Beatriz", "Lucas", "Vanessa", "Otávio", "Lívia", "Caio", "Débora", "Rodrigo", "Simone",
             "André", "Tatiana", "Henrique", "Bianca", "Vitor", "Carolina", "Fábio", "Natália", "Leandro", "Priscila"]
SOBRENOMES = ["Duarte", "Moreira", "Takeda", "Fontes", "Prado", "Menezes", "Arantes", "Castilho", "Ribeiro", "Martins",
              "Rocha", "Bastos", "Lopes", "Lemos", "Albuquerque", "Siqueira", "Barreto", "Cardoso", "Nogueira", "Teles",
              "Antunes", "Queiroz", "Pimenta", "Rangel", "Freitas", "Coelho", "Vasconcelos", "Paiva", "Brandão", "Sales",
              "Moura", "Guedes", "Peixoto", "Andrade", "Farias", "Leite", "Campos", "Xavier", "Aguiar", "Rezende"]
NOMES = [f"{p} {s}" for p, s in zip(PRIMEIROS, SOBRENOMES)] + [f"{p} {s}" for p, s in zip(PRIMEIROS, reversed(SOBRENOMES))]
ASSUNTO_PT = {
    "Account access": "Acesso à conta", "Battery life": "Bateria", "Cancellation request": "Cancelamento",
    "Data loss": "Perda de dados", "Delivery problem": "Entrega", "Display issue": "Tela", "Hardware issue": "Defeito",
    "Installation support": "Instalação", "Network problem": "Conexão", "Payment issue": "Pagamento",
    "Peripheral compatibility": "Compatibilidade", "Product compatibility": "Compatibilidade",
    "Product recommendation": "Recomendação", "Product setup": "Configuração", "Refund request": "Reembolso",
    "Software bug": "Software",
}
ROTULO_ACAO ={"A": "IA responde", "B": "IA resolve", "C": "Resumo pro atendente", "D": "Pessoa agora", "E": "Pergunta ao cliente"}
VAI_PRA_PESSOA = {"C", "D"}


def carregar(caminho):
    with open(caminho, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def processa(t):
    s = le(t)
    d = decide(t, s)
    texto, ja_enviado = rascunho(t, s, d)
    return s, d, texto, ja_enviado


def tipo_de_erro(certo, motor):
    """Erro perigoso: a IA ficou com o caso quando devia ir pra pessoa.
    Erro cauteloso: mandou pra pessoa sem precisar. Outro: trocou entre ações da IA."""
    if certo == motor:
        return ""
    if certo in VAI_PRA_PESSOA and motor not in VAI_PRA_PESSOA:
        return "perigoso"
    if motor in VAI_PRA_PESSOA and certo not in VAI_PRA_PESSOA:
        return "cauteloso"
    return "outro"


def main(gerar_tela=True, casos=CASOS, gabarito=GABARITO, saida=SAIDA):
    casos = carregar(casos)
    gabarito = {g["id"]: g["acao"] for g in carregar(gabarito)}
    linhas, problemas_trava = [], []

    for i, t in enumerate(casos):
        t["cliente"] = NOMES[i % len(NOMES)]
        s, d, texto, ja_enviado = processa(t)
        if trava(texto):
            problemas_trava.append((t["id"], trava(texto)))
        linhas.append({
            "id": t["id"], "gabarito": gabarito.get(t["id"], ""), "motor": d.acao,
            "erro": tipo_de_erro(gabarito.get(t["id"], ""), d.acao),
            "regra": d.regra, "processo": d.processo, "porque": d.porque,
            "sinais": "; ".join(f"{k}={v}" for k, v in s.items()), "rascunho": texto,
            "_t": t, "_s": s, "_d": d, "_ja": ja_enviado,
        })

    # ---- Medição ----
    n = len(linhas)
    certos = sum(1 for l in linhas if l["gabarito"] == l["motor"])
    erros = Counter(l["erro"] for l in linhas if l["erro"])
    print(f"Acerto contra o gabarito: {certos}/{n} ({certos / n:.0%})")
    print(f"Erros perigosos (IA ficou com o que era de pessoa): {erros['perigoso']}")
    print(f"Erros cautelosos (mandou pra pessoa sem precisar): {erros['cauteloso']}")
    print(f"Outros (trocou A, B ou E entre si): {erros['outro']}")
    print(f"Rascunhos barrados pela trava: {len(problemas_trava)}")
    for l in linhas:
        if l["erro"]:
            print(f"  {l['id']}: gabarito {l['gabarito']}, motor {l['motor']} ({l['erro']}) · {l['regra']} · {l['sinais'] or 'sem sinais'}")
    for id_, achados in problemas_trava:
        print(f"  TRAVA {id_}: {achados}")

    print("\nMatriz (linhas = gabarito, colunas = motor)")
    print("     " + "  ".join(a for a in "ABCDE"))
    for g in "ABCDE":
        print(f"  {g}  " + "  ".join(f"{sum(1 for l in linhas if l['gabarito'] == g and l['motor'] == m):>1}" for m in "ABCDE"))

    with open(saida, "w", newline="", encoding="utf-8-sig") as f:
        campos = ["id", "gabarito", "motor", "erro", "regra", "processo", "porque", "sinais", "rascunho"]
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)
    print(f"\nResultado por ticket em {saida.relative_to(SOLUCAO.parent)}")

    if gerar_tela:
        exporta_tela(linhas)
    return linhas


def exporta_tela(linhas):
    """Gera interface/dados.js com o que o motor decidiu. A espera é simulada:
    o Dataset 1 não registra quando o ticket foi aberto."""
    faixa = {"D": (3, 45), "C": (8, 60), "E": (2, 15), "B": (1, 6), "A": (1, 12)}
    tickets = []
    for i, l in enumerate(linhas):
        t, d, s = l["_t"], l["_d"], l["_s"]
        lo, hi = faixa[d.acao]
        espera = lo + (sum(map(ord, t["id"])) * 7 + i) % (hi - lo + 1)
        dias = t["dias_desde_compra"]
        valor = t["valor_rs"]
        tickets.append({
            "id": t["id"], "acao": d.acao, "espera": espera, "cliente": t["cliente"],
            "produto": t["produto"] or "Sem pedido", "canal": t["canal"], "assunto": ASSUNTO_PT.get(t["assunto_d1"], t["tipo"]),
            "valor": f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if valor else "-",
            "dias": f"{dias} dias" if dias not in ("", None) else "-", "status": t["status_pedido"],
            "contatos": f"{t['contatos_anteriores']}º contato" if t["contatos_anteriores"] != "0" else "Primeiro",
            "msg": t["mensagem_do_cliente"], "regra": d.regra, "processo": d.processo or "Sem processo",
            "porque": d.porque, "resumo": resumo(t, s, d), "rascunho": l["rascunho"], "barrado": [],
            "jaEnviado": l["_ja"],
        })
    # Duas conversas já com outra atendente, pra a tela mostrar o time trabalhando.
    for x in tickets:
        if x["id"] in ("R01", "R07"):
            x["dono"] = "Ana Prado"
    from testar_trava import TEM_QUE_BARRAR
    exemplos = [{"frase": f, "motivo": trava(f)[0][1]} for f in TEM_QUE_BARRAR if trava(f)]
    cab = ("// Gerado por solution/motor/motor.py a partir dos 80 tickets de teste.\n"
           "// Não edite à mão: rode o motor de novo.\n")
    TELA.write_text(cab + "window.TICKETS = " + json.dumps(tickets, ensure_ascii=False, indent=1) + ";\n"
                    + "window.TRAVA_EXEMPLOS = " + json.dumps(exemplos, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    print(f"Tela atualizada: {TELA.relative_to(SOLUCAO.parent)} ({len(tickets)} tickets)")


if __name__ == "__main__":
    if "--novos" in sys.argv:
        main(gerar_tela=False, casos=CASOS_NOVOS, gabarito=REFERENCIA_NOVOS, saida=SAIDA_NOVOS)
    else:
        main(gerar_tela="--sem-tela" not in sys.argv)
