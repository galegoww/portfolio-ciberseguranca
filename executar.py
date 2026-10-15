"""Executa consultas em SQLite em memoria, sem arquivos de banco persistentes."""
from pathlib import Path
import sqlite3

def executar():
    base = Path(__file__).resolve().parent
    with sqlite3.connect(':memory:') as db:
        db.executescript((base / 'dados.sql').read_text(encoding='utf-8'))
        consultas = (base / 'consultas.sql').read_text(encoding='utf-8').split(';')
        for numero, consulta in enumerate(consultas, 1):
            if consulta.strip():
                print(f'Q{numero}: {db.execute(consulta).fetchall()}')

if __name__ == '__main__':
    executar()
