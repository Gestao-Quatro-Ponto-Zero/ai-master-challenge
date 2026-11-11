#!/usr/bin/env python3
"""Registrador de uso de IA: grava o diário e mantém os contadores do REGISTRO.md.

Só biblioteca padrão, compatível com Python 3.9 (o avaliador pode ter o Python do sistema).
Todo arquivo é texto, para que o histórico do git conte a história sozinho.

  registrar.py --inicio "Tarefa 3" [--modelo claude-opus-5] [--ferramenta "Claude Code"]
  registrar.py --pedi "..." --veio "..." --mudei "..."
  registrar.py --erro "..." [--propos "..."] --pego-por "..." --teste "..." --ficou "..."
  registrar.py --nota "..."
  registrar.py --fim "Tarefa 3 verde, 7 testes"
  registrar.py --conferir
"""
import argparse
import datetime as dt
import pathlib
import re
import sys

AQUI = pathlib.Path(__file__).resolve().parent
DIARIO = AQUI / "diario.md"
REGISTRO = AQUI / "REGISTRO.md"
MODELOS = AQUI / "MODELOS.md"
ERROS = AQUI / "onde-a-ia-errou.md"
ACRESCENTEI = AQUI / "o-que-eu-acrescentei.md"

MODELO_PADRAO = "claude-opus-5"
FERRAMENTA_PADRAO = "Claude Code"
MARCA_EXEMPLO = "<!-- exemplo: apague esta linha ao preencher -->"


def agora():
    return dt.datetime.now().astimezone()


def acrescentar(caminho, texto):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    anterior = caminho.read_text(encoding="utf-8") if caminho.exists() else ""
    if anterior and not anterior.endswith("\n"):
        anterior += "\n"
    caminho.write_text(anterior + texto, encoding="utf-8")


def sessoes_abertas():
    """Devolve a lista de (titulo, inicio) de sessões sem fechamento, na ordem do arquivo.

    Uma sessão abandonada no meio do diário também conta: o `--fim` seguinte fecha a sessão
    que estava aberta na hora, não todas as anteriores.
    """
    if not DIARIO.exists():
        return []
    abertas = []
    for linha in DIARIO.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## (\S+ \S+) · (.+?) · modelo ", linha)
        if m:
            abertas.append((m.group(2), m.group(1)))
        elif linha.startswith("**Fim da sessão") and abertas:
            abertas.pop()
    return abertas


def sessao_aberta():
    """A sessão aberta mais recente, ou None."""
    abertas = sessoes_abertas()
    return abertas[-1] if abertas else None


def cmd_inicio(a):
    if sessao_aberta():
        titulo, quando = sessao_aberta()
        print(f"aviso: a sessão '{titulo}' (aberta em {quando}) não foi fechada. Feche com --fim antes de abrir outra.", file=sys.stderr)
    t = agora()
    acrescentar(DIARIO, "\n## {} · {} · modelo {} · ferramenta {}\n".format(
        t.strftime("%Y-%m-%d %H:%M"), a.inicio, a.modelo, a.ferramenta))
    print("sessão aberta:", a.inicio, "| modelo:", a.modelo)
    if MODELOS.exists() and a.modelo not in MODELOS.read_text(encoding="utf-8"):
        print(f"aviso: {a.modelo} não está em MODELOS.md. Acrescente a linha com versão, papel e custo.", file=sys.stderr)


def cmd_iteracao(a):
    if not sessao_aberta():
        print("aviso: nenhuma sessão aberta. Rode --inicio primeiro (a entrada vai ser gravada de todo modo).", file=sys.stderr)
    t = agora().strftime("%H:%M")
    acrescentar(DIARIO, "\n- **{}** — pedi: {}\n  - veio: {}\n  - mudei: {}\n".format(
        t, a.pedi, a.veio or "(nada registrado)", a.mudei or "(nada mudou)"))
    print("iteração registrada")


def cmd_erro(a):
    if not (a.teste or a.pego_por):
        print("erro: um erro da IA sem o mecanismo que o pegou não é evidência. Use --teste ou --pego-por.", file=sys.stderr)
        return 1
    t = agora()
    propos = a.propos or a.erro
    acrescentar(DIARIO, "\n- **{}** — ERRO DA IA: {}\n  - propôs: {}\n  - pego por: {}\n  - teste: {}\n  - ficou: {}\n".format(
        t.strftime("%H:%M"), a.erro, propos, a.pego_por or "(não informado)",
        a.teste or "(sem teste nomeado)", a.ficou or "(pendente)"))
    acrescentar(ERROS, "\n## {}\n\n- **O que a IA propôs:** {}\n- **Como foi pego:** {}\n- **Teste que fixa:** {}\n- **O que ficou:** {}\n- **Quando:** {}\n".format(
        a.erro, propos, a.pego_por or "(não informado)", a.teste or "(sem teste nomeado)",
        a.ficou or "(pendente)", t.strftime("%Y-%m-%d %H:%M")))
    print("erro registrado no diário e em onde-a-ia-errou.md")
    return 0


