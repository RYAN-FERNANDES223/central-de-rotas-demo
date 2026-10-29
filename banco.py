"""Banco SQLite do protótipo local. Não contém credenciais de produção."""
import json
import os
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path

CAMINHO_BANCO = Path(os.getenv('ROTAS_DB', str(Path(__file__).with_name('rotas.db'))))
# Cada visitante da demonstração tem seu próprio banco temporário.
# ContextVar evita que sessões concorrentes alterem o caminho uma da outra.
_BANCO_DA_SESSAO = ContextVar('banco_da_sessao', default=None)


def selecionar_banco(caminho):
    _BANCO_DA_SESSAO.set(str(caminho))


def agora():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


@contextmanager
def conectar():
    conn = sqlite3.connect(_BANCO_DA_SESSAO.get() or CAMINHO_BANCO, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA busy_timeout = 20000')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def preparar_banco():
    """Cria estruturas novas sem apagar os registros de rotas da v0.1."""
    with conectar() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS motoristas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf_hash TEXT UNIQUE,
            ativo INTEGER NOT NULL DEFAULT 1
        )''')
        colunas_motorista = {r['name'] for r in conn.execute('PRAGMA table_info(motoristas)')}
        if 'cpf_hash' not in colunas_motorista:
            conn.execute('ALTER TABLE motoristas ADD COLUMN cpf_hash TEXT')
        if 'ativo' not in colunas_motorista:
            conn.execute('ALTER TABLE motoristas ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_motorista_cpf ON motoristas(cpf_hash)')
        conn.execute('''CREATE TABLE IF NOT EXISTS rotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origem TEXT NOT NULL,
            destino TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            observacoes TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'disponivel',
            motorista_id INTEGER REFERENCES motoristas(id),
            criada_em TEXT NOT NULL,
            assumida_em TEXT
        )''')
        # Migração pequena: a v0.1 não registrava o número do cliente.
        cols = {r['name'] for r in conn.execute('PRAGMA table_info(rotas)')}
        if 'cliente_telefone' not in cols:
            conn.execute('ALTER TABLE rotas ADD COLUMN cliente_telefone TEXT')

        conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            telefone TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            papel TEXT NOT NULL CHECK (papel IN ('cliente', 'motorista', 'admin')),
            nome_confirmado INTEGER NOT NULL DEFAULT 0 CHECK (nome_confirmado IN (0, 1)),
            cpf_hash TEXT,
            cpf_confirmado INTEGER NOT NULL DEFAULT 0 CHECK (cpf_confirmado IN (0, 1)),
            ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
            motorista_id INTEGER UNIQUE REFERENCES motoristas(id)
        )''')
        # Atualiza bancos anteriores sem remover clientes, motoristas ou rotas.
        colunas_usuario = {linha['name'] for linha in conn.execute('PRAGMA table_info(usuarios)')}
        if 'nome_confirmado' not in colunas_usuario:
            conn.execute('ALTER TABLE usuarios ADD COLUMN nome_confirmado INTEGER NOT NULL DEFAULT 0')
            # Preserva nomes de clientes já preenchidos em versões anteriores.
            conn.execute("""
                UPDATE usuarios SET nome_confirmado=1
                WHERE papel='cliente' AND TRIM(nome) NOT IN ('', 'Cliente')
            """)

        if 'cpf_hash' not in colunas_usuario:
            conn.execute('ALTER TABLE usuarios ADD COLUMN cpf_hash TEXT')
        if 'cpf_confirmado' not in colunas_usuario:
            conn.execute('ALTER TABLE usuarios ADD COLUMN cpf_confirmado INTEGER NOT NULL DEFAULT 0')

        conn.execute('''CREATE TABLE IF NOT EXISTS conversas (
            telefone TEXT PRIMARY KEY REFERENCES usuarios(telefone),
            etapa TEXT NOT NULL,
            dados_json TEXT NOT NULL DEFAULT '{}',
            atualizada_em TEXT NOT NULL
        )''')


def obter_usuario(conn, telefone):
    linha = conn.execute('SELECT * FROM usuarios WHERE telefone = ?', (telefone,)).fetchone()
    return dict(linha) if linha else None


def garantir_cliente(telefone):
    """Somente quem não existe vira cliente. Nunca promove motorista/admin."""
    with conectar() as conn:
        conn.execute('''INSERT OR IGNORE INTO usuarios (telefone, nome, papel)
                        VALUES (?, 'Cliente', 'cliente')''', (telefone,))
        return obter_usuario(conn, telefone)


def criar_admin_local(telefone, nome='Administrador de teste'):
    """Utilizado APENAS na simulação local, nunca por mensagem de WhatsApp."""
    with conectar() as conn:
        atual = obter_usuario(conn, telefone)
        if atual and atual['papel'] != 'admin':
            raise ValueError('Número já usado por outro perfil; não houve promoção.')
        if not atual:
            conn.execute('INSERT INTO usuarios(telefone,nome,papel) VALUES (?, ?, ?)',
                         (telefone, nome, 'admin'))


def salvar_conversa(conn, telefone, etapa, dados):
    conn.execute('''INSERT INTO conversas (telefone,etapa,dados_json,atualizada_em)
                    VALUES (?,?,?,?)
                    ON CONFLICT(telefone) DO UPDATE SET
                    etapa=excluded.etapa,dados_json=excluded.dados_json,
                    atualizada_em=excluded.atualizada_em''',
                 (telefone, etapa, json.dumps(dados, ensure_ascii=False), agora()))


def obter_conversa(conn, telefone):
    linha = conn.execute('SELECT * FROM conversas WHERE telefone=?', (telefone,)).fetchone()
    return (linha['etapa'], json.loads(linha['dados_json'])) if linha else (None, {})


def limpar_conversa(conn, telefone):
    conn.execute('DELETE FROM conversas WHERE telefone=?', (telefone,))
