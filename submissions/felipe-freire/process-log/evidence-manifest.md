# Manifesto de evidências

**Gerado em:** 16 de julho de 2026
**Algoritmo de integridade:** SHA-256

## Vídeos

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `evidence/videos/Iniciando_os_trabalhos.mp4` | 7.502.043 bytes | `BB96BA88D8B4C2FE7ADFE5041F7D4535F63EBB611536798F6C888A53956E4520` |
| `evidence/videos/Video_Workspace.mp4` | 6.709.000 bytes | `C0ED2F63F029CAF0FCDD20575D86E507F82927F8A4E48E55C72C5664C30F3A37` |
| `evidence/videos/Video_Workspace2.mp4` | 1.769.507 bytes | `4A6533FDF057C970473C40D4550A173960DF1CF4214AC58E3A274CDA5AB151A0` |
| `evidence/videos/Video_Workspace3.mp4` | 4.634.852 bytes | `0D7C18FB6CF789C61D4933BF152C56CA894046E889CC0CD30AD75795F9D2543C` |
| `evidence/videos/Analisando os dados.mp4` | 2.656.915 bytes | `6BAFC7104330A3F26EFA6E02ED94421CBF5653857F804D5997F612DDDCD33CD5` |
| `evidence/videos/Error_do_Claude.mp4` | 10.564.453 bytes | `E18881A1E14BCA9C8FF4CC656B91B33A8D89E4618FAB49E3C898AD5A486533F3` |
| `evidence/videos/Validando o que a IA quer fazer.mp4` | 1.836.526 bytes | `70151488986BC3F0B1E0BD96235D08C166E026AE50BFAD764A4513F56E41C827` |

## Imagens

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `evidence/images/Colocando as duas IAs para trabalhar em conjunto.png` | 295.791 bytes | `E9CDC5056732C9B5AE8EC5C716A0E67C4DDC852CFDC905BEE560CD5B33CF38D2` |
| `evidence/images/Diagrama_funcional_Projeto.png` | 245.291 bytes | `2B3733DCCADAACA854557E05931717D1B1108493FA7E4C2010EDA009C3FF123F` |
| `evidence/images/vibecodando.png` | 223.901 bytes | `B797BECEC5F45BFA642D194FD1CBA5AAB29971BD710FEC00B651B180C5973531` |

## Conversas externas

Os links originalmente armazenados em `linksdechats.txt` foram preservados em `evidence/links/linksdechats.txt`:

- ChatGPT: `https://chatgpt.com/share/6a590f17-cc70-83e9-a5eb-dc2188739a3b`
- Gemini: `https://share.gemini.google/WiX6OzRCWFaq`

## Histórico desta sessão

O registro cronológico está em `chat-export.md`. Ele documenta pedidos, decisões, arquivos produzidos, validações e limitações do processo de exportação.

## Verificação

No PowerShell, execute a partir de `submissions/felipe-freire/process-log`:

```powershell
Get-ChildItem evidence\videos\*.mp4,evidence\images\*.png | Get-FileHash -Algorithm SHA256
```

Os hashes retornados devem coincidir com a tabela acima.
