# Diário de resposta a incidentes

**Incidente simulado INC-LAB-001.** Datas, usuários e evidências são fictícios, associados à amostra SQL. Nenhuma contenção real foi executada.

## Resumo inicial

Em 1º de outubro de 2026, a conta `bruno` apresentou três falhas e depois um sucesso entre 23h10 e 23h13. Classificação inicial: evento suspeito de autenticação. Severidade provisória: média, sujeita ao privilégio da conta e aos recursos acessados. Não há evidência suficiente para confirmar comprometimento.

## Linha do tempo

| Horário do laboratório | Observação ou ação simulada | Evidência ou justificativa |
| --- | --- | --- |
| 23:10–23:12 | Três falhas na conta bruno | IDs 2, 3 e 4 da base SQL |
| 23:13 | Sucesso da mesma conta e IP | ID 5; sucesso não prova legitimidade |
| 23:15 | Analista abre triagem | Preservar cópia dos registros e restringir acesso |
| 23:20 | Solicitação de confirmação por canal confiável | Ação proposta; resposta do usuário indisponível |
| 23:25 | Verificação de dispositivo, MFA e sessões | Dados não incluídos na amostra |
| 23:30 | Decisão condicional de contenção | Se acesso não reconhecido: revogar sessões e bloquear conta conforme autorização |

## Preservação proposta

Exportar logs com identificação de fonte, intervalo, fuso e responsável. Calcular hash da cópia, guardar o original com acesso restrito e trabalhar em uma cópia. Um hash detecta alterações posteriores; não comprova a origem do evento por si só. Nenhum hash de evidência real foi produzido neste exercício.

## Critérios de decisão e recuperação

- Se o usuário reconhecer o acesso, confrontar essa resposta com o dispositivo e os recursos acessados antes de encerrar como atividade legítima.
- Se negar ou houver outras evidências, acionar o responsável, conter conforme procedimento, revisar privilégios, trocar credenciais por canal seguro e investigar o escopo.
- Para recuperar: confirmar dispositivo confiável, aplicar controles necessários e monitorar novas autenticações.

## Encerramento do exercício

**Situação: inconclusivo por falta de dados complementares.** Não atribuir autoria nem afirmar exfiltração com base apenas em falhas de login. Em uma ocorrência real, o encerramento exigiria revisão das evidências, conclusão documentada e aprovação do responsável.

Lição: separar fatos observados, hipóteses e ações propostas evita conclusões precipitadas.
