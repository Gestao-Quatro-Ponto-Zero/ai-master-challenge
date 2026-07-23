# Manual de Setup: Como Instalar o Python e Rodar o Dashboard

Este guia é voltado para usuários que não têm o Python instalado no computador e desejam rodar o Dashboard RavenStack localmente.

## 1. Instalando o Python

### No Windows
1. Acesse o site oficial do Python: [python.org/downloads](https://www.python.org/downloads/)
2. Clique no botão **Download Python** (a versão mais recente, preferencialmente 3.10 ou superior).
3. **MUITO IMPORTANTE:** Ao abrir o instalador, marque a caixa que diz **"Add Python to PATH"** (ou "Add Python.exe to PATH") na parte inferior da janela ANTES de clicar em "Install Now".
4. Clique em **Install Now** e aguarde a conclusão.
5. Para verificar se deu certo, abra o **Prompt de Comando (cmd)** e digite `python --version`. Ele deve mostrar a versão instalada.

### No Mac (macOS)
1. O Mac geralmente já vem com uma versão do Python, mas recomenda-se usar o Homebrew.
2. Abra o **Terminal**.
3. Se você não tem o Homebrew, instale-o com o comando:
   `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
4. Após o Homebrew instalado, digite: `brew install python`
5. Verifique a instalação digitando `python3 --version`.

### No Linux (Ubuntu/Debian)
1. Abra o Terminal e digite:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```
2. Verifique a instalação com `python3 --version`.

---

## 2. Preparando a Ferramenta de Código (Opcional, mas recomendado)
Recomendamos o uso do **VS Code** (Visual Studio Code) para abrir as pastas do projeto.
1. Baixe em: [code.visualstudio.com](https://code.visualstudio.com/)
2. Instale normalmente.
3. Abra o VS Code e abra a pasta onde estão os arquivos da sua submissão.

---

## 3. Rodando o Projeto (Resumo)
Com o Python instalado, você pode seguir as instruções originais. Aqui vai um lembrete rápido (abra o Terminal ou Prompt de Comando na pasta do projeto):

1. **Criar o ambiente virtual:**
   - Windows: `python -m venv venv`
   - Mac/Linux: `python3 -m venv venv`
2. **Ativar o ambiente virtual:**
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
3. **Instalar as dependências:**
   - `pip install streamlit pandas plotly langchain-experimental langchain-openai`
4. **Executar o Dashboard:**
   - `streamlit run app.py`

*(O navegador abrirá automaticamente no endereço http://localhost:8501)*
