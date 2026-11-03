#!/usr/bin/env python3
"""Audit reviewer navigation/capture coverage; record only with explicit --record."""

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOUR = ".tours/assisted-triage.tour"
REPORT = "docs/review-evidence/reviewer-evidence-checks.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_path(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing/outside reviewer target: {name}")
    if any(part in {".venv", ".runtime", "raw", "processed", "models", "runtime"} for part in path.relative_to(root.resolve()).parts):
        raise ValueError(f"Private/local target in review tour: {name}")
    return path


def tour_steps(root):
    tour = json.loads((root / TOUR).read_text())
    if not tour.get("title") or not tour.get("steps") or tour.get("isPrimary") is not True:
        raise ValueError("Expected a titled primary tour with steps")
    if set(tour) - {"$schema", "title", "description", "isPrimary", "steps"}:
        raise ValueError("Unexpected tour properties/actions")
    steps = []
    for step in tour["steps"]:
        if set(step) != {"title", "file", "pattern", "description"} or not step["title"] or not step["description"]:
            raise ValueError("Expected passive titled file/pattern navigation only")
        path = checked_path(root, step["file"])
        matches = [i for i, line in enumerate(path.read_text().splitlines(), 1) if re.search(step["pattern"], line)]
        if len(matches) != 1:
            raise ValueError(f"Tour pattern must match exactly once: {step['file']} / {step['pattern']}")
        steps.append({**step, "line": matches[0], "sha256": digest(path)})
    workspace = json.loads((root / "review.code-workspace").read_text())
    if len(workspace["folders"]) != 1 or workspace["folders"][0]["path"] != "." or workspace["extensions"]["recommendations"] != ["vsls-contrib.codetour"]:
        raise ValueError("Review workspace must use the submission as root")
    if workspace.get("settings", {}).get("codetour.promptForWorkspaceTours") is not True:
        raise ValueError("Review workspace must offer its discovered tour")
    return steps


def captures(root):
    records, seen = [], set()
    secret_patterns = [r"sk-[A-Za-z0-9]{20,}", r"gh[pousr]_[A-Za-z0-9]{30,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"]
    for path in sorted((root / "process-log/chat-exports").glob("*.md")):
        content = path.read_text()
        header = content.split("\n---\n", 1)[0]
        source = re.search(r"^Source: (.+)$", header, re.M)
        captured = re.search(r"^Captured: (.+)$", header, re.M)
        if not source or not captured or "Coverage:" not in header:
            raise ValueError(f"Missing capture provenance/coverage: {path.name}")
        messages = re.findall(r"^## (?:User|Assistant)(?: \([^\n]+\))?\s*$", content, re.M)
        ids = re.findall(r"^Message: `([^`]+)`", content, re.M)
        if not messages or (ids and len(ids) != len(messages)) or seen.intersection(ids) or len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate IDs or inconsistent labeled messages: {path.name}")
        if any(re.search(pattern, content) for pattern in secret_patterns):
            raise ValueError(f"Credential-like content requires manual review: {path.name}")
        seen.update(ids)
        more = re.search(r"hasMore[=:](true|false)", header)
        records.append({"file": path.relative_to(root).as_posix(), "source": source[1], "captured": captured[1],
                        "message_occurrences": len(messages), "explicit_message_ids": len(ids),
                        "represented_turn_ids": len(set(re.findall(r"^Turn: `([^`]+)`", content, re.M))),
                        "has_more_reported": more[1] == "true" if more else None, "sha256": digest(path)})
    return records


