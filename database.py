<<<<<<< HEAD
import sqlite3


DB_NAME = "banco.db"


def conectar():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [item[1] for item in cursor.fetchall()]
    return coluna in colunas


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas_veiculo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            data_despesa TEXT,
            categoria TEXT,
            descricao TEXT,
            valor REAL,
            observacoes TEXT,
            comprovante_path TEXT,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT,
            rg TEXT,
            telefone TEXT,
            endereco TEXT,
            cidade TEXT,
            estado TEXT,
            cep TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo TEXT NOT NULL,
            marca TEXT,
            ano TEXT,
            placa TEXT,
            cor TEXT,
            status TEXT DEFAULT 'Disponível',
            observacoes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            veiculo_id INTEGER NOT NULL,
            data_inicio TEXT,
            data_fim TEXT,
            valor_semanal REAL,
            valor_total_contrato REAL DEFAULT 0,
            caucao REAL,
            status TEXT DEFAULT 'Ativo',
            arquivo_contrato TEXT,
            valor_pago REAL DEFAULT 0,
            status_pagamento TEXT DEFAULT 'Pendente',
            data_pagamento TEXT,
            comprovante_pagamento TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        )
    """)

    if not coluna_existe(cursor, "contratos", "valor_total_contrato"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN valor_total_contrato REAL DEFAULT 0
        """)

    if not coluna_existe(cursor, "contratos", "valor_pago"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN valor_pago REAL DEFAULT 0
        """)

    if not coluna_existe(cursor, "contratos", "status_pagamento"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN status_pagamento TEXT DEFAULT 'Pendente'
        """)

    if not coluna_existe(cursor, "contratos", "data_pagamento"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN data_pagamento TEXT
        """)

    if not coluna_existe(cursor, "contratos", "comprovante_pagamento"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN comprovante_pagamento TEXT
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vistorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            contrato_id INTEGER,
            cliente_contrato TEXT,
            vistoriador TEXT,
            data_vistoria TEXT,
            odometro INTEGER,
            observacoes TEXT,
            foto_path TEXT,
            latitude REAL,
            longitude REAL,
            endereco TEXT,
            data_hora_real TEXT,
            hash_vistoria TEXT,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id),
            FOREIGN KEY (contrato_id) REFERENCES contratos(id)
        )
    """)

    if not coluna_existe(cursor, "vistorias", "foto_path"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN foto_path TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "latitude"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN latitude REAL
        """)

    if not coluna_existe(cursor, "vistorias", "longitude"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN longitude REAL
        """)

    if not coluna_existe(cursor, "vistorias", "endereco"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN endereco TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "data_hora_real"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN data_hora_real TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "vistoriador"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN vistoriador TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "cliente_contrato"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN cliente_contrato TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "contrato_id"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN contrato_id INTEGER
        """)

    if not coluna_existe(cursor, "vistorias", "hash_vistoria"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN hash_vistoria TEXT
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manutencoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            data_manutencao TEXT,
            tipo_servico TEXT,
            descricao TEXT,
            valor REAL,
            oficina TEXT,
            km_atual INTEGER,
            proxima_troca_oleo INTEGER,
            observacoes TEXT,
            foto_path TEXT,
            km_prox_revisao INTEGER,
            km_prox_pneu INTEGER,
            km_prox_freio INTEGER,
            km_prox_bateria INTEGER,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        )
    """)

    if not coluna_existe(cursor, "manutencoes", "foto_path"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN foto_path TEXT
        """)

    if not coluna_existe(cursor, "manutencoes", "km_prox_revisao"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN km_prox_revisao INTEGER
        """)

    if not coluna_existe(cursor, "manutencoes", "km_prox_pneu"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN km_prox_pneu INTEGER
        """)

    if not coluna_existe(cursor, "manutencoes", "km_prox_freio"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN km_prox_freio INTEGER
        """)

    if not coluna_existe(cursor, "manutencoes", "km_prox_bateria"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN km_prox_bateria INTEGER
        """)

    conn.commit()
=======
import sqlite3


DB_NAME = "banco.db"


def conectar():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [item[1] for item in cursor.fetchall()]
    return coluna in colunas


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas_veiculo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            data_despesa TEXT,
            categoria TEXT,
            descricao TEXT,
            valor REAL,
            observacoes TEXT,
            comprovante_path TEXT,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT,
            rg TEXT,
            telefone TEXT,
            endereco TEXT,
            cidade TEXT,
            estado TEXT,
            cep TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo TEXT NOT NULL,
            marca TEXT,
            ano TEXT,
            placa TEXT,
            cor TEXT,
            status TEXT DEFAULT 'Disponível',
            observacoes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            veiculo_id INTEGER NOT NULL,
            data_inicio TEXT,
            data_fim TEXT,
            valor_semanal REAL,
            valor_total_contrato REAL DEFAULT 0,
            caucao REAL,
            status TEXT DEFAULT 'Ativo',
            arquivo_contrato TEXT,
            valor_pago REAL DEFAULT 0,
            status_pagamento TEXT DEFAULT 'Pendente',
            data_pagamento TEXT,
            comprovante_pagamento TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        )
    """)

    if not coluna_existe(cursor, "contratos", "valor_total_contrato"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN valor_total_contrato REAL DEFAULT 0
        """)

    if not coluna_existe(cursor, "contratos", "valor_pago"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN valor_pago REAL DEFAULT 0
        """)

    if not coluna_existe(cursor, "contratos", "status_pagamento"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN status_pagamento TEXT DEFAULT 'Pendente'
        """)

    if not coluna_existe(cursor, "contratos", "data_pagamento"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN data_pagamento TEXT
        """)

    if not coluna_existe(cursor, "contratos", "comprovante_pagamento"):
        cursor.execute("""
            ALTER TABLE contratos
            ADD COLUMN comprovante_pagamento TEXT
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vistorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            contrato_id INTEGER,
            cliente_contrato TEXT,
            vistoriador TEXT,
            data_vistoria TEXT,
            odometro INTEGER,
            observacoes TEXT,
            foto_path TEXT,
            latitude REAL,
            longitude REAL,
            endereco TEXT,
            data_hora_real TEXT,
            hash_vistoria TEXT,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id),
            FOREIGN KEY (contrato_id) REFERENCES contratos(id)
        )
    """)

    if not coluna_existe(cursor, "vistorias", "foto_path"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN foto_path TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "latitude"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN latitude REAL
        """)

    if not coluna_existe(cursor, "vistorias", "longitude"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN longitude REAL
        """)

    if not coluna_existe(cursor, "vistorias", "endereco"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN endereco TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "data_hora_real"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN data_hora_real TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "vistoriador"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN vistoriador TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "cliente_contrato"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN cliente_contrato TEXT
        """)

    if not coluna_existe(cursor, "vistorias", "contrato_id"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN contrato_id INTEGER
        """)

    if not coluna_existe(cursor, "vistorias", "hash_vistoria"):
        cursor.execute("""
            ALTER TABLE vistorias
            ADD COLUMN hash_vistoria TEXT
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manutencoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            data_manutencao TEXT,
            tipo_servico TEXT,
            descricao TEXT,
            valor REAL,
            oficina TEXT,
            km_atual INTEGER,
            proxima_troca_oleo INTEGER,
            observacoes TEXT,
            foto_path TEXT,
            km_prox_revisao INTEGER,
            km_prox_pneu INTEGER,
            km_prox_freio INTEGER,
            km_prox_bateria INTEGER,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        )
    """)

    if not coluna_existe(cursor, "manutencoes", "foto_path"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN foto_path TEXT
        """)

    if not coluna_existe(cursor, "manutencoes", "km_prox_revisao"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN km_prox_revisao INTEGER
        """)

    if not coluna_existe(cursor, "manutencoes", "km_prox_pneu"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN km_prox_pneu INTEGER
        """)

    if not coluna_existe(cursor, "manutencoes", "km_prox_freio"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN km_prox_freio INTEGER
        """)

    if not coluna_existe(cursor, "manutencoes", "km_prox_bateria"):
        cursor.execute("""
            ALTER TABLE manutencoes
            ADD COLUMN km_prox_bateria INTEGER
        """)

    conn.commit()
>>>>>>> 4f4d18623026bf11e99f258282f6ff8da67220f9
    conn.close()