<<<<<<< HEAD
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

=======
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

>>>>>>> 4f4d18623026bf11e99f258282f6ff8da67220f9
print("Ajuste concluído com sucesso.")