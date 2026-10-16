# Avaliação de vulnerabilidades — pequena empresa

**Cenário inventado para exercício.** Os riscos abaixo são hipóteses fornecidas pelo cenário; não são resultados de varredura real ou CVEs confirmadas.

## Método

Inventariar ativos, avaliar ameaça e consequência, pontuar probabilidade e impacto de 1 a 3 e multiplicar os valores. Prioridade local: 1–2 baixa, 3–4 média, 6–9 alta. Esta matriz simplificada não é CVSS.

| Ativo e condição fictícia | Ameaça e efeito | P | I | Risco | Tratamento |
| --- | --- | --- | --- | --- | --- |
| Painel administrativo sem MFA | Credencial roubada permite alteração indevida | 3 | 3 | 9, alta | MFA, contas individuais e revisão de privilégios |
| Backup no mesmo dispositivo do original | Falha ou malware elimina original e cópia | 2 | 3 | 6, alta | Cópia separada e teste de restauração |
| Serviço de compartilhamento acessível a visitantes | Dispositivo não confiável alcança dados internos | 2 | 3 | 6, alta | Segmentação e regras de acesso |
| Sistema sem registro de atualização | Falhas conhecidas podem permanecer sem correção | 2 | 2 | 4, média | Inventário, checagem de versões e atualização testada |
| Contas antigas não revisadas | Ex-colaborador mantém acesso | 2 | 2 | 4, média | Fluxo de desligamento e revisão periódica |

## Plano de validação

1. Confirmar cada hipótese com inventário, configurações e entrevistas autorizadas.
2. Tratar primeiro identidades sensíveis e capacidade de recuperação.
3. Testar bloqueios com contas de laboratório e restauração em destino isolado.
4. Registrar responsável, data, evidência e risco residual de cada correção.

## Exemplo de reavaliação

Se MFA for aplicado e validado, a probabilidade estimada do primeiro risco pode cair de 3 para 1. O impacto continua 3, resultando em 3 (médio). Isso é uma projeção e não uma redução demonstrada. Roubo de sessão e outros caminhos ainda precisam de controles adicionais.

## Aprendizagem

Uma vulnerabilidade descreve uma fraqueza; o risco relaciona essa fraqueza a uma ameaça e a uma consequência. Ausência de inventário não basta para afirmar que uma versão vulnerável está instalada.
