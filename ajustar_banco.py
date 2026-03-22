import sqlite3

DB_NAME = "banco.db"


def coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [item[1] for item in cursor.fetchall()]
    return coluna in colunas


conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# vistorias
if not coluna_existe(cursor, "vistorias", "foto_path"):
    cursor.execute("ALTER TABLE vistorias ADD COLUMN foto_path TEXT")
    print("Coluna foto_path adicionada em vistorias.")
else:
    print("A coluna foto_path já existe em vistorias.")

# manutencoes
if not coluna_existe(cursor, "manutencoes", "foto_path"):
    cursor.execute("ALTER TABLE manutencoes ADD COLUMN foto_path TEXT")
    print("Coluna foto_path adicionada em manutencoes.")
else:
    print("A coluna foto_path já existe em manutencoes.")

conn.commit()
conn.close()

print("Ajuste concluído com sucesso.")