def render_tour(steps):
    text = """# CodeTour — roteiro da implementação

Na raiz do repositório, execute:

```bash
bash submissions/giovanne-berteli-comba/review.sh
```

Dentro desta submissão, basta `bash review.sh`. O comando confere/instala o
CodeTour no perfil atual e abre uma nova janela de revisão, preservando a anterior.
Clique **Start CodeTour** na notificação da primeira visita; o tour também aparece
na seção CodeTour do Explorer. Não é necessário procurar diretórios ou configurar
a extensão manualmente. Se a instalação for necessária, ela requer rede/Marketplace.

O [inicializador](../review.sh) abre [review.code-workspace](../review.code-workspace):
a submissão passa a ser a raiz dos caminhos do tour. A extensão não procura
automaticamente todos os `.tours` aninhados no workspace do repositório. O
[arquivo do tour](../.tours/assisted-triage.tour) usa padrões únicos, não executa
comandos e não abre dados locais do teste. Não é necessário usar VS Code para
ler o roteiro abaixo.

O formato foi conferido na [documentação/schema primário](https://github.com/microsoft/codetour).
Os checks locais validam a estrutura usada, workspace, arquivos e uma âncora
única por parada. O [teste real de descoberta/navegação](review-evidence/codetour-discovery.json)
usou VS Code e CodeTour em perfis isolados: a raiz não descobriu o tour, o workspace
correto descobriu e navegou às 11 âncoras. A verificação usa APIs do editor, sem
alegar inspeção visual humana ou screenshots. Nenhuma configuração global foi alterada.

## Roteiro sem extensão

"""
    for step in steps:
        text += f"### {step['title']}\n\n[{step['file']}:{step['line']}](../{step['file']}#L{step['line']})\n\n{step['description']}\n\n"
    return text.rstrip() + "\n"


def render_coverage(records):
    messages = sum(r["message_occurrences"] for r in records)
    ids = sum(r["explicit_message_ids"] for r in records)
    text = f"""# Cobertura das conversas preservadas

Este inventário descreve os arquivos locais disponíveis para recrutamento; não é
prova de completude da plataforma. Há **{len(records)} capturas**, **{messages} ocorrências
de mensagens** e **{ids} IDs explícitos distintos**, sem duplicação desses IDs.
As {messages - ids} ocorrências sem ID continuam sem deduplicação global comprovada.
Contagens de turnos abaixo são os representados no arquivo após deduplicação,
não o número de turnos retornados pela API; cada cabeçalho declara sua cobertura.

| Captura | Mensagens | IDs explícitos | Turnos representados | hasMore no cabeçalho |
| --- | ---: | ---: | ---: | --- |
"""
    for record in records:
        more = "true" if record["has_more_reported"] else "false" if record["has_more_reported"] is False else "não extraído"
        text += f"| [{Path(record['file']).name}](../{record['file']}) | {record['message_occurrences']} | {record['explicit_message_ids']} | {record['represented_turn_ids']} | {more} |\n"
    text += """
As três primeiras capturas não registram IDs por mensagem. `hasMore=false` não
comprova mensagens excluídas, editadas, ramificações ou anexos recuperados;
`hasMore=true` indica paginação anterior fora daquela leitura. As extrações
retêm usuário/assistente no idioma original; não são exports nativos completos.
Ferramentas, raciocínio privado, instruções internas, imagens e gravações não
integram essas capturas. Não há export de Claude Code ou Gemini para alegar uso.

O arquivo mais recente declara seu corte e suas lacunas: mensagens
posteriores, inclusive a resposta final ainda inexistente na captura, ficam para
próxima extração. Não foram reconstruídas como citação. Um scan de padrões comuns
de credenciais não encontrou correspondências; isso é um check limitado, não uma
certificação de privacidade ou de revisão humana. Veja o [process log](../process-log/README.md).

O process log é evidência histórica, fora do contexto operacional padrão. Decisões
atuais continuam nos donos indicados em [status](../PROJECT_STATUS.md) e
[conhecimento](../knowledge/index.md).
"""
    return text


