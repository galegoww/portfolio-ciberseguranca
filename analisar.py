"""Triagem local de logs sinteticos; nao conecta a redes ou contas."""
from collections import Counter
from datetime import datetime
from ipaddress import ip_address
from pathlib import Path
import argparse
import json

def analisar(caminho, limiar=3):
    if limiar < 1:
        raise ValueError('O limiar deve ser pelo menos 1.')
    falhas = Counter()
    sucessos = 0
    invalidas = []
    with Path(caminho).open(encoding='utf-8') as arquivo:
        for numero, linha in enumerate(arquivo, 1):
            campos = linha.strip().split('|')
            if len(campos) != 4:
                invalidas.append(numero)
                continue
            instante, usuario, ip, resultado = campos
            try:
                data = datetime.fromisoformat(instante.replace('Z', '+00:00'))
                ip_address(ip)
                if not usuario.strip() or resultado not in ('FALHA', 'SUCESSO') or data.tzinfo is None:
                    raise ValueError('Registro invalido')
            except ValueError:
                invalidas.append(numero)
                continue
            if resultado == 'FALHA':
                falhas[(usuario, ip)] += 1
            else:
                sucessos += 1
    alertas = [
        {'usuario': usuario, 'ip': ip, 'falhas': total}
        for (usuario, ip), total in sorted(falhas.items()) if total >= limiar
    ]
    return {'falhas': sum(falhas.values()), 'sucessos': sucessos,
            'linhas_invalidas': invalidas, 'limiar': limiar, 'alertas': alertas}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arquivo', nargs='?', type=Path,
                        default=Path(__file__).with_name('eventos.txt'))
    parser.add_argument('--limiar', type=int, default=3)
    args = parser.parse_args()
    try:
        resumo = analisar(args.arquivo, args.limiar)
    except (OSError, UnicodeError, ValueError) as erro:
        parser.exit(1, f'Erro: {erro}\n')
    print(json.dumps(resumo, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
