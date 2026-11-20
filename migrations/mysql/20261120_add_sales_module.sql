-- Faça backup e aplique uma única vez antes de publicar a versão com vendas.
-- Esta migração é aditiva e preserva os registros existentes.
ALTER TABLE usuarios
    MODIFY perfil ENUM('Admin', 'Vendedor', 'Mecanico', 'Recepcionista')
        NOT NULL DEFAULT 'Recepcionista';

CREATE TABLE vendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    veiculo_id INT NOT NULL,
    vendedor_id INT NOT NULL,
    data DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    desconto DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status ENUM('aberta', 'paga', 'cancelada') NOT NULL DEFAULT 'aberta',
    total DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    KEY ix_vendas_cliente_id (cliente_id),
    KEY ix_vendas_veiculo_id (veiculo_id),
    KEY ix_vendas_vendedor_id (vendedor_id),
    CONSTRAINT fk_vendas_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
    CONSTRAINT fk_vendas_veiculo
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id) ON DELETE RESTRICT,
    CONSTRAINT fk_vendas_vendedor
        FOREIGN KEY (vendedor_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT ck_vendas_desconto_nao_negativo CHECK (desconto >= 0),
    CONSTRAINT ck_vendas_total_nao_negativo CHECK (total >= 0)
) ENGINE=InnoDB;

CREATE TABLE itens_venda (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venda_id INT NOT NULL,
    tipo ENUM('peca', 'servico') NOT NULL,
    peca_id INT NULL,
    servico_id INT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    KEY ix_itens_venda_venda_id (venda_id),
    CONSTRAINT fk_itens_venda_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
    CONSTRAINT fk_itens_venda_peca
        FOREIGN KEY (peca_id) REFERENCES pecas(id) ON DELETE RESTRICT,
    CONSTRAINT fk_itens_venda_servico
        FOREIGN KEY (servico_id) REFERENCES servicos(id) ON DELETE RESTRICT,
    CONSTRAINT ck_itens_venda_quantidade_positiva CHECK (quantidade > 0),
    CONSTRAINT ck_itens_venda_preco_nao_negativo CHECK (preco_unitario >= 0),
    CONSTRAINT ck_itens_venda_tipo_referencia CHECK (
        (tipo = 'peca' AND peca_id IS NOT NULL AND servico_id IS NULL) OR
        (tipo = 'servico' AND servico_id IS NOT NULL AND peca_id IS NULL)
    )
) ENGINE=InnoDB;

CREATE TABLE pagamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venda_id INT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    metodo ENUM('dinheiro', 'pix', 'cartao_credito', 'cartao_debito') NOT NULL,
    parcelas INT NOT NULL DEFAULT 1,
    data DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY ix_pagamentos_venda_id (venda_id),
    CONSTRAINT fk_pagamentos_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
    CONSTRAINT ck_pagamentos_valor_positivo CHECK (valor > 0),
    CONSTRAINT ck_pagamentos_parcelas CHECK (parcelas BETWEEN 1 AND 12)
) ENGINE=InnoDB;

ALTER TABLE financeiro
    ADD COLUMN venda_id INT NULL,
    ADD KEY ix_financeiro_venda_id (venda_id),
    ADD CONSTRAINT fk_financeiro_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE SET NULL;
