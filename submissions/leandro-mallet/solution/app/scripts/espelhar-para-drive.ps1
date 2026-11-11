# Espelha o código da cópia de trabalho (fora do Google Drive) para a pasta do repositório.
#
# Por quê: o volume do Google Drive é FAT32 virtual e não aceita junção nem link simbólico, então
# node_modules e .next não podem ficar "apontados" para fora. O app é editado, instalado e rodado
# numa cópia local, e só o código é copiado para o repositório.
#
# Mão única: cópia de trabalho -> repositório. Ninguém edita o espelho à mão.
# Sem /PURGE: nada é apagado no destino. Com /XO: arquivo mais novo no destino não é sobrescrito.
# Arquivo removido na cópia de trabalho precisa ser tirado
# do repositório pelo git, por quem faz os commits.
#
# Uso:
#   powershell -File scripts\espelhar-para-drive.ps1 -Destino "<caminho de solution\app no repositório>"
param(
  [Parameter(Mandatory = $true)][string]$Destino,
  [string]$Origem
)

if (-not $Origem) { $Origem = Split-Path -Parent $PSScriptRoot }

if (-not (Test-Path -LiteralPath $Destino)) { Write-Error "Destino não existe: $Destino"; exit 2 }

robocopy $Origem $Destino /E /XD node_modules .next .git coverage playwright-report test-results `
  /XF .env .env.local .env.*.local *.tsbuildinfo next-env.d.ts /XO /NFL /NDL /NJH /NP /R:2 /W:2

# robocopy: 0 a 7 = sucesso (com ou sem arquivos copiados); 8 ou mais = erro
if ($LASTEXITCODE -ge 8) { Write-Error "robocopy falhou com código $LASTEXITCODE"; exit 1 }
Write-Output "Espelho atualizado em $Destino"
exit 0
