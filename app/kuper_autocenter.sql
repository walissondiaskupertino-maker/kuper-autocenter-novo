-- =====================================================
-- PROJETO: KUPER AUTOCENTER
-- BANCO DE DADOS: kuper_autocenter
-- SGBD: MySQL 8
-- =====================================================

CREATE DATABASE IF NOT EXISTS kuper_autocenter
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
USE kuper_autocenter;

-- =====================================================
-- USUÁRIOS DO SISTEMA
-- =====================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    perfil ENUM('Admin', 'Mecanico', 'Recepcionista')
        NOT NULL DEFAULT 'Recepcionista',
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =====================================================
-- 1. CLIENTES
-- =====================================================

CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf_cnpj VARCHAR(20) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(100),
    endereco TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =====================================================
-- 2. VEÍCULOS
-- =====================================================

CREATE TABLE IF NOT EXISTS veiculos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    placa VARCHAR(10) NOT NULL UNIQUE,
    modelo VARCHAR(50) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    ano INT,
    quilometragem INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_veiculo_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CHECK (quilometragem >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 3. MECÂNICOS
-- =====================================================

CREATE TABLE IF NOT EXISTS mecanicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    telefone VARCHAR(20),
    especialidade VARCHAR(80),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =====================================================
-- 4. PEÇAS E ESTOQUE
-- =====================================================

CREATE TABLE IF NOT EXISTS pecas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE,
    descricao VARCHAR(150) NOT NULL,
    preco_custo DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    preco_venda DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    estoque_atual INT NOT NULL DEFAULT 0,
    estoque_minimo INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CHECK (preco_custo >= 0),
    CHECK (preco_venda >= 0),
    CHECK (estoque_atual >= 0),
    CHECK (estoque_minimo >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 5. SERVIÇOS
-- =====================================================

CREATE TABLE IF NOT EXISTS servicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco_base DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (preco_base >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 6. ORDENS DE SERVIÇO
-- =====================================================

CREATE TABLE IF NOT EXISTS ordens_servico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    veiculo_id INT NOT NULL,
    mecanico_id INT NULL,

    status ENUM(
        'Aberto',
        'Em Andamento',
        'Aguardando Peças',
        'Concluído',
        'Cancelado'
    ) NOT NULL DEFAULT 'Aberto',

    defeito_relatado TEXT,
    diagnostico TEXT,

    valor_total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    data_abertura DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_conclusao DATETIME NULL,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_os_veiculo
        FOREIGN KEY (veiculo_id)
        REFERENCES veiculos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_os_mecanico
        FOREIGN KEY (mecanico_id)
        REFERENCES mecanicos(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CHECK (valor_total >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 7. SERVIÇOS UTILIZADOS NA ORDEM DE SERVIÇO
-- =====================================================

CREATE TABLE IF NOT EXISTS os_servicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    os_id INT NOT NULL,
    servico_id INT NOT NULL,
    quantidade INT NOT NULL DEFAULT 1,
    preco_unitario DECIMAL(10,2) NOT NULL,

    subtotal DECIMAL(10,2)
        GENERATED ALWAYS AS (quantidade * preco_unitario) STORED,

    CONSTRAINT fk_os_servicos_os
        FOREIGN KEY (os_id)
        REFERENCES ordens_servico(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_os_servicos_servico
        FOREIGN KEY (servico_id)
        REFERENCES servicos(id)
        ON DELETE RESTRICT,

    CHECK (quantidade > 0),
    CHECK (preco_unitario >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 8. PEÇAS UTILIZADAS NA ORDEM DE SERVIÇO
-- =====================================================

CREATE TABLE IF NOT EXISTS os_pecas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    os_id INT NOT NULL,
    peca_id INT NOT NULL,
    quantidade INT NOT NULL DEFAULT 1,
    preco_unitario DECIMAL(10,2) NOT NULL,

    subtotal DECIMAL(10,2)
        GENERATED ALWAYS AS (quantidade * preco_unitario) STORED,

    CONSTRAINT fk_os_pecas_os
        FOREIGN KEY (os_id)
        REFERENCES ordens_servico(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_os_pecas_peca
        FOREIGN KEY (peca_id)
        REFERENCES pecas(id)
        ON DELETE RESTRICT,

    CHECK (quantidade > 0),
    CHECK (preco_unitario >= 0)
) ENGINE=InnoDB;

-- =====================================================
-- 9. MOVIMENTAÇÕES DE ESTOQUE
-- =====================================================

CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
    id INT AUTO_INCREMENT PRIMARY KEY,
    peca_id INT NOT NULL,
    os_id INT NULL,

    tipo ENUM(
        'Entrada',
        'Saida',
        'Ajuste'
    ) NOT NULL,

    quantidade INT NOT NULL,
    descricao VARCHAR(255),
    data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mov_peca
        FOREIGN KEY (peca_id)
        REFERENCES pecas(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_mov_os
        FOREIGN KEY (os_id)
        REFERENCES ordens_servico(id)
        ON DELETE SET NULL,

    CHECK (quantidade > 0)
) ENGINE=InnoDB;

-- =====================================================
-- 10. FINANCEIRO
-- =====================================================

CREATE TABLE IF NOT EXISTS financeiro (
    id INT AUTO_INCREMENT PRIMARY KEY,
    os_id INT NULL,

    tipo ENUM(
        'Entrada',
        'Saida'
    ) NOT NULL,

    descricao VARCHAR(255) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    categoria VARCHAR(80),
    forma_pagamento VARCHAR(50),

    data_movimentacao DATETIME
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_financeiro_os
        FOREIGN KEY (os_id)
        REFERENCES ordens_servico(id)
        ON DELETE SET NULL,

    CHECK (valor > 0)
) ENGINE=InnoDB;

INSERT INTO clientes
(nome, cpf_cnpj, telefone, email, endereco)
VALUES
('João da Silva', '123.456.789-00',
 '(63) 99999-1111', 'joao@email.com', 'Palmas - TO'),

('Maria Oliveira', '234.567.890-11',
 '(63) 99999-2222', 'maria@email.com', 'Araguaína - TO'),

('Carlos Santos', '345.678.901-22',
 '(63) 99999-3333', 'carlos@email.com', 'Porto Nacional - TO'),

('Ana Ferreira', '456.789.012-33',
 '(63) 99999-4444', 'ana@email.com', 'Palmas - TO');
 
 INSERT INTO veiculos
(cliente_id, placa, modelo, marca, ano, quilometragem)
VALUES
(1, 'QWE1A23', 'Corolla', 'Toyota', 2022, 35000),
(1, 'RTY2B34', 'Civic', 'Honda', 2020, 48000),
(2, 'UIO3C45', 'Onix', 'Chevrolet', 2023, 22000),
(3, 'PAS4D56', 'Hilux', 'Toyota', 2021, 55000),
(4, 'DFG5E67', 'HB20', 'Hyundai', 2022, 30000);

INSERT INTO mecanicos
(nome, cpf, telefone, especialidade)
VALUES
('Roberto Almeida', '111.222.333-44',
 '(63) 99911-1111', 'Motor'),

('Paulo Henrique', '222.333.444-55',
 '(63) 99922-2222', 'Suspensão'),

('Marcos Ferreira', '333.444.555-66',
 '(63) 99933-3333', 'Freios'),

('André Costa', '444.555.666-77',
 '(63) 99944-4444', 'Injeção eletrônica');
 
 INSERT INTO pecas
(codigo, descricao, preco_custo, preco_venda,
 estoque_atual, estoque_minimo)
VALUES
('P001', 'Óleo de motor 5W30', 25.00, 45.00, 30, 5),
('P002', 'Filtro de óleo', 15.00, 30.00, 20, 5),
('P003', 'Pastilha de freio', 65.00, 110.00, 12, 3),
('P004', 'Filtro de ar', 30.00, 55.00, 15, 5),
('P005', 'Vela de ignição', 20.00, 40.00, 25, 5),
('P006', 'Correia dentada', 90.00, 150.00, 2, 5);

INSERT INTO servicos
(nome, descricao, preco_base)
VALUES
('Troca de óleo', 'Substituição do óleo do motor', 80.00),

('Revisão completa', 'Inspeção geral do veículo', 250.00),

('Alinhamento', 'Alinhamento da direção', 90.00),

('Balanceamento', 'Balanceamento das rodas', 70.00),

('Troca de pastilhas', 'Substituição das pastilhas de freio', 120.00),

('Revisão de suspensão', 'Inspeção dos componentes da suspensão', 180.00);


INSERT INTO ordens_servico
(veiculo_id, mecanico_id, status,
 defeito_relatado, diagnostico)
VALUES
(1, 1, 'Concluído',
 'Motor apresentando ruído e necessidade de revisão',
 'Realizada troca de óleo e filtro'),

(2, 3, 'Concluído',
 'Freios apresentando ruído',
 'Pastilhas de freio desgastadas'),

(3, 2, 'Em Andamento',
 'Cliente relata necessidade de revisão',
 'Revisão geral em execução'),

(4, 4, 'Aguardando Peças',
 'Problema no sistema de injeção',
 'Necessária substituição de componente'),

(5, 1, 'Aberto',
 'Cliente solicita revisão preventiva',
 'Aguardando avaliação');
 
 INSERT INTO os_servicos
(os_id, servico_id, quantidade, preco_unitario)
VALUES
(1, 1, 1, 80.00),
(2, 5, 1, 120.00),
(3, 2, 1, 250.00),
(5, 3, 1, 90.00);

INSERT INTO os_pecas
(os_id, peca_id, quantidade, preco_unitario)
VALUES
(1, 1, 1, 45.00),
(1, 2, 1, 30.00),
(2, 3, 1, 110.00),
(3, 4, 1, 55.00);

INSERT INTO movimentacoes_estoque
(peca_id, os_id, tipo, quantidade, descricao)
VALUES
(1, 1, 'Saida', 1, 'Óleo utilizado na OS 1'),
(2, 1, 'Saida', 1, 'Filtro utilizado na OS 1'),
(3, 2, 'Saida', 1, 'Pastilha utilizada na OS 2'),
(4, 3, 'Saida', 1, 'Filtro utilizado na OS 3');

UPDATE pecas
SET estoque_atual = estoque_atual - 1
WHERE id IN (1, 2, 3, 4);

UPDATE ordens_servico os

SET valor_total =

    COALESCE((
        SELECT SUM(subtotal)
        FROM os_servicos
        WHERE os_id = os.id
    ), 0)

    +

    COALESCE((
        SELECT SUM(subtotal)
        FROM os_pecas
        WHERE os_id = os.id
    ), 0);
    
    UPDATE ordens_servico
SET data_conclusao = CURRENT_TIMESTAMP
WHERE status = 'Concluído';

INSERT INTO financeiro
(os_id, tipo, descricao, valor, categoria, forma_pagamento)
VALUES
(1, 'Entrada', 'Pagamento da OS 1', 155.00,
 'Serviços', 'Pix'),

(2, 'Entrada', 'Pagamento da OS 2', 230.00,
 'Serviços', 'Cartão de Débito'),

(3, 'Entrada', 'Pagamento parcial da OS 3', 100.00,
 'Serviços', 'Dinheiro'),

(NULL, 'Saida', 'Compra de materiais', 500.00,
 'Estoque', 'Pix'),

(NULL, 'Saida', 'Despesas de energia elétrica', 250.00,
 'Despesas fixas', 'Boleto'),

(NULL, 'Saida', 'Manutenção de equipamentos', 150.00,
 'Manutenção', 'Pix');
 
 -- DASHBOARD GERAL

CREATE OR REPLACE VIEW vw_dashboard_resumo AS
SELECT
    (SELECT COUNT(*) FROM clientes) AS total_clientes,

    (SELECT COUNT(*) FROM veiculos) AS total_veiculos,

    (SELECT COUNT(*) FROM mecanicos
     WHERE ativo = TRUE) AS total_mecanicos,

    (SELECT COUNT(*) FROM ordens_servico
     WHERE status = 'Aberto') AS os_abertas,

    (SELECT COUNT(*) FROM ordens_servico
     WHERE status = 'Em Andamento') AS os_andamento,

    (SELECT COUNT(*) FROM ordens_servico
     WHERE status = 'Aguardando Peças') AS os_aguardando,

    (SELECT COUNT(*) FROM ordens_servico
     WHERE status = 'Concluído') AS os_concluidas,

    (SELECT COALESCE(SUM(valor), 0)
     FROM financeiro
     WHERE tipo = 'Entrada') AS entradas,

    (SELECT COALESCE(SUM(valor), 0)
     FROM financeiro
     WHERE tipo = 'Saida') AS saidas;
     
     -- RELATÓRIO DE ORDENS DE SERVIÇO

CREATE OR REPLACE VIEW vw_relatorio_ordens_servico AS
SELECT
    os.id AS os_id,
    c.nome AS cliente,
    c.telefone,
    v.placa,
    v.marca,
    v.modelo,
    m.nome AS mecanico,
    os.status,
    os.valor_total,
    os.data_abertura,
    os.data_conclusao

FROM ordens_servico os

INNER JOIN veiculos v
    ON os.veiculo_id = v.id

INNER JOIN clientes c
    ON v.cliente_id = c.id

LEFT JOIN mecanicos m
    ON os.mecanico_id = m.id;
    
    SHOW TABLES;
    SELECT * FROM vw_dashboard_resumo;
    
    SELECT * FROM vw_relatorio_ordens_servico;
 
 SELECT * FROM clientes;
 SELECT * FROM veiculos;
 SELECT * FROM ordens_servico;
 SELECT * FROM pecas;
 SELECT * FROM financeiro;
 SELECT * FROM vw_dashboard_resumo;
 SELECT * FROM vw_relatorio_ordens_servico;
 
 