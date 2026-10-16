# Linux — menor privilégio em arquivos

**Laboratório com dados fictícios.** O script cria uma pasta temporária exclusiva, verifica as permissões e remove apenas essa pasta ao encerrar. Não precisa de `sudo`.

## Problema e procedimento

Um relatório financeiro com modo `644` concede leitura ao grupo e aos demais usuários, desde que o caminho permita acesso. O exercício usa uma pasta inicialmente `755` e altera pasta/arquivo para `700`/`600`.

```bash
bash laboratorio.sh
```

| Comando | Finalidade |
| --- | --- |
| `umask 077` | Restringir permissões iniciais dos objetos criados |
| `mktemp -d` | Criar diretório isolado sem sobrescrever arquivos existentes |
| `stat -c '%a'` | Ler modo octal no Linux |
| `chmod 700` | Dar leitura, escrita e travessia da pasta somente ao proprietário |
| `chmod 600` | Dar leitura e escrita do arquivo somente ao proprietário |

## Resultado esperado

```text
Antes: pasta=755 arquivo=644
Depois: pasta=700 arquivo=600
OK: somente o proprietario possui permissoes POSIX na pasta e no arquivo.
```

## Interpretação e limites

Leitura vale 4, escrita 2 e execução/travessia 1. Para diretórios, execução permite atravessar o caminho; para arquivos, execução permite executar. O script verifica os modos POSIX, não um login com outro usuário. ACLs adicionais, privilégios administrativos e outras camadas de acesso não são avaliados. A mudança é adequada ao cenário de proprietário único; equipes precisam de uma política de grupo explícita.

Depois de executar, salve sua saída em `evidencias/` e explique por que `chmod 777` seria inadequado para este relatório.
