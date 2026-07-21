# Protótipo — Triagem automática de tickets

Ferramenta que recebe o texto de um ticket, classifica em 1 de 8 categorias e decide
se **auto-roteia** para a fila responsável ou **encaminha para um humano**, conforme a
confiança do modelo. Roda 100% local — modelo supervisionado (TF-IDF + Regressão
Logística), sem custo por chamada e em milissegundos.

---

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`. Não precisa de internet, GPU nem chave de API.

---

## Como usar

- **Ticket único:** cole um texto (ou clique em *"Carregar ticket real do dataset"*) e
  classifique. Você vê a categoria, a confiança, a decisão de roteamento e **os termos
  que mais pesaram** na decisão. Se o ticket veio do dataset, mostro também o rótulo
  real — inclusive quando o modelo erra (honestidade > cherry-pick).
- **Lote (CSV):** use a amostra inclusa (50 tickets reais) ou envie seu CSV. Retorna
  **quanto seria automatizado vs. humano** no limiar atual — a leitura que um Diretor
  de Operações quer — mais a acurácia ao vivo quando o CSV traz o rótulo real.
- **Limiar de confiança (barra lateral):** arraste e veja o trade-off. Mais alto =
  auto-roteamento mais preciso, porém menos cobertura (mais tickets vão para humano).

---

## Lógica (o que está por trás)

1. **Classificação.** TF-IDF (1–2 grams) + Regressão Logística, treinado em ~38k tickets
   reais rotulados. Acurácia honesta de **86,5%** em teste (F1-macro 0,86), sólida nas 8
   classes. Escolha deliberada de um modelo supervisionado em vez de LLM: mais preciso
   *nesta* tarefa, custo zero por chamada, ~1.000× mais rápido e explicável (ver
   `docs/` da submissão para o comparativo).
2. **Gate de confiança.** O modelo devolve uma probabilidade; acima do limiar (padrão
   0,69 ≈ **95% de precisão** nos auto-roteados, 74% de cobertura) o ticket é
   auto-roteado para a fila da categoria; abaixo, vai para um humano. É assim que a
   ferramenta responde *o que NÃO automatizar* — com número, não opinião.
3. **Explicabilidade.** Como o modelo é linear sobre TF-IDF, os termos que empurraram a
   decisão saem de graça dos pesos do modelo — o agente vê *por que* aquele roteamento.

O código separa **núcleo** (`router.py`, sem UI) de **interface** (`app.py`). A mesma
função `classify()` que alimenta a demo é a que iria atrás de um endpoint em produção.

---

## Caminho para produção / Limitações

O **cérebro é grau de produção**; a casca Streamlit é a demo. O que muda no deploy real:

| Componente | Em produção |
|---|---|
| Modelo + gate + roteamento | Viram um serviço (FastAPI) que o helpdesk (Zendesk/ServiceNow/Jira) chama por API/webhook quando um ticket entra |
| UI Streamlit | Deixa de ser um app que se "abre"; vira integração no helpdesk. Streamlit segue útil como console interno de revisão |
| Slider do limiar | Vira valor de *config* que o time de ops fixa |
| Upload de CSV | Vira job agendado ou consumidor de stream |

**Premissas que "viável" carrega (e que assumo abertamente):**

1. **Retreinar nos dados da própria empresa.** Este modelo aprendeu a taxonomia do
   dataset público de teste. Um deploy real treina nos tickets e nas categorias da
   empresa. A *capacidade* é viável; este artefato é prova de conceito.
2. **Treinar em texto cru.** O dataset vem pré-processado (sem stopwords); ticket real é
   linguagem natural — o que na prática dá *mais* sinal, não menos.
3. **Monitoramento + loop de feedback.** Quando o agente corrige um roteamento errado,
   isso vira novo rótulo de treino. TF-IDF é barato de retreinar (minutos) — vantagem
   sobre LLM.
4. **Híbrido para a cauda longa.** O modelo só conhece as 8 categorias que viu.
   Categoria nova / cold start / ticket genuinamente ambíguo → é onde um LLM ou um
   humano entram. A arquitetura certa usa cada ferramenta onde ela brilha.
5. **Confiança ≠ probabilidade calibrada.** O número de "confiança" é o *score* do
   modelo, não uma probabilidade calibrada (ex.: "0,69" não significa literalmente 69%
   de chance de acerto). O limiar foi escolhido **empiricamente** para dar ~95% de
   precisão nos auto-roteados, então o roteamento é confiável; num deploy real vale
   calibrar (Platt/isotônica) para o número exibido ser interpretável.

---

## Estrutura

```
prototype/
├── app.py                 ← UI Streamlit (fina)
├── router.py              ← núcleo: classify() / roteamento (sem UI; iria para FastAPI)
├── model/
│   └── ticket_classifier.joblib   ← modelo treinado
├── sample_tickets.csv     ← 50 tickets reais para a demo
├── requirements.txt
└── README.md
```
