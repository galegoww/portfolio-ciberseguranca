# Notas da versão pública

O caminho de uso é pelo EXE e pela extensão, sem instalar Python. Esta é a versão Ultra enviada pelo autor, com sua extensão 1.7. Não inclui o servidor alternativo do repositório anterior.

## Conferência antes da publicação

- O arquivo PE do Windows e o contêiner PyInstaller foram lidos estaticamente, sem executar o EXE ou desserializar o modelo.
- Foi removido o histórico inicial do banco embutido e foram limpos os diagnósticos de atualização das fontes. O SQLite foi reconstruído com VACUUM para retirar páginas antigas.
- O bootloader e todos os demais itens do contêiner foram comparados byte a byte: código, bibliotecas e modelo foram preservados. O EXE público tem um hash diferente por causa da limpeza do banco.
- O banco público passou em integrity_check e possui zero registros no histórico.
- Os vídeos passaram na leitura completa por FFmpeg. As imagens e os arquivos da extensão estão presentes no pacote.

## Limites

A cópia pública do EXE não foi executada em Windows neste ambiente. As capturas são do funcionamento mostrado pelo autor antes da limpeza do banco. Isso não valida automaticamente a versão pública ou a eficácia do bloqueio.

A extensão original aplica no máximo 5.000 regras e usa urlFilter. O total mostrado pelo banco não equivale a regras confirmadas no navegador. Os rótulos e scores do modelo experimental não comprovam presença de malware. O programa não configura o DNS do adaptador; o uso da extensão não altera a rede inteira.

O fonte de referência em fontes/ acompanha o projeto para consulta. Os recursos de banco e modelo estão empacotados no EXE; essa pasta não é um ambiente de montagem completo. A interface pode depender de recursos externos para gráficos.

## Empacotamento do download

O envio de um único ZIP grande pela API foi recusado pelo GitHub. A distribuição usa o ZIP automático da branch `dns-ai-shield-ultra`: ele inclui o programa, a extensão e os materiais de apresentação.

O pequeno `DNS_AI_Shield_Ultra.exe` da raiz é um iniciador Windows x64 compilado em C com Zig. Ele reúne as seis partes locais em `dados_programa`, verifica o SHA-256 do conteúdo completo e abre a versão Ultra. Não baixa arquivos da internet, não pede privilégios administrativos e não altera o DNS do sistema. O executável reunido fica em `%LOCALAPPDATA%\DNS AI Shield Ultra\bin`.

Para o usuário, o fluxo continua sendo extrair o ZIP inteiro e dar dois cliques no EXE. A pasta `dados_programa` precisa acompanhar o iniciador. O fonte do iniciador está em `fontes/launcher_publico.c`; ele foi compilado para Windows, mas não executado em Windows neste ambiente. A reconstituição das partes e o hash esperado foram conferidos localmente.
