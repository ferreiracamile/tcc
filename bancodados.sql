-- ========================================================
-- BANCO DE DADOS: ALMOXARIFADO (SENAI - PROJETO TCC)
-- ========================================================
-- Este script deve ser executado no MySQL Workbench ou no
-- container Docker para criar a base e as tabelas do sistema.
-- ========================================================

CREATE DATABASE IF NOT EXISTS almoxarifado;
USE almoxarifado;

-- 1. Tabela de Estoque
CREATE TABLE IF NOT EXISTS estoque (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    qntd INT NOT NULL DEFAULT 0,
    estoque_minimo INT NOT NULL DEFAULT 0,
    descricao TEXT,
    preco DECIMAL(10,2) DEFAULT 0.00,
    foto VARCHAR(500),
    categoria VARCHAR(100)
);

-- 2. Tabela de Usuários (Autenticação via Bcrypt)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    funcao VARCHAR(50) NOT NULL DEFAULT 'user'
);

-- 3. Tabela de Histórico de Movimentações
CREATE TABLE IF NOT EXISTS historico (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario VARCHAR(100) NOT NULL,
    item_nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    quantidade INT NOT NULL,
    finalidade VARCHAR(150),
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO usuarios (usuario, senha, funcao) 
VALUES 
    ('admin', '$2b$12$ZttIbkUMAX682KVIbSJmmuu.PIt9huqBrSVQx5P9K.g.WH6pr0b0.', 'admin'),
    ('usuario', '$2b$12$ZttIbkUMAX682KVIbSJmmuu.PIt9huqBrSVQx5P9K.g.WH6pr0b0.', 'user')
ON DUPLICATE KEY UPDATE senha=VALUES(senha);

INSERT INTO usuarios (usuario, senha, funcao) 
VALUES ('chico', '$2b$12$ZttIbkUMAX682KVIbSJmmuu.PIt9huqBrSVQx5P9K.g.WH6pr0b0.', 'admin')
AS novos_dados 
ON DUPLICATE KEY UPDATE senha = novos_dados.senha;

-- ========================================================
-- DADOS INICIAIS
-- ========================================================

-- Usuários Padrão:
-- admin   / senha: 123 (Hash Bcrypt)
-- usuario / senha: 123 (Hash Bcrypt)
INSERT INTO usuarios (usuario, senha, funcao) 
VALUES 
    ('admin', '$2b$12$ZttIbkUMAX682KVIbSJmmuu.PIt9huqBrSVQx5P9K.g.WH6pr0b0.', 'admin'),
    ('usuario', '$2b$12$ZttIbkUMAX682KVIbSJmmuu.PIt9huqBrSVQx5P9K.g.WH6pr0b0.', 'user')
ON DUPLICATE KEY UPDATE senha=VALUES(senha);

-- Estoque Inicial: O sistema inicia com estoque zerado.
-- (Caso queira carregar dados de teste no futuro, descomente o bloco abaixo):
-- INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria) VALUES
-- ('Chave de Fenda 1/4', 15, 5, 'Chave de fenda em aço cromo vanádio com cabo isolado', 18.50, 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500', 'Mecânica'),
-- ('Multímetro Digital', 8, 3, 'Multímetro digital com pontas de prova e medição de tensão/corrente', 120.00, 'https://images.unsplash.com/photo-1581092335397-9583fe92d232?w=500', 'Elétrica'),
-- ('Martelo de Borracha', 12, 4, 'Martelo de borracha preta 450g para montagem de bancadas', 35.00, 'https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?w=500', 'Geral'),
-- ('Alicate Universal 8"', 20, 6, 'Alicate universal em aço carbono com cabo antiderrapante', 42.90, 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=500', 'Mecânica')
-- ON DUPLICATE KEY UPDATE nome=VALUES(nome);