def cmd_nota(a):
    acrescentar(DIARIO, "\n- **{}** — nota: {}\n".format(agora().strftime("%H:%M"), a.nota))
    print("nota registrada")


def cmd_fim(a):
    aberta = sessao_aberta()
    if not aberta:
        print("aviso: nenhuma sessão aberta para fechar.", file=sys.stderr)
    t = agora()
    acrescentar(DIARIO, "\n**Fim da sessão** {} — {}\n".format(t.strftime("%Y-%m-%d %H:%M"), a.fim))
    print("sessão fechada:", aberta[0] if aberta else "(sem título)")
    contar(imprimir=True)


def contar(imprimir=False):
    """Conta sessões, iterações e erros registrados."""
    texto = DIARIO.read_text(encoding="utf-8") if DIARIO.exists() else ""
    sessoes = len(re.findall(r"^## \S+ \S+ · ", texto, re.M))
    iteracoes = len(re.findall(r"— pedi:", texto))
    erros = len(re.findall(r"— ERRO DA IA:", texto))
    modelos = sorted(set(re.findall(r"· modelo (\S+)", texto)))
    if imprimir:
        print("sessões: {} | iterações: {} | erros da IA pegos: {} | modelos: {}".format(
            sessoes, iteracoes, erros, ", ".join(modelos) or "nenhum"))
    return dict(sessoes=sessoes, iteracoes=iteracoes, erros=erros, modelos=modelos)


def cmd_conferir(_a):
    problemas = []
    c = contar(imprimir=True)

    for titulo, quando in sessoes_abertas():
        problemas.append("a sessão '{}' (aberta em {}) nunca foi fechada".format(titulo, quando))
    if c["sessoes"] == 0:
        problemas.append("o diário não tem nenhuma sessão")
    if c["iteracoes"] < 3:
        problemas.append("só {} iterações registradas; um process log com uma ida e volta parece prompt único".format(c["iteracoes"]))
    if c["erros"] == 0:
        problemas.append("nenhum erro da IA registrado; se nada foi pego, o registro não mostra verificação")

    if not MODELOS.exists():
        problemas.append("MODELOS.md não existe")
    else:
        texto = MODELOS.read_text(encoding="utf-8")
        if MARCA_EXEMPLO in texto:
            problemas.append("MODELOS.md ainda tem linha de exemplo")
        for m in c["modelos"]:
            if m not in texto:
                problemas.append("o modelo {} aparece no diário e não está em MODELOS.md".format(m))

    for caminho, nome in ((ERROS, "onde-a-ia-errou.md"), (ACRESCENTEI, "o-que-eu-acrescentei.md"), (REGISTRO, "REGISTRO.md")):
        if not caminho.exists():
            problemas.append("{} não existe".format(nome))
        elif MARCA_EXEMPLO in caminho.read_text(encoding="utf-8"):
            problemas.append("{} ainda tem conteúdo de exemplo".format(nome))

    if ERROS.exists() and "(sem teste nomeado)" in ERROS.read_text(encoding="utf-8"):
        problemas.append("há erro da IA sem teste nomeado em onde-a-ia-errou.md")
    if ERROS.exists() and "(pendente)" in ERROS.read_text(encoding="utf-8"):
        problemas.append("há erro da IA com correção pendente em onde-a-ia-errou.md")

    if problemas:
        print("\nPendências ({}):".format(len(problemas)))
        for p in problemas:
            print("  -", p)
        return 1
    print("\nRegistro completo. Nenhuma pendência.")
    return 0


def main():
    p = argparse.ArgumentParser(description="Registrador de uso de IA")
    p.add_argument("--inicio", help="abre uma sessão com este título")
    p.add_argument("--modelo", default=MODELO_PADRAO)
    p.add_argument("--ferramenta", default=FERRAMENTA_PADRAO)
    p.add_argument("--pedi")
    p.add_argument("--veio")
    p.add_argument("--mudei")
    p.add_argument("--erro", help="título do erro")
    p.add_argument("--propos", help="o que a IA propôs, quando for diferente do título")
    p.add_argument("--pego-por", dest="pego_por")
    p.add_argument("--teste")
    p.add_argument("--ficou")
    p.add_argument("--nota")
    p.add_argument("--fim", help="fecha a sessão com este resumo")
    p.add_argument("--conferir", action="store_true")
    a = p.parse_args()

    if a.conferir:
        return cmd_conferir(a)
    if a.inicio:
        return cmd_inicio(a) or 0
    if a.erro:
        return cmd_erro(a)
    if a.pedi:
        return cmd_iteracao(a) or 0
    if a.nota:
        return cmd_nota(a) or 0
    if a.fim:
        return cmd_fim(a) or 0
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
