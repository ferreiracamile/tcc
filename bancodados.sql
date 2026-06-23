CREATE DATABASE almoxarifado;

USE almoxarifado;

CREATE TABLE estoque (
    id INT PRIMARY KEY auto_increment,
    nome VARCHAR(255),
    qntd INT,
    estoque_minimo INT,
    descricao varchar(255),
    preco DECIMAL,
    foto varchar(255),
    categoria VARCHAR(255)
);

CREATE TABLE usuarios (
    id INT PRIMARY KEY auto_increment,
    usuario VARCHAR(255),
	senha VARCHAR(255),
    funcao VARCHAR(255)
);



