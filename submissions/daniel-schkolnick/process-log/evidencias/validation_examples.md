# Exemplos reais de validação da seed

## 1) Exemplo de Score A
- `opportunity_id`: **Z063OYW0**
- Conta: **Isdom**
- Produto: **GTXPro**
- Setor: **medical**
- Employees: **4540**
- Bucket: **1001-5000**
- Score numérico: **56,30**
- Faixa: **A**

Componentes do score:
- Nota win rate do setor: **31,07**
- Nota tempo do setor: **94,12**
- Nota win rate do porte: **0,00**
- Nota tempo do porte: **100,00**

Leitura:
Esse lead entra em **A** porque, na base histórica, o setor **medical** e o bucket **1001-5000** geram uma combinação estrutural acima do corte dos quartis.

---

## 2) Exemplo de Score D
- `opportunity_id`: **ENB2XD8G**
- Conta: **Sonron**
- Produto: **GTX Plus Pro**
- Setor: **telecommunications**
- Employees: **5108**
- Bucket: **5001+**
- Score numérico: **24,19**
- Faixa: **D**

Componentes do score:
- Nota win rate do setor: **36,09**
- Nota tempo do setor: **20,47**
- Nota win rate do porte: **30,37**
- Nota tempo do porte: **9,85**

Leitura:
Esse lead cai em **D** porque a combinação de setor **telecommunications** com bucket **5001+** tem eficiência estrutural historicamente mais fraca na base.

---

## 3) Exemplo de dado incompleto
- `opportunity_id`: **HAXMC4IX**
- Produto: **MG Advanced**
- Etapa: **Engaging**
- Sector: **None**
- Employees: **None**
- Campos faltantes: **setor, porte**
- Score numérico: **não calculado**
- Faixa: **não classificado**

Leitura:
Esse lead permanece no Kanban, mas fica como **Dados incompletos** e fora dos quartis A/B/C/D, exatamente para evidenciar o gargalo de qualidade cadastral.
