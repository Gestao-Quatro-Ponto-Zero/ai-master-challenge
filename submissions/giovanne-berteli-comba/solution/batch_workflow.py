"""Durable batch decisions and a preplanned manual/assisted usability rehearsal.

The frozen inference service is reused, not edited. Timers describe server elapsed
workflow time; actor identity is declared. Human benefit is never manufactured.
"""

import csv
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import uuid

from triage.artifacts import ROOT, sha256
from triage.core import CLASSES, MAX_CHARS, normalize
from triage.repository import Repository
from triage.runtime import TriageService

MAX_ROWS = 50
MAX_BYTES = 2_000_000
ACTORS = {"operator_declared", "automated_test"}


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def validate_rows(rows):
    if not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError(f"Use 1 a {MAX_ROWS} tickets por lote.")
    cleaned, seen = [], set()
    for row in rows:
        ticket = row.get("ticket_id", "").strip()
        text = row.get("text", "")
        reference = row.get("reference_category") or None
        if not ticket or len(ticket) > 120 or ticket in seen:
            raise ValueError("ticket_id deve ser único no lote, não vazio e ter até 120 caracteres.")
        if not isinstance(text, str) or not normalize(text) or len(text) > MAX_CHARS or len(normalize(text)) > MAX_CHARS:
            raise ValueError("Cada texto deve ter conteúdo e até 10.000 caracteres; nada será truncado.")
        if reference is not None and reference not in CLASSES:
            raise ValueError("Categoria de referência inválida.")
        seen.add(ticket)
        cleaned.append({"ticket_id": ticket, "text": text, "reference_category": reference,
                        "source": row.get("source", {"dataset": "uploaded_it", "partition": "user_upload"})})
    return cleaned


def parse_csv(payload):
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise ValueError("CSV deve ter até 2 MB.")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""), strict=True)
        fields = reader.fieldnames or []
        if (len(fields) != len(set(fields)) or not {"ticket_id", "text"} <= set(fields)
                or set(fields) - {"ticket_id", "text", "reference_category"}):
            raise ValueError("Use as colunas ticket_id,text e, opcionalmente, reference_category.")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("CSV contém linha com colunas faltando ou em excesso.")
            rows.append(row)
            if len(rows) > MAX_ROWS:
                raise ValueError(f"Limite de {MAX_ROWS} tickets por lote.")
        return validate_rows(rows)
    except (UnicodeError, csv.Error) as error:
        raise ValueError("Não foi possível ler um CSV UTF-8 válido.") from error


