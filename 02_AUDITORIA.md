# Auditoria de segurança — Loja Horizonte

**Estudo de caso fictício.** Não houve auditoria de empresa real.

## Objetivo e escopo

Avaliar controles básicos de uma pequena loja com 12 colaboradores, sistema de vendas, rede de visitantes, arquivos financeiros e cópia de segurança. Avaliação documental simulada; sem exploração, acesso a produção ou conclusão de conformidade legal.

## Critérios

Acesso individual, menor privilégio, autenticação reforçada em contas sensíveis, isolamento de visitantes, manutenção de sistemas, recuperação e rastreabilidade.

| Controle | Evidência fictícia | Situação | Impacto |
| --- | --- | --- | --- |
| Identidade individual | Duas pessoas usam a conta `caixa` | Inadequado | Dificulta atribuir ações |
| Autenticação | Administrador usa apenas senha | Inadequado | Facilita uso de credencial roubada |
| Visitantes | Wi-Fi usa a mesma rede do caixa | Inadequado | Amplia possibilidade de acesso lateral |
| Atualizações | Não existe inventário de versões | Não verificado | Exposição desconhecida |
| Backup | Cópia diária, sem teste de restauração registrado | Parcial | Recuperação não demonstrada |
| Logs | Retenção local sem revisão definida | Parcial | Investigação e detecção limitadas |

## Plano de tratamento

| Prioridade | Ação | Responsável proposto | Prazo proposto | Evidência de aceite |
| --- | --- | --- | --- | --- |
| Alta | Contas individuais e MFA nas contas sensíveis | Administração de TI | 7 dias | Teste de login e lista de contas revisada |
| Alta | Segregar visitantes | Redes | 7 dias | Teste de bloqueio ao sistema de vendas |
| Alta | Restaurar uma cópia em ambiente isolado | TI | 7 dias | Registro de recuperação e integridade |
| Média | Inventariar ativos e versões | TI | 15 dias | Relação validada e plano de atualização |
| Média | Definir coleta, acesso e revisão de logs | Segurança/TI | 30 dias | Evento de teste localizado pelo analista |

## Conclusão

Na hipótese apresentada, o maior ganho inicial vem de reduzir acesso indevido e comprovar recuperação. A existência de uma cópia não prova que os dados podem ser restaurados. O inventário deve preceder afirmações sobre correções pendentes.

## Limitações e aprendizagem

Os controles foram avaliados com evidências inventadas. Uma auditoria real exigiria autorização, entrevistas, amostras, inspeção técnica e validação das correções. Lição do exercício: distinguir controle ausente, controle parcial e evidência insuficiente.
