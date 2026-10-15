# Everton Macedo | Portfólio de Segurança Cibernética

**Objetivo de carreira:** desenvolver uma base prática para oportunidades iniciais em segurança cibernética, com foco em análise de eventos, controle de acesso e documentação.

> Portfólio em desenvolvimento. Os estudos de caso usam cenários fictícios e os laboratórios usam dados de exemplo. As evidências das minhas execuções serão adicionadas conforme eu avançar nos estudos.

## Apresentação

Tenho ensino médio completo e atuo há seis anos na SintecSoluções. Minha trajetória está ligada à informática e ao suporte técnico. Agora estou ampliando meus conhecimentos com o curso Fundamentos da Segurança Cibernética, do Google, pela Coursera.

Quero aproximar o que já conheço de tecnologia das práticas de proteção de sistemas e informações. Neste portfólio, organizo meus estudos sobre controle de acesso, redes, análise de eventos e resposta a incidentes.

[Leia minha declaração profissional](01_declaracao_profissional/README.md).

## Projetos e documentos

| Item | Entrega | Natureza |
| --- | --- | --- |
| [01. Declaração profissional](01_declaracao_profissional/README.md) | Apresentação, objetivos e princípios | Apresentação profissional |
| [02. Auditoria de segurança](02_auditoria/README.md) | Escopo, evidências fictícias e plano de ação | Estudo de caso |
| [03. Segurança de redes](03_redes/README.md) | Fluxos, segmentação e regras defensivas | Proposta simulada |
| [04. Permissões no Linux](04_linux/README.md) | Laboratório isolado e resultado verificável | Exercício reproduzível |
| [05. Filtros SQL](05_sql/README.md) | Base SQLite, consultas e interpretação | Exercício reproduzível |
| [06. Vulnerabilidades](06_vulnerabilidades/README.md) | Registro de riscos e prioridades | Estudo de caso |
| [07. Diário de incidentes](07_incidentes/README.md) | Linha do tempo, investigação e encerramento | Simulação |
| [08. Análise com Python](08_python/README.md) | Leitura de logs, tratamento de erros e alertas | Exercício reproduzível |
| [09. Currículo](09_curriculo/CURRICULO.md) | Currículo em atualização | Rascunho com campos pendentes |

## Executar os exercícios

SQL e Python precisam apenas de Python 3 com biblioteca padrão. Abra o terminal dentro desta pasta:

```bash
python3 05_sql/executar.py
python3 08_python/analisar.py
```

No Windows, se necessário, troque `python3` por `py -3`. O laboratório de permissões requer Linux e Bash:

```bash
bash 04_linux/laboratorio.sh
```

As instruções e os resultados esperados estão nas pastas de cada projeto. Não é necessário instalar pacotes Python, usar credenciais, acessar serviços ou examinar máquinas de terceiros.

## Próximos passos

1. Revisar nome, objetivos e declaração profissional.
2. Preencher o currículo e confirmar a situação do curso.
3. Executar os três laboratórios e salvar saídas próprias em `evidencias/`.
4. Reescrever as conclusões com suas palavras e explicar cada comando.
5. Conferir privacidade e manter o repositório privado até finalizar.

[Guia de organização e GitHub](COMECAR_AQUI.md) · [Registro de validação técnica](VALIDACAO.md)
