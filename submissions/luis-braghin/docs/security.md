# Segurança

## Auditoria do Repositório do Challenge

Antes de fornecer o repositório `ai-master-challenge` como contexto para as IAs, realizei auditoria completa dos 16 arquivos. Resultado: 0 ameaças.

**Categorias verificadas:** prompt injection (comentários HTML, base64, unicode, frases de manipulação), código malicioso (URLs externas, eval/exec, ofuscação), data poisoning nos CSVs (formula injection, instruções ocultas), GitHub Actions/workflows.

**Erros de qualidade encontrados e corrigidos:** "Philipines" → "Philippines", "technolgy" → "technology", "GTXPro" → "GTX Pro".

---

## Agentes de IA — Decisão Consciente

O projeto previa agentes contextuais por deal: pesquisa de empresa (enriquecimento por CNPJ/nome), análise de fit empresa × produto, geração de mensagens de prospecção personalizadas, e verificação de compliance (sanções, PEP).

**Por que não implementei:** dataset contém empresas fictícias (Bluth Company, Bubba Gump, Acme Corporation). API geraria resultados inventados. A lógica rule-based implementada demonstra o conceito sem dependência externa.

**Nota:** Implementei sistema similar no Travelex Bank — dossiê automatizado por CNPJ cruzando 6+ fontes via API (Receita Federal, Serasa, compliance). A decisão foi por inadequação do dataset, não por falta de capacidade técnica.
