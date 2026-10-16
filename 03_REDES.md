# Análise de estrutura e segurança de rede

**Projeto defensivo simulado para a Loja Horizonte.** Nenhuma alteração de rede foi aplicada.

## Diagnóstico proposto

Uma rede única para caixa, administração e visitantes permite que dispositivos com níveis de confiança diferentes compartilhem alcance desnecessário. A proposta separa funções e libera somente fluxos indispensáveis.

| Zona | Sub-rede de laboratório | Função |
| --- | --- | --- |
| Administração | 10.10.10.0/24 | Estações internas |
| Vendas | 10.10.20.0/24 | Terminais de venda |
| Visitantes | 10.10.30.0/24 | Acesso à internet |
| Servidores | 10.10.40.0/24 | Aplicação e serviços internos |

São endereços privados de exemplo; não representam uma rede existente.

## Política de comunicação

Aplicar negação por padrão entre zonas. Permitir retorno de conexões estabelecidas no firewall com estado. VLANs dependem de regras entre redes para oferecer isolamento efetivo.

| Origem | Destino | Serviço | Decisão e motivo |
| --- | --- | --- | --- |
| Visitantes | Redes internas | Qualquer | Bloquear |
| Visitantes | Internet | HTTPS | Permitir navegação conforme política |
| Vendas | Aplicação 10.10.40.10 | TCP 443 | Permitir operação do caixa |
| Vendas | Administração | Qualquer | Bloquear |
| Estação administrativa autorizada | Servidor gerenciado | TCP 22 | Permitir gestão com chave e registro |
| Dispositivos internos | Resolvedor autorizado | UDP/TCP 53 | Permitir DNS |
| Dispositivos internos | Servidor de horário autorizado | UDP 123 | Permitir sincronização |

DHCP e outros serviços necessários devem ser mapeados antes de implantar a política. As regras são requisitos de desenho, não configuração completa para um fabricante.

## Testes de aceite a executar em laboratório

1. Visitante acessa um site permitido, mas não a aplicação interna.
2. Caixa acessa a aplicação em HTTPS, mas não uma estação administrativa.
3. Apenas a estação de gestão alcança SSH no servidor.
4. DNS e horário funcionam; logs registram tentativas bloqueadas relevantes.
5. Mudanças têm cópia da configuração anterior e um procedimento de reversão.

## Conclusão

A segmentação reduz o alcance de um dispositivo comprometido. Não impede todos os ataques: identidade, atualizações, proteção dos endpoints e monitoramento continuam necessários. Os testes acima ainda não foram executados em uma rede real.
