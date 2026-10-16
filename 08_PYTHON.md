# Python — importação e análise de arquivo de texto

**Exercício com dados sintéticos.** O programa lê um arquivo UTF-8 linha por linha, valida campos, conta resultados e sinaliza pares usuário/IP com pelo menos três falhas na amostra.

```bash
python3 analisar.py
python3 analisar.py eventos.txt --limiar 2
```

## Formato

`data_com_fuso|usuario|ip|FALHA_ou_SUCESSO`

O programa valida data com fuso, endereço IP, usuário não vazio e resultado conhecido. Linhas inválidas são informadas pelo número e não entram nas contagens. Arquivo ausente, codificação inválida ou limiar menor que 1 produzem erro e saída de falha.

## Resultado padrão

- 4 falhas e 2 sucessos válidos.
- Linha 7 inválida.
- Alerta: usuário `bruno`, IP `198.51.100.23`, 3 falhas.

## Interpretação

O alerta orienta triagem; não confirma ataque. Correlacione com horários, dispositivo, sucessos subsequentes e validação do usuário. Os IPs do exercício são de documentação.

## Limitações

O contador cobre o arquivo inteiro e não usa janela de tempo. Não distingue falhas consecutivas, não geolocaliza IPs e não analisa privilégio ou dispositivo. Não é um SIEM e não bloqueia usuários. Para evoluir: definir janelas, reduzir falsos positivos com contexto e testar com outras amostras autorizadas.