def audit(root, record=False):
    steps, records = tour_steps(root), captures(root)
    readme = (root / "README.md").read_text()
    for heading in ["## Sobre mim", "## Executive Summary", "## Solução", "### Abordagem", "### Resultados / Findings", "### Recomendações", "### Limitações", "## Process Log — Como usei IA", "### Ferramentas usadas", "### Workflow", "### Onde a IA errou e como corrigi", "### O que eu adicionei que a IA sozinha não faria", "## Evidências"]:
        if heading not in readme:
            raise ValueError(f"Missing submission-template heading: {heading}")
    summary = readme.split("## Executive Summary\n", 1)[1].split("\n## ", 1)[0].strip()
    sentences = [s for s in re.split(r"[.!?](?:\s+|$)", summary) if s.strip()]
    if not 3 <= len(sentences) <= 5:
        raise ValueError("Executive summary must have 3–5 sentences")
    final = json.loads((root / "data/final-evaluation.json").read_text())
    a = final["assisted"]
    comma = lambda value, places: f"{value:.{places}f}".replace(".", ",")
    required = [comma(final["classifier_metrics"][final["selected_model"]]["macro_f1"], 6),
                comma(final["classifier_metrics"]["multinomial_nb"]["macro_f1"], 6),
                comma(a["standard_coverage"] * 100, 2) + "%", comma(a["standard_accuracy"] * 100, 2) + "%",
                f"{a['standard_cases']:,}/{final['population']:,}".replace(",", ".")]
    if any(token not in readme for token in required) or re.search(r"\d,\s+\d", readme):
        raise ValueError("README headline metrics/decimal formatting differ from original result")
    for name in ("docs/final-evaluation.md", "knowledge/final-evaluation.md"):
        if re.search(r"\d,\s+\d", (root / name).read_text()):
            raise ValueError(f"Broken numeric punctuation in reader summary: {name}")
    rendered = {"docs/code-tour.md": render_tour(steps), "docs/conversation-coverage.md": render_coverage(records)}
    for name, content in rendered.items():
        if record:
            (root / name).write_text(content)
        elif not (root / name).exists() or (root / name).read_text() != content:
            raise ValueError(f"Generated navigation/coverage changed: rerun review before --record: {name}")
    names = {TOUR, "review.sh", "review.code-workspace", "README.md", "docs/review-guide.md", "docs/review-evidence/codetour-discovery.json", "docs/final-evaluation.md", "knowledge/final-evaluation.md", "scripts/check_review_evidence.py", "data/final-evaluation.json"} | set(rendered)
    names |= {r["file"] for r in records} | {step["file"] for step in steps}
    result = {"scope": "Reviewer presentation, passive tour paths/unique patterns, capture inventory, headline metrics and known credential patterns; not full schema/UI/privacy certification or human verification",
              "tour_steps": [{key: step[key] for key in ("title", "file", "line", "sha256")} for step in steps],
              "captures": records, "message_occurrences": sum(r["message_occurrences"] for r in records),
              "distinct_explicit_message_ids": sum(r["explicit_message_ids"] for r in records),
              "duplicate_explicit_ids": 0, "executive_summary_sentences": len(sentences),
              "headline_metric_tokens_matched": required, "credential_pattern_matches": 0,
              "limits": "Legacy messages without IDs, API pagination, incomplete/edited/deleted branches, absent attachments/native exports and messages after the current capture remain explicit gaps; no new model inference or fitting",
              "input_sha256": {name: digest(root / name) for name in sorted(names)}}
    if record:
        (root / REPORT).write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    elif json.loads((root / REPORT).read_text()) != result:
        raise ValueError("Review evidence changed; inspect it before explicitly recording another version")
    return {"passed": True, "tour_steps": len(steps), "capture_files": len(records),
            "message_occurrences": result["message_occurrences"], "distinct_explicit_message_ids": result["distinct_explicit_message_ids"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true", help="Explicitly regenerate navigation/inventory after reviewing inputs")
    args = parser.parse_args()
    try:
        print(json.dumps(audit(ROOT, args.record), indent=2))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Reviewer evidence check failed: {error}\n")