def decisions_csv(rows):
    fields = ["batch_id", "ticket_id", "mode", "run_id", "suggested_category", "final_category", "model_version", "review_state", "actor_type"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: ("'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v) for k,v in row.items()})
    return stream.getvalue()


def pilot_sample(seed, root=ROOT):
    """Sample development tasks without inspecting predictions or final members."""
    manifest = json.loads((root / "data/evaluation-manifest.json").read_text())
    membership = root / manifest["membership"]["path"]
    source = json.loads((root / "data/manifest.json").read_text())["datasets"]["it_service"]["file"]
    if sha256(membership) != manifest["membership"]["sha256"] or sha256(root / source["path"]) != source["sha256"]:
        raise ValueError("Fontes do ensaio diferem dos dados versionados.")
    with membership.open(newline="") as handle:
        train = {int(r["row_index"]): r for r in csv.DictReader(handle) if r["partition"] == "train"}
    groups = {label: [] for label in CLASSES}
    with (root / source["path"]).open(encoding="utf-8-sig", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle), 1):
            if index not in train:
                continue
            member = train[index]
            groups[row["Topic_group"]].append({"ticket_id": member["case_id"], "text": row["Document"],
                "reference_category": row["Topic_group"], "source": {"dataset": "it_service", "partition": "train", "case_id": member["case_id"], "group_id": member["group_id"]}})
    arms, used = {"manual": [], "assisted": []}, set()
    for label in CLASSES:
        candidates = sorted(groups[label], key=lambda r: digest(seed + r["ticket_id"]))
        first = next(r for r in candidates if r["source"]["group_id"] not in used)
        used.add(first["source"]["group_id"])
        second = min((r for r in candidates if r["source"]["group_id"] not in used),
                     key=lambda r: (abs(len(r["text"]) - len(first["text"])), digest(seed + r["ticket_id"])))
        used.add(second["source"]["group_id"])
        pair = [first, second] if int(digest(seed + label)[0], 16) % 2 else [second, first]
        for mode, row in zip(("manual", "assisted"), pair):
            arms[mode].append(row)
    return {"arms": arms, "source_sha256": source["sha256"], "membership_sha256": manifest["membership"]["sha256"]}


class WorkflowStore:
    def __init__(self, path, clock=utc):
        self.path, self.clock = Path(path), clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS wf_batches (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS wf_events (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
                    batch_id TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS wf_studies (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def _read(self, db, table, identifier):
        row = db.execute(f"SELECT payload FROM {table} WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ValueError("Registro não encontrado.")
        return json.loads(row[0])

    def _put(self, db, table, value):
        db.execute(f"UPDATE {table} SET payload=? WHERE id=?", (encode(value), value["id"]))

    def _event(self, db, identifier, kind, payload, event_id=None):
        db.execute("INSERT INTO wf_events(id,batch_id,kind,payload,created_at) VALUES (?,?,?,?,?)",
                   (event_id or str(uuid.uuid4()), identifier, kind, encode(payload), self.clock()))

    def _new(self, mode, operator, actor_type, identifier, purpose="operation", study_id=None):
        if mode not in {"manual", "assisted"} or actor_type not in ACTORS or not operator.strip() or len(operator) > 120:
            raise ValueError("Informe modo, identificação (até 120 caracteres) e tipo de participante válidos.")
        return {"id": identifier, "mode": mode, "operator": operator.strip(), "actor_type": actor_type,
                "purpose": purpose, "study_id": study_id, "state": "active", "started_at": self.clock(),
                "finished_at": None, "revision": 0, "items": [], "content_sha256": None, "artifact": None}

    def start(self, mode, operator, actor_type, request_id):
        identifier = "batch-" + digest(request_id)[:32]
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            exists = db.execute("SELECT payload FROM wf_batches WHERE id=?", (identifier,)).fetchone()
            if exists:
                batch = json.loads(exists[0])
                if (batch["mode"], batch["operator"], batch["actor_type"]) != (mode, operator.strip(), actor_type):
                    raise ValueError("Identificador já usado para outro início.")
                return identifier
            batch = self._new(mode, operator, actor_type, identifier)
            db.execute("INSERT INTO wf_batches VALUES (?,?)", (identifier, encode(batch)))
            self._event(db, identifier, "started", {"mode": mode, "actor_type": actor_type})
        return identifier

    def batch(self, identifier):
        with self.connect() as db:
            return self._read(db, "wf_batches", identifier)

    def batches(self):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT payload FROM wf_batches ORDER BY rowid DESC")]

    def attach(self, identifier, rows):
        rows = validate_rows(rows)
        fingerprint = digest(encode(rows))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            batch = self._read(db, "wf_batches", identifier)
            if batch["content_sha256"] == fingerprint:
                return
            if batch["state"] != "active" or batch["items"]:
                raise ValueError("O conteúdo do lote já foi fixado e não pode ser substituído.")
            batch["items"] = [{**r, "prediction": None} for r in rows]
            batch["content_sha256"] = fingerprint
            batch["revision"] += 1
            self._put(db, "wf_batches", batch)
            self._event(db, identifier, "imported", {"rows": len(rows), "sha256": fingerprint})

    def prepare(self, identifier, service=None, progress=None):
        batch = self.batch(identifier)
        if batch["mode"] != "assisted" or batch["state"] != "active" or not batch["items"]:
            raise ValueError("Sugestões exigem um lote assistido ativo e importado.")
        service = service or TriageService(Repository(self.path))
        for index, item in enumerate(batch["items"]):
            if item["prediction"] is None:
                token = digest(identifier + ":" + item["ticket_id"])
                result = service.submit(item["text"], "it_service_en", request_id="batch:"+token,
                                        case_id="batch:"+token, source=item["source"])
                with self.connect() as db:
                    db.execute("BEGIN IMMEDIATE")
                    current = self._read(db, "wf_batches", identifier)
                    if current["items"][index]["prediction"] is None:
                        if current["state"] != "active":
                            raise ValueError("Lote encerrado durante a preparação.")
                        current["items"][index]["prediction"] = result
                        current["revision"] += 1
                        self._put(db, "wf_batches", current)
                        self._event(db, identifier, "suggestion_attempt", {"ticket_id": item["ticket_id"], "run_id": result["run_id"],
                                    "persisted": result["persisted"], "outcome": result["outcome"]})
            if progress:
                progress(index+1, len(batch["items"]))

    def decisions(self, identifier):
        latest = {}
        for event in self.events(identifier):
            if event["kind"] == "decisions":
                latest.update(event["payload"]["choices"])
        return latest

    def save_decisions(self, identifier, choices, event_id, expected_revision):
        if not choices or any(not isinstance(k,str) or v not in CLASSES for k,v in choices.items()):
            raise ValueError("Marque linhas revisadas e escolha uma categoria IT válida para cada uma.")
        payload = {"choices": choices}
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT batch_id,payload FROM wf_events WHERE id=?", (event_id,)).fetchone()
            if previous:
                if previous != (identifier, encode(payload)):
                    raise ValueError("Identificador da decisão já usado para outro conteúdo.")
                return
            batch = self._read(db, "wf_batches", identifier)
            if batch["state"] != "active" or batch["revision"] != expected_revision:
                raise ValueError("Lote encerrado ou atualizado em outra ação. Recarregue antes de confirmar.")
            if not set(choices) <= {r["ticket_id"] for r in batch["items"]}:
                raise ValueError("Decisão aponta para ticket fora do lote.")
            if batch["mode"] == "assisted" and any(r["prediction"] is None for r in batch["items"]):
                raise ValueError("Registre as tentativas de sugestão antes da revisão assistida.")
            self._event(db, identifier, "decisions", payload, event_id)
            batch["revision"] += 1
            self._put(db, "wf_batches", batch)

    def events(self, identifier):
        with self.connect() as db:
            return [{"seq": seq, "event_id": eid, "kind": kind, "payload": json.loads(payload), "created_at": stamp}
                    for seq,eid,kind,payload,stamp in db.execute("SELECT seq,id,kind,payload,created_at FROM wf_events WHERE batch_id=? ORDER BY seq", (identifier,))]

    def note_import_failure(self, identifier, reason):
        with self.connect() as db:
            batch = self._read(db, "wf_batches", identifier)
            if batch["state"] == "active":
                self._event(db, identifier, "import_failed", {"reason": reason})

    def audit(self, identifier):
        batch = self.batch(identifier)
        return {"batch_id":identifier,"mode":batch["mode"],"purpose":batch["purpose"],"actor_type":batch["actor_type"],
                "state":batch["state"],"started_at":batch["started_at"],"finished_at":batch["finished_at"],
                "elapsed_seconds":batch.get("elapsed_seconds"),"content_sha256":batch["content_sha256"],
                "artifact_sha256":batch.get("artifact_sha256"),"events":self.events(identifier),
                "limits":"Server elapsed workflow time including pauses; not active work/cash savings; original texts, names and reference labels omitted"}

    def finish(self, identifier, expected_revision=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            batch = self._read(db, "wf_batches", identifier)
            if batch["state"] == "completed":
                return
            if expected_revision is not None and expected_revision != batch["revision"]:
                raise ValueError("Lote atualizado. Confira as decisões registradas antes de concluir.")
            if batch["state"] != "active" or not batch["items"]:
                raise ValueError("É necessário um lote ativo com tickets.")
            choices = {}
            for payload, in db.execute("SELECT payload FROM wf_events WHERE batch_id=? AND kind='decisions' ORDER BY seq", (identifier,)):
                choices.update(json.loads(payload)["choices"])
            if set(choices) != {r["ticket_id"] for r in batch["items"]}:
                raise ValueError("Todos os tickets precisam de confirmação explícita antes de concluir.")
            output = []
            for item in batch["items"]:
                prediction = item["prediction"]
                if batch["mode"] == "assisted" and prediction is None:
                    raise ValueError("Falta tentativa de sugestão; nenhuma falha pode ser omitida.")
                output.append({"batch_id": identifier, "ticket_id": item["ticket_id"], "mode": batch["mode"],
                               "run_id": prediction.get("run_id") if prediction else None,
                               "suggested_category": prediction.get("predicted_category") if prediction else None,
                               "final_category": choices[item["ticket_id"]], "model_version": prediction.get("model_version") if prediction else None,
                               "review_state":"confirmed", "actor_type":batch["actor_type"]})
            artifact = decisions_csv(output)
            finished = self.clock()
            elapsed = (datetime.fromisoformat(finished)-datetime.fromisoformat(batch["started_at"])).total_seconds()
            if elapsed < 0:
                raise ValueError("Relógio do servidor recuou. Preserve o lote e investigue; tempo inválido.")
            batch.update(state="completed", finished_at=finished, elapsed_seconds=elapsed,
                         artifact=artifact, artifact_sha256=digest(artifact), revision=batch["revision"]+1)
            self._put(db, "wf_batches", batch)
            self._event(db, identifier, "completed", {"elapsed_seconds": elapsed, "artifact_sha256": digest(artifact)})

    def abort(self, identifier, reason):
        if not reason.strip():
            raise ValueError("Informe o motivo do encerramento sem conclusão.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            batch = self._read(db, "wf_batches", identifier)
            if batch["state"] != "active":
                raise ValueError("O lote já foi encerrado.")
            batch.update(state="aborted", finished_at=self.clock(), abort_reason=reason.strip(), revision=batch["revision"]+1)
            self._put(db, "wf_batches", batch)
            self._event(db, identifier, "aborted", {"reason": reason.strip()})

    def create_study(self, operator, actor_type, request_id, root=ROOT, sample=None):
        identifier = "study-"+digest(request_id)[:32]
        self._new("manual", operator, actor_type, identifier)
        with self.connect() as db:
            found = db.execute("SELECT payload FROM wf_studies WHERE id=?", (identifier,)).fetchone()
            if found:
                study = json.loads(found[0])
                if (study["operator"], study["actor_type"]) != (operator.strip(), actor_type):
                    raise ValueError("Estudo já iniciado por outro participante declarado.")
                return identifier
        protocol_path = root / "data/workflow-protocol.json"
        protocol = json.loads(protocol_path.read_text())
        sample = sample or pilot_sample(identifier, root)
        arms = {mode: validate_rows(sample["arms"][mode]) for mode in ("manual", "assisted")}
        arms = {mode: sorted(rows, key=lambda r: digest(identifier+mode+r["ticket_id"])) for mode,rows in arms.items()}
        all_rows = [r for rows in arms.values() for r in rows]
        if any(len(v)!=protocol["cases_per_arm"] for v in arms.values()) or len({r["ticket_id"] for r in all_rows}) != len(all_rows):
            raise ValueError("O plano precisa de amostras distintas e do tamanho previsto.")
        if any({r["reference_category"] for r in rows} != set(CLASSES) for rows in arms.values()):
            raise ValueError("Cada etapa precisa de uma tarefa de cada classe fornecida.")
        if any(r["source"].get("partition") != "train" or r["reference_category"] not in CLASSES for r in all_rows):
            raise ValueError("O ensaio interno usa apenas treino com referência fornecida.")
        if len({r["source"].get("group_id") for r in all_rows}) != len(all_rows):
            raise ValueError("Grupos de similaridade devem ser distintos entre todas as tarefas.")
        order = ["manual", "assisted"] if int(digest(identifier)[0],16)%2 else ["assisted", "manual"]
        study = {"id":identifier, "operator":operator.strip(), "actor_type":actor_type, "created_at":self.clock(),
                 "protocol":protocol, "protocol_sha256":sha256(protocol_path), "order":order, "arms":arms,
                 "case_manifest":{mode:[{"case_id":r["ticket_id"], "group_id":r["source"]["group_id"], "partition":"train", "text_chars":len(r["text"])} for r in rows] for mode,rows in arms.items()},
                 "batch_ids":{}, "sampling":{k:v for k,v in sample.items() if k!="arms"}, "seed":identifier}
        with self.connect() as db:
            db.execute("INSERT INTO wf_studies VALUES (?,?)", (identifier,encode(study)))
        return identifier

    def studies(self):
        with self.connect() as db:
            return [{k:v for k,v in json.loads(r[0]).items() if k not in {"arms","operator"}}
                    for r in db.execute("SELECT payload FROM wf_studies ORDER BY rowid DESC")]

    def start_arm(self, study_id):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            study = self._read(db,"wf_studies",study_id)
            for mode in study["order"]:
                if mode in study["batch_ids"]:
                    batch = self._read(db,"wf_batches",study["batch_ids"][mode])
                    if batch["state"] == "aborted":
                        raise ValueError("Ensaio interrompido; a tentativa é preservada.")
                    if batch["state"] != "completed":
                        return batch["id"]
                    continue
                identifier = study_id+":"+mode
                batch = self._new(mode, study["operator"],study["actor_type"],identifier,"study",study_id)
                batch["items"]=[{**r,"prediction":None} for r in study["arms"][mode]]
                batch["content_sha256"]=digest(encode(study["arms"][mode]))
                batch["revision"]=1
                db.execute("INSERT INTO wf_batches VALUES (?,?)",(identifier,encode(batch)))
                self._event(db,identifier,"started",{"mode":mode,"actor_type":study["actor_type"],"prepared_input":True})
                study["batch_ids"][mode]=identifier
                self._put(db,"wf_studies",study)
                return identifier
        raise ValueError("As duas etapas já foram concluídas.")

    def study_result(self, study_id):
        study = next(s for s in self.studies() if s["id"]==study_id)
        batches = {m:self.batch(bid) for m,bid in study["batch_ids"].items()}
        states = {m:b["state"] for m,b in batches.items()}
        base = {"study_id":study_id,"actor_type":study["actor_type"],"protocol":study["protocol"],
                "protocol_sha256":study["protocol_sha256"],"seed":study["seed"],"order":study["order"],"states":states,
                "sampling":study["sampling"],"case_manifest":study["case_manifest"],"completed":len(batches)==2 and all(s=="completed" for s in states.values())}
        if not base["completed"]:
            return base
        summary = {}
        for mode,batch in batches.items():
            choices=self.decisions(batch["id"])
            predicted=[r["prediction"] for r in batch["items"] if r["prediction"] is not None]
            correct=sum(choices[r["ticket_id"]]==r["reference_category"] for r in batch["items"])
            summary[mode]={"batch_id":batch["id"],"cases":len(batch["items"]),"elapsed_seconds":batch["elapsed_seconds"],
                           "seconds_per_case":batch["elapsed_seconds"]/len(batch["items"]),"reference_matches":correct,
                           "reference_concordance":correct/len(batch["items"]),
                           "suggestion_corrections":sum(p.get("predicted_category") is not None and choices[r["ticket_id"]]!=p["predicted_category"] for r in batch["items"] for p in [r["prediction"]] if p),
                           "failed_suggestions":sum(not p["persisted"] or p["outcome"]=="failed" for p in predicted),
                           "decision_events":sum(e["kind"]=="decisions" for e in self.events(batch["id"])),
                           "artifact_sha256":batch["artifact_sha256"]}
        delta=summary["manual"]["elapsed_seconds"]-summary["assisted"]["elapsed_seconds"]
        return {**base,"arms":summary,"manual_minus_assisted_seconds":delta,
                "relative_time_reduction":delta/summary["manual"]["elapsed_seconds"] if summary["manual"]["elapsed_seconds"] else None,
                "quality_not_lower_in_sample":summary["assisted"]["reference_concordance"]>=summary["manual"]["reference_concordance"],
                "meaning":"Observed local rehearsal only; includes pauses and small-sample/order/learning limits; not production savings or a new classifier benchmark"}
