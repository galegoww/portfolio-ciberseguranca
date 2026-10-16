# SQL — filtros para investigar autenticações

**Base sintética com oito eventos.** Use `python3 executar.py`. O script lê os arquivos SQL, cria um banco SQLite em memória e imprime resultados sem dependências externas.

## Perguntas e resultados esperados

| Consulta | Pergunta | IDs ou agregação |
| --- | --- | --- |
| Q1 | Quais falhas ocorreram em 1º de outubro? | 2, 3, 4 |
| Q2 | Quais eventos ocorreram fora de 08h–18h? | 2, 3, 4, 5, 8 |
| Q3 | Quem acumulou pelo menos três falhas na amostra? | bruno: 3 |
| Q4 | Quais sucessos pertencem ao Financeiro? | 1, 7 |

## Análise

Bruno apresenta três falhas seguidas de um sucesso no mesmo IP. Isso merece triagem, mas não prova invasão: pode decorrer de erros de senha. O próximo passo seria confirmar com o usuário, verificar dispositivo, MFA e histórico. O sucesso de Davi às 22h15 também exige contexto de trabalho.

O filtro usa limite superior exclusivo para evitar perder eventos com frações de segundo ao final do dia. `AND` combina condições; `OR` cobre os dois lados do expediente; `GROUP BY` agrega por usuário e `HAVING` filtra grupos.

## Limitações

A amostra não informa fuso horário ou dispositivo. As datas são tratadas como horários do laboratório. A consulta Q3 conta falhas no conjunto inteiro, sem janela móvel, e não deve ser tratada como detector de força bruta em produção. Este exemplo não executa consultas contra uma empresa real.
