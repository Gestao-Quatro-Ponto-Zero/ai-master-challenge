# Correção do setup — 02/11/2026

O usuário encontrou dois obstáculos reais: o comando foi executado na pasta pai,
e o setup manual exigiu instalar suporte a venv. A repetição do treino terminou
com FileExistsError e traceback, embora os quatro ajustes já estivessem concluídos.
Pediu uma inicialização pensada para quem apenas quer executar a entrega.

Codex substituiu o caminho principal de setup por `bash run.sh`. O script resolve
sua própria pasta, verifica Linux x86_64, usa lock de preparação, fornece Python
3.12.3 local por uv 0.9.7 quando necessário, sincroniza o lock e prepara/verifica
dados, membership e modelo antes de abrir o Streamlit. Não usa sudo, ensurepip ou
python3-venv do sistema. O uv vem de URL fixa oficial, com SHA-256 conferido antes
de executar; caches/runtime/backup de venv ficam em `.runtime/`, fora do Git.

O treino direto também passou a reconhecer e validar uma tentativa concluída,
retornando sucesso sem ajustar de novo. Tentativas interrompidas, arquivos órfãos,
hashes incompatíveis ou dados alterados recebem diagnóstico, sem exclusão ou
sobrescrita. `--prepare-only` permite conferir o setup sem iniciar um servidor.
O modo padrão abre a interface local. README e setup agora mostram esse comando
primeiro; os passos manuais da V00 ficam como referência técnica.

## Preservação e proveniência

Modificar o preflight mudou o hash do arquivo de treino. Antes da alteração,
foram preservados código/bundle/relatório originais na proveniência local. A
revisão comparou a AST do corpo de cálculo, removendo apenas os novos guards:
permaneceu igual. Pickles, referência e política também mantiveram seus hashes.
A [revalidação explícita](../docs/review-evidence/setup-binding.json) atualiza o
binding de execução e conserva os hashes reais do treino original no relatório.
Nenhum classificador do workspace principal foi reajustado e nenhum resultado
ou limiar foi escolhido de novo. Não se ocultou a mudança com atualização cega
de recibo. O teste final permaneceu sem previsões.

## Verificação executada

- Cópia limpa sem venv/runtime/uv, dados brutos, membership ou modelos: o comando
  baixou tudo, forneceu Python gerenciado e executou os quatro ajustes fixos só
  nessa reprodução isolada. Mesmos macro F1 e configuração selecionada da execução
  original; não foi experimento novo para melhorar resultados.
- Repetição com proxy bloqueado e uv offline: sucesso sem rede, treino adicional
  ou mudança de hashes/mtimes dos modelos/dados.
- Comando padrão, chamado de `/tmp`: preparação seguida de servidor local HTTP 200,
  encerrado depois do check. Smoke de inferência no Python gerenciado passou.
- Sete testes novos de guard/estado/diagnóstico. Os 64 testes passaram, sem skips,
  incluindo AppTest e os fluxos anteriores. Smoke do workspace principal passou.

[Evidência de reprodução](../docs/review-evidence/setup-reproduction.json) e
[testes](../docs/review-evidence/triage-tests.txt) registram o escopo. A primeira
execução ainda exige internet, escrita/espaço em disco e comandos básicos Linux;
Windows/macOS/Alpine não foram validados. Falhas do host não são garantia de sucesso
universal: são tratadas com orientação, preservando dados e tentativas existentes.

## Conversas e handoff

A [captura 17](chat-exports/17-setup-fix-chat.md) preserva oito mensagens novas de
quatro turnos retornados, incluindo conclusão I01, erro de pasta e o relato de
venv/treino repetido. `hasMore=true` aponta para histórico anterior fora da página.
Mensagens posteriores e a resposta final ficam para próxima extração. Somente
mensagens de usuário/assistente foram retidas, sem instruções/ferramentas/raciocínio.
I01 recebeu esta correção; V01 continua sendo o próximo passo. Sem commit/push.
