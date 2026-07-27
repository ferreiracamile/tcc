CREATE DATABASE IF NOT EXISTS almoxarifado;
USE almoxarifado;

-- Tabela de Estoque
CREATE TABLE IF NOT EXISTS estoque (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL,
    qntd INT NOT NULL DEFAULT 0,
    estoque_minimo INT NOT NULL DEFAULT 0,
    descricao TEXT,
    preco DECIMAL(10,2) DEFAULT 0.00,
    foto VARCHAR(500),
    categoria VARCHAR(100)
);

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    funcao VARCHAR(50) NOT NULL DEFAULT 'user'
);

-- Tabela de Histórico de Movimentações
CREATE TABLE IF NOT EXISTS historico (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario VARCHAR(255) NOT NULL,
    item_nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    quantidade INT NOT NULL,
    finalidade VARCHAR(255),
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Inserção de Usuário Administrador Padrão (Senha: admin123 hash bcrypt/pbkdf2)
-- Para conveniência, a aplicação app.py também verifica e cria os dados padrão se vazios.
INSERT INTO usuarios (usuario, senha, funcao) 
VALUES ('admin', 'scrypt:32768:8:1$k04d3eFq9Hk1V9xZ$17a26f8ed2541cf237b6703edc98bf35a4d6ef292882798e1f0e42d76f80998fcf6eb54cf2ebff9ecb9b8b0e77dce7e4f8ecaaedec7ce71bb57200787e91bb64', 'admin')
ON DUPLICATE KEY UPDATE usuario=usuario;

INSERT INTO usuarios (usuario, senha, funcao) 
VALUES ('usuario', 'scrypt:32768:8:1$k04d3eFq9Hk1V9xZ$17a26f8ed2541cf237b6703edc98bf35a4d6ef292882798e1f0e42d76f80998fcf6eb54cf2ebff9ecb9b8b0e77dce7e4f8ecaaedec7ce71bb57200787e91bb64', 'user')
ON DUPLICATE KEY UPDATE usuario=usuario;

-- Dados Iniciais do Estoque para Demonstração
INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria) VALUES
('Chave de Fenda 1/4', 15, 5, 'Chave de fenda em aço cromo vanádio com cabo isolado', 18.50, 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500', 'Mecânica'),
('Multímetro Digital', 8, 3, 'Multímetro digital com pontas de prova e medição de tensão/corrente', 120.00, 'https://images.unsplash.com/photo-1581092335397-9583fe92d232?w=500', 'Elétrica'),
('Martelo de Borracha', 12, 4, 'Martelo de borracha preta 450g para montagem de bancadas', 35.00, 'https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?w=500', 'Geral'),
('Alicete Universal 8"', 20, 6, 'Alicate universal em aço carbono com cabo antiderrapante', 42.90, 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=500', 'Mecânica');

-- Histórico de Amostra
INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora) VALUES
('admin', 'Chave de Fenda 1/4', 'Entrada', 15, 'Estoque inicial da oficina SENAI', NOW()),
('admin', 'Multímetro Digital', 'Entrada', 10, 'Compra de suprimentos para laboratório', NOW()),
('usuario', 'Multímetro Digital', 'Saída', 2, 'Aula do professor Roger no laboratório 2', NOW());
