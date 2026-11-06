# Análises — como reproduzir

Requisitos: Python 3.10+ com `pandas`, `numpy`, `scipy`, `scikit-learn` (`pip install pandas numpy scipy scikit-learn`).
Dados: baixe do Kaggle e passe o caminho do CSV como argumento (os dados não vão para o repositório).

| Script | O que faz | Entrada |
|---|---|---|
| `01_inspecao_dados.py` | Qualidade dos dados: volume, placeholders, horários, uniformidade | Dataset 1 + Dataset 2 |
| `02_diagnostico.py` | As 3 perguntas do Diretor com testes estatísticos e permutação | Dataset 1 |
| `03_classificador.py` | Exploração: TF-IDF + regressão logística, 40 mil termos (86,5%) | Dataset 2 |
| `04_onde_parar.py` | Desempenho por categoria acima/abaixo do limiar | Dataset 2 |
| `05_exportar_modelo.py` | **Modelo final** (20 mil termos, 86,1%, leve para o navegador) e arquivos do protótipo | Dataset 2 |
| `07_curva_aprendizado.py` | Quantos tickets rotulados a empresa precisa: acerto e volume automatizado com 250 a 38 mil exemplos | Dataset 2 |
| `06_validacao_e_regras.py` | Auditoria: confirma o limiar numa validação separada e exporta os textos de teste para medir as regras | Dataset 2 |

`pt_teste_original_en.json` e `pt_teste_traduzido.json`: 56 tickets do conjunto de teste e suas traduções para português, usados para medir a camada de português (`../prototype/src/pt_eval.js`).

Todos os números dos documentos vêm do modelo final (`05`), exceto quando indicado.
