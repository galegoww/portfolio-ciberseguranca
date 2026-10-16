# Verificação dos exemplos

Os exemplos foram verificados em uma pasta com a mesma organização plana utilizada neste repositório. Este registro é uma referência de funcionamento dos exemplos; as evidências das minhas execuções pessoais serão acrescentadas separadamente.

## Comandos a partir da raiz

```bash
bash laboratorio.sh
python3 executar.py
python3 analisar.py
```

No Windows, use `py -3` em lugar de `python3`, se necessário. O laboratório Bash requer Linux.

## Resultado de referência — Linux

```text
Antes: pasta=755 arquivo=644
Depois: pasta=700 arquivo=600
OK: somente o proprietario possui permissoes POSIX na pasta e no arquivo.
```

## Resultado de referência — SQL

```text
Q1: [(2, 'bruno', '198.51.100.23'), (3, 'bruno', '198.51.100.23'), (4, 'bruno', '198.51.100.23')]
Q2: [(2, 'bruno'), (3, 'bruno'), (4, 'bruno'), (5, 'bruno'), (8, 'davi')]
Q3: [('bruno', 3)]
Q4: [(1, 'ana'), (7, 'ana')]
```

## Resultado de referência — Python

```text
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

Os casos de auditoria, redes, vulnerabilidades e incidentes são simulações documentais, sem avaliação de organização real.
