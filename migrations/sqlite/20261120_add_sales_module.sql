-- Faça backup e aplique uma única vez antes de publicar a versão com vendas.
-- Esta migração é aditiva e preserva os registros existentes.
BEGIN IMMEDIATE;

CREATE TABLE vendas (
    id INTEGER NOT NULL PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    veiculo_id INTEGER NOT NULL,
    vendedor_id INTEGER NOT NULL,
    data DATETIME NOT NULL,
    desconto NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(9) NOT NULL DEFAULT 'aberta',
    total NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT ck_vendas_desconto_nao_negativo CHECK (desconto >= 0),
    CONSTRAINT ck_vendas_total_nao_negativo CHECK (total >= 0),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
    FOREIGN KEY (veiculo_id) REFERENCES veiculos(id) ON DELETE RESTRICT,
    FOREIGN KEY (vendedor_id) REFERENCES usuarios(id) ON DELETE RESTRICT
);
CREATE INDEX ix_vendas_cliente_id ON vendas(cliente_id);
CREATE INDEX ix_vendas_veiculo_id ON vendas(veiculo_id);
CREATE INDEX ix_vendas_vendedor_id ON vendas(vendedor_id);

CREATE TABLE itens_venda (
    id INTEGER NOT NULL PRIMARY KEY,
    venda_id INTEGER NOT NULL,
    tipo VARCHAR(7) NOT NULL,
    peca_id INTEGER,
    servico_id INTEGER,
    quantidade INTEGER NOT NULL,
    preco_unitario NUMERIC(10, 2) NOT NULL,
    CONSTRAINT ck_itens_venda_quantidade_positiva CHECK (quantidade > 0),
    CONSTRAINT ck_itens_venda_preco_nao_negativo CHECK (preco_unitario >= 0),
    CONSTRAINT ck_itens_venda_tipo_referencia CHECK (
        (tipo = 'peca' AND peca_id IS NOT NULL AND servico_id IS NULL) OR
        (tipo = 'servico' AND servico_id IS NOT NULL AND peca_id IS NULL)
    ),
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
    FOREIGN KEY (peca_id) REFERENCES pecas(id) ON DELETE RESTRICT,
    FOREIGN KEY (servico_id) REFERENCES servicos(id) ON DELETE RESTRICT
);
CREATE INDEX ix_itens_venda_venda_id ON itens_venda(venda_id);

CREATE TABLE pagamentos (
    id INTEGER NOT NULL PRIMARY KEY,
    venda_id INTEGER NOT NULL,
    valor NUMERIC(10, 2) NOT NULL,
    metodo VARCHAR(14) NOT NULL,
    parcelas INTEGER NOT NULL DEFAULT 1,
    data DATETIME NOT NULL,
    CONSTRAINT ck_pagamentos_valor_positivo CHECK (valor > 0),
    CONSTRAINT ck_pagamentos_parcelas CHECK (parcelas BETWEEN 1 AND 12),
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE
);
CREATE INDEX ix_pagamentos_venda_id ON pagamentos(venda_id);

ALTER TABLE financeiro
    ADD COLUMN venda_id INTEGER REFERENCES vendas(id) ON DELETE SET NULL;
CREATE INDEX ix_financeiro_venda_id ON financeiro(venda_id);

COMMIT;
