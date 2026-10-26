-- Script de criação equivalente ao que o SQLAlchemy gera automaticamente na inicialização
-- (Base.metadata.create_all). Útil para recriar a estrutura manualmente (SQLite).

CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       VARCHAR(120) NOT NULL UNIQUE,
    senha_hash  VARCHAR(255) NOT NULL,
    criado_em   DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_usuarios_email ON usuarios (email);

CREATE TABLE IF NOT EXISTS categorias (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        VARCHAR(80) NOT NULL,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios (id)
);
CREATE INDEX IF NOT EXISTS ix_categorias_usuario_id ON categorias (usuario_id);

CREATE TABLE IF NOT EXISTS transacoes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao     VARCHAR(200) NOT NULL,
    valor         NUMERIC(12, 2) NOT NULL,
    tipo          VARCHAR(7) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    data          DATE NOT NULL,
    categoria_id  INTEGER REFERENCES categorias (id),
    usuario_id    INTEGER NOT NULL REFERENCES usuarios (id),
    criado_em     DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_transacoes_tipo ON transacoes (tipo);
CREATE INDEX IF NOT EXISTS ix_transacoes_data ON transacoes (data);
CREATE INDEX IF NOT EXISTS ix_transacoes_usuario_id ON transacoes (usuario_id);
