"""
Base RAG (Retrieval-Augmented Generation) com Gemini Embedding.

Gera embeddings dos datasets e permite busca semântica por similaridade.
Serve como memória de longo prazo para o LLM principal.
"""

import logging
import time
import json
from pathlib import Path

import numpy as np
import pandas as pd
from google import genai

from config import (
    GOOGLE_API_KEY, GEMINI_EMBEDDING_MODEL, GEMINI_EMBEDDING_DIMENSIONS,
    DATASET1_PATH, DATASET2_PATH, CACHE_DIR,
    RAG_BATCH_SIZE, RAG_MAX_CORPUS, RAG_TOP_K, DUPLICATE_THRESHOLD,
)

logger = logging.getLogger(__name__)


def _get_client() -> genai.Client:
    return genai.Client(api_key=GOOGLE_API_KEY)


class RAGStore:
    def __init__(self):
        self._embeddings: np.ndarray | None = None
        self._documents: list[dict] = []
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def size(self) -> int:
        return len(self._documents)

    def inicializar(self):
        if not GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY não configurada — RAG desativado")
            return

        cache_emb = CACHE_DIR / "rag_embeddings.npy"
        cache_docs = CACHE_DIR / "rag_documents.json"
        cache_meta = CACHE_DIR / "rag_metadata.json"

        if cache_emb.exists() and cache_docs.exists() and cache_meta.exists():
            try:
                with open(cache_meta, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                cache_valido = (
                    meta.get("rag_max_corpus") == RAG_MAX_CORPUS
                    and meta.get("embedding_model") == GEMINI_EMBEDDING_MODEL
                    and meta.get("embedding_dimensions") == GEMINI_EMBEDDING_DIMENSIONS
                )
                if cache_valido:
                    logger.info("Carregando RAG do cache...")
                    self._embeddings = np.load(str(cache_emb))
                    with open(cache_docs, "r", encoding="utf-8") as f:
                        self._documents = json.load(f)
                    self._ready = True
                    logger.info("RAG carregado do cache: %d documentos", len(self._documents))
                    return
                logger.info("Cache RAG desatualizado. Recriando índice com configuração atual.")
            except Exception as e:
                logger.warning("Falha ao validar cache RAG (%s). Recriando índice.", e)

        logger.info("Construindo base RAG a partir dos datasets...")
        docs = self._carregar_datasets()
        if not docs:
            logger.warning("Nenhum documento carregado para RAG")
            return

        self._documents = docs
        textos = [d["texto"][:500] for d in docs]
        self._embeddings = self._gerar_embeddings_batch(textos)

        if self._embeddings is not None:
            np.save(str(cache_emb), self._embeddings)
            with open(cache_docs, "w", encoding="utf-8") as f:
                json.dump(self._documents, f, ensure_ascii=False)
            with open(cache_meta, "w", encoding="utf-8") as f:
                json.dump({
                    "rag_max_corpus": RAG_MAX_CORPUS,
                    "embedding_model": GEMINI_EMBEDDING_MODEL,
                    "embedding_dimensions": GEMINI_EMBEDDING_DIMENSIONS,
                    "documents": len(self._documents),
                }, f, ensure_ascii=False)
            self._ready = True
            logger.info("RAG pronto: %d documentos, shape %s",
                        len(self._documents), self._embeddings.shape)

    def _carregar_datasets(self) -> list[dict]:
        docs = []

        if DATASET1_PATH.exists():
            df1 = pd.read_csv(DATASET1_PATH)
            ds1 = df1.dropna(subset=["Ticket Description"]).copy()
            limite_ds1 = min(len(ds1), RAG_MAX_CORPUS // 2)
            for _, row in ds1.head(limite_ds1).iterrows():
                docs.append({
                    "texto": str(row["Ticket Description"]),
                    "resolucao": str(row.get("Resolution", "")) if pd.notna(row.get("Resolution", "")) else "",
                    "categoria": str(row.get("Ticket Type", "")),
                    "origem": "dataset1",
                })

        if DATASET2_PATH.exists():
            df2 = pd.read_csv(DATASET2_PATH)
            restante = max(RAG_MAX_CORPUS - len(docs), 0)
            if restante > 0:
                sample = df2.sample(min(restante, len(df2)), random_state=42)
            else:
                sample = df2.iloc[0:0]
            for _, row in sample.iterrows():
                docs.append({
                    "texto": str(row["Document"]),
                    "resolucao": "",
                    "categoria": str(row["Topic_group"]),
                    "origem": "dataset2",
                })

        logger.info("Documentos carregados: %d (DS1: %d, DS2: %d)",
                     len(docs),
                     sum(1 for d in docs if d["origem"] == "dataset1"),
                     sum(1 for d in docs if d["origem"] == "dataset2"))
        return docs

    def _gerar_embeddings_batch(self, textos: list[str]) -> np.ndarray | None:
        client = _get_client()
        all_embeddings = []
        total = len(textos)
        max_retries = 5

        for i in range(0, total, RAG_BATCH_SIZE):
            batch = textos[i:i + RAG_BATCH_SIZE]
            for attempt in range(max_retries):
                try:
                    result = client.models.embed_content(
                        model=GEMINI_EMBEDDING_MODEL,
                        contents=batch,
                        config={
                            "output_dimensionality": GEMINI_EMBEDDING_DIMENSIONS,
                        },
                    )
                    for emb in result.embeddings:
                        all_embeddings.append(emb.values)
                    batch_num = i // RAG_BATCH_SIZE
                    if batch_num % 20 == 0:
                        logger.info("Embeddings: %d/%d", min(i + RAG_BATCH_SIZE, total), total)
                    time.sleep(0.7)
                    break
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        wait = min(30 * (2 ** attempt), 120)
                        logger.warning("Rate limit (batch %d), aguardando %ds (tentativa %d/%d)",
                                       i, wait, attempt + 1, max_retries)
                        time.sleep(wait)
                    else:
                        logger.error("Erro ao gerar embeddings (batch %d): %s", i, e)
                        return None
            else:
                logger.error("Esgotou tentativas no batch %d", i)
                return None

        return np.array(all_embeddings, dtype=np.float32)

    def _gerar_embedding(self, texto: str) -> np.ndarray | None:
        client = _get_client()
        try:
            result = client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=texto[:500],
                config={
                    "output_dimensionality": GEMINI_EMBEDDING_DIMENSIONS,
                },
            )
            return np.array(result.embeddings[0].values, dtype=np.float32)
        except Exception as e:
            logger.error("Erro ao gerar embedding: %s", e)
            return None

    def buscar_similares(self, texto: str, top_k: int = RAG_TOP_K) -> list[dict]:
        if not self._ready or self._embeddings is None:
            return []

        query_emb = self._gerar_embedding(texto)
        if query_emb is None:
            return []

        norms_docs = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        norms_docs = np.where(norms_docs == 0, 1, norms_docs)
        norm_query = np.linalg.norm(query_emb)
        if norm_query == 0:
            return []

        similarities = (self._embeddings @ query_emb) / (norms_docs.flatten() * norm_query)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            doc = self._documents[idx]
            results.append({
                "texto": doc["texto"],
                "resolucao": doc["resolucao"],
                "categoria": doc["categoria"],
                "similaridade": round(float(similarities[idx]), 4),
                "origem": doc["origem"],
            })
        return results

    def verificar_duplicatas(self, texto: str, tickets_abertos: list[dict],
                              threshold: float = DUPLICATE_THRESHOLD) -> list[dict]:
        if not self._ready or not tickets_abertos:
            return []

        query_emb = self._gerar_embedding(texto)
        if query_emb is None:
            return []

        textos_abertos = [t.get("texto", "")[:500] for t in tickets_abertos]
        embs = self._gerar_embeddings_batch(textos_abertos)
        if embs is None:
            return []

        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        norm_q = np.linalg.norm(query_emb)
        if norm_q == 0:
            return []

        sims = (embs @ query_emb) / (norms.flatten() * norm_q)
        duplicatas = []
        for i, sim in enumerate(sims):
            if sim >= threshold:
                ticket = tickets_abertos[i]
                duplicatas.append({
                    "ticket_id": ticket.get("id", ""),
                    "similaridade": round(float(sim), 4),
                    "texto_preview": textos_abertos[i][:100],
                })

        return sorted(duplicatas, key=lambda x: -x["similaridade"])

    def reindexar(self, novos_docs: list[dict]):
        if not GOOGLE_API_KEY:
            return

        textos = [d["texto"][:500] for d in novos_docs]
        novos_embs = self._gerar_embeddings_batch(textos)
        if novos_embs is None:
            return

        self._documents.extend(novos_docs)
        if self._embeddings is not None:
            self._embeddings = np.vstack([self._embeddings, novos_embs])
        else:
            self._embeddings = novos_embs

        cache_emb = CACHE_DIR / "rag_embeddings.npy"
        cache_docs = CACHE_DIR / "rag_documents.json"
        cache_meta = CACHE_DIR / "rag_metadata.json"
        np.save(str(cache_emb), self._embeddings)
        with open(cache_docs, "w", encoding="utf-8") as f:
            json.dump(self._documents, f, ensure_ascii=False)
        with open(cache_meta, "w", encoding="utf-8") as f:
            json.dump({
                "rag_max_corpus": RAG_MAX_CORPUS,
                "embedding_model": GEMINI_EMBEDDING_MODEL,
                "embedding_dimensions": GEMINI_EMBEDDING_DIMENSIONS,
                "documents": len(self._documents),
            }, f, ensure_ascii=False)

        self._ready = True
        logger.info("RAG re-indexado: +%d docs, total %d", len(novos_docs), len(self._documents))


rag_store = RAGStore()
