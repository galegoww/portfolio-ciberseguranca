# Validação técnica da preparação

Verificações executadas no ambiente de preparação do pacote em 15/10/2026. Este registro verifica o funcionamento dos exemplos. As evidências das minhas próprias execuções serão adicionadas à pasta `evidencias/`. Estudos documentais são simulados e não foram aplicados a uma organização.

- Linux: script executado, modos 755/644 alterados para 700/600 e verificados.
- SQL: quatro consultas executadas e resultados comparados com os esperados.
- Python: contagens, alerta e linha inválida conferidos; arquivo ausente e limiar zero retornam erro.
- Documentação: destinos de todos os links locais conferidos.

## Saída Linux

```text
Antes: pasta=755 arquivo=644
Depois: pasta=700 arquivo=600
OK: somente o proprietario possui permissoes POSIX na pasta e no arquivo.
```

## Saída SQL

```text
Q1: [(2, 'bruno', '198.51.100.23'), (3, 'bruno', '198.51.100.23'), (4, 'bruno', '198.51.100.23')]
Q2: [(2, 'bruno'), (3, 'bruno'), (4, 'bruno'), (5, 'bruno'), (8, 'davi')]
Q3: [('bruno', 3)]
Q4: [(1, 'ana'), (7, 'ana')]
```

## Saída Python

```json
{
  "falhas": 4,
  "sucessos": 2,
  "linhas_invalidas": [
    7
  ],
  "limiar": 3,
  "alertas": [
    {
      "usuario": "bruno",
      "ip": "198.51.100.23",
      "falhas": 3
    }
  ]
}
```
