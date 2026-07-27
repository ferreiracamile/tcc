import os
import io
import csv
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'senai_almoxarifado_secret_key_tcc'

# ==========================================
# GESTOR DE BANCO DE DADOS (MySQL com Fallback SQLite)
# ==========================================
USE_SQLITE_FALLBACK = False

def get_db():
    global USE_SQLITE_FALLBACK
    if not USE_SQLITE_FALLBACK:
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                port=3306,
                database='almoxarifado'
            )
            return conn, 'mysql'
        except Exception as e:
            print(f"[Aviso] Conexão MySQL não disponível ({e}). Utilizando fallback SQLite local.")
            USE_SQLITE_FALLBACK = True

    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), 'almoxarifado.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn, 'sqlite'

def init_db():
    conn, db_type = get_db()
    cursor = conn.cursor()

    if db_type == 'mysql':
        cursor.execute("""
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
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT PRIMARY KEY AUTO_INCREMENT,
            usuario VARCHAR(255) UNIQUE NOT NULL,
            senha VARCHAR(255) NOT NULL,
            funcao VARCHAR(50) NOT NULL DEFAULT 'user'
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INT PRIMARY KEY AUTO_INCREMENT,
            usuario VARCHAR(255) NOT NULL,
            item_nome VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            quantidade INT NOT NULL,
            finalidade VARCHAR(255),
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
    else: # sqlite
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            qntd INTEGER NOT NULL DEFAULT 0,
            estoque_minimo INTEGER NOT NULL DEFAULT 0,
            descricao TEXT,
            preco REAL DEFAULT 0.00,
            foto TEXT,
            categoria TEXT
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            funcao TEXT NOT NULL DEFAULT 'user'
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            item_nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            finalidade TEXT,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

    # Popular usuários padrão se vazios
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    res = cursor.fetchone()
    count_user = res[0] if type(res) is tuple else res['COUNT(*)']
    if count_user == 0:
        pass_hash = generate_password_hash('123456')
        if db_type == 'mysql':
            cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES (%s, %s, %s)", ('admin', pass_hash, 'admin'))
            cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES (%s, %s, %s)", ('usuario', pass_hash, 'user'))
        else:
            cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES (?, ?, ?)", ('admin', pass_hash, 'admin'))
            cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES (?, ?, ?)", ('usuario', pass_hash, 'user'))

    # Popular estoque de teste se vazio
    cursor.execute("SELECT COUNT(*) FROM estoque")
    res_est = cursor.fetchone()
    count_est = res_est[0] if type(res_est) is tuple else res_est['COUNT(*)']
    if count_est == 0:
        itens_demo = [
            ('Chave de Fenda 1/4', 15, 5, 'Chave de fenda em aço cromo vanádio com cabo isolado', 18.50, 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500', 'Mecânica'),
            ('Multímetro Digital', 8, 3, 'Multímetro digital com pontas de prova e medição de tensão/corrente', 120.00, 'https://images.unsplash.com/photo-1581092335397-9583fe92d232?w=500', 'Elétrica'),
            ('Martelo de Borracha', 12, 4, 'Martelo de borracha preta 450g para montagem de bancadas', 35.00, 'https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?w=500', 'Geral'),
            ('Alicate Universal 8"', 20, 6, 'Alicate universal em aço carbono com cabo antiderrapante', 42.90, 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=500', 'Mecânica')
        ]
        for item in itens_demo:
            if db_type == 'mysql':
                cursor.execute("INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria) VALUES (%s,%s,%s,%s,%s,%s,%s)", item)
            else:
                cursor.execute("INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria) VALUES (?,?,?,?,?,?,?)", item)

        # Histórico demo
        demo_hist = [
            ('admin', 'Chave de Fenda 1/4', 'Entrada', 15, 'Estoque inicial da oficina SENAI'),
            ('admin', 'Multímetro Digital', 'Entrada', 10, 'Compra de suprimentos para laboratório'),
            ('usuario', 'Multímetro Digital', 'Saída', 2, 'Aula do professor Roger no laboratório 2')
        ]
        for h in demo_hist:
            if db_type == 'mysql':
                cursor.execute("INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora) VALUES (%s,%s,%s,%s,%s,NOW())", h)
            else:
                cursor.execute("INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora) VALUES (?,?,?,?,?,datetime('now'))", h)

    conn.commit()
    conn.close()

# Inicializar DB ao carregar
try:
    init_db()
except Exception as err:
    print(f"Erro na inicialização do BD: {err}")

# ==========================================
# DECORADORES DE AUTENTICAÇÃO
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Por favor, faça login para acessar o sistema.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        if session.get('funcao') != 'admin':
            flash('Acesso negado. Esta página requer privilégios de Administrador.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# ROTAS DA APLICAÇÃO
# ==========================================

@app.route("/", methods=['GET', 'POST'])
@app.route("/login", methods=['GET', 'POST'])
@app.route("/login.html", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        conn, db_type = get_db()
        cursor = conn.cursor()

        if db_type == 'mysql':
            cursor.execute("SELECT usuario, senha, funcao FROM usuarios WHERE usuario = %s", (usuario,))
            user = cursor.fetchone()
        else:
            cursor.execute("SELECT usuario, senha, funcao FROM usuarios WHERE usuario = ?", (usuario,))
            row = cursor.fetchone()
            user = tuple(row) if row else None

        conn.close()

        if user:
            db_usuario, db_senha_hash, db_funcao = user[0], user[1], user[2]
            # Suporte para hash de teste em texto plano ou werkzeug generate_password_hash
            senha_valida = False
            if db_senha_hash == senha or db_senha_hash == '123456':
                senha_valida = True
            else:
                try:
                    senha_valida = check_password_hash(db_senha_hash, senha)
                except Exception:
                    senha_valida = False

            if senha_valida:
                session['usuario'] = db_usuario
                session['funcao'] = db_funcao
                flash(f'Bem-vindo, {db_usuario}!', 'success')
                return redirect(url_for('home'))

        flash('Usuário ou senha inválidos!', 'danger')
        return render_template("login.html", erro="Credenciais inválidas")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

@app.route("/home")
@app.route("/home.html")
@login_required
def home():
    conn, db_type = get_db()
    cursor = conn.cursor()

    if db_type == 'mysql':
        cursor.execute("SELECT id, nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY nome ASC")
        itens_rows = cursor.fetchall()
        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM historico WHERE tipo = 'Entrada' AND DATE(data_hora) = CURDATE()")
        entradas_hoje = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM historico WHERE tipo = 'Saída' AND DATE(data_hora) = CURDATE()")
        saidas_hoje = cursor.fetchone()[0]
    else:
        cursor.execute("SELECT id, nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY nome ASC")
        itens_rows = [tuple(r) for r in cursor.fetchall()]
        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM historico WHERE tipo = 'Entrada' AND date(data_hora) = date('now')")
        entradas_hoje = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM historico WHERE tipo = 'Saída' AND date(data_hora) = date('now')")
        saidas_hoje = cursor.fetchone()[0]

    conn.close()

    total_itens = sum(item[2] for item in itens_rows) if itens_rows else 0

    return render_template("home.html", itens=itens_rows, total_itens=total_itens, entradas_hoje=entradas_hoje, saidas_hoje=saidas_hoje)

@app.route("/novos-itens", methods=['GET', 'POST'])
@app.route("/novos-itens.html", methods=['GET', 'POST'])
@login_required
def novositens():
    conn, db_type = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        qntd = int(request.form.get('qntd', 0))
        estoque_minimo = int(request.form.get('estoque_minimo', 0))
        descricao = request.form.get('descricao', '')
        preco = float(request.form.get('preco', 0.0))
        foto = request.form.get('foto', '')
        categoria = request.form.get('categoria', 'Geral')

        if not foto:
            foto = 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500'

        if db_type == 'mysql':
            cursor.execute("""
                INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nome, qntd, estoque_minimo, descricao, preco, foto, categoria))
            cursor.execute("""
                INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (session['usuario'], nome, 'Entrada', qntd, 'Cadastro inicial de novo item'))
        else:
            cursor.execute("""
                INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nome, qntd, estoque_minimo, descricao, preco, foto, categoria))
            cursor.execute("""
                INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (session['usuario'], nome, 'Entrada', qntd, 'Cadastro inicial de novo item'))

        conn.commit()
        flash(f'Item "{nome}" cadastrado com sucesso!', 'success')
        conn.close()
        return redirect(url_for('novositens'))

    if db_type == 'mysql':
        cursor.execute("SELECT id, nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY id DESC")
        itens = cursor.fetchall()
    else:
        cursor.execute("SELECT id, nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY id DESC")
        itens = [tuple(r) for r in cursor.fetchall()]

    conn.close()
    return render_template("novos-itens.html", itens=itens)

@app.route("/entrada-saida", methods=['GET', 'POST'])
@app.route("/entrada-saida.html", methods=['GET', 'POST'])
@login_required
def entradasaida():
    conn, db_type = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        tipo = request.form.get('tipo') # 'Entrada' ou 'Saída'
        item_id = request.form.get('item_id')
        quantidade = int(request.form.get('quantidade', 0))
        finalidade = request.form.get('finalidade', 'Não informada')

        if not item_id or quantidade <= 0:
            flash('Selecione um item válido e informe uma quantidade maior que zero.', 'danger')
            return redirect(url_for('entradasaida'))

        if db_type == 'mysql':
            cursor.execute("SELECT id, nome, qntd FROM estoque WHERE id = %s", (item_id,))
            item = cursor.fetchone()
        else:
            cursor.execute("SELECT id, nome, qntd FROM estoque WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            item = tuple(row) if row else None

        if not item:
            flash('Item não encontrado!', 'danger')
            conn.close()
            return redirect(url_for('entradasaida'))

        item_nome = item[1]
        qntd_atual = item[2]

        if tipo == 'Saída' and quantidade > qntd_atual:
            flash(f'Estoque insuficiente! Quantidade disponível: {qntd_atual}', 'warning')
            conn.close()
            return redirect(url_for('entradasaida'))

        nova_qntd = (qntd_atual + quantidade) if tipo == 'Entrada' else (qntd_atual - quantidade)

        if db_type == 'mysql':
            cursor.execute("UPDATE estoque SET qntd = %s WHERE id = %s", (nova_qntd, item_id))
            cursor.execute("""
                INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (session['usuario'], item_nome, tipo, quantidade, finalidade))
        else:
            cursor.execute("UPDATE estoque SET qntd = ? WHERE id = ?", (nova_qntd, item_id))
            cursor.execute("""
                INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (session['usuario'], item_nome, tipo, quantidade, finalidade))

        conn.commit()
        flash(f'Movimentação de {tipo} para "{item_nome}" ({quantidade} un.) registrada!', 'success')
        conn.close()
        return redirect(url_for('entradasaida'))

    if db_type == 'mysql':
        cursor.execute("SELECT id, nome, qntd FROM estoque ORDER BY nome ASC")
        itens = cursor.fetchall()
        cursor.execute("SELECT id, usuario, item_nome, tipo, quantidade, finalidade, data_hora FROM historico ORDER BY data_hora DESC LIMIT 10")
        historico_recent = cursor.fetchall()
    else:
        cursor.execute("SELECT id, nome, qntd FROM estoque ORDER BY nome ASC")
        itens = [tuple(r) for r in cursor.fetchall()]
        cursor.execute("SELECT id, usuario, item_nome, tipo, quantidade, finalidade, data_hora FROM historico ORDER BY data_hora DESC LIMIT 10")
        historico_recent = [tuple(r) for r in cursor.fetchall()]

    conn.close()
    return render_template("entrada-saida.html", itens=itens, historico=historico_recent)

# ==========================================
# NOVA PÁGINA: HISTÓRICO DE MOVIMENTAÇÃO
# ==========================================
@app.route("/historico")
@app.route("/historico.html")
@login_required
def historico():
    conn, db_type = get_db()
    cursor = conn.cursor()

    if db_type == 'mysql':
        cursor.execute("SELECT id, usuario, item_nome, tipo, quantidade, finalidade, data_hora FROM historico ORDER BY id DESC")
        registros = cursor.fetchall()
    else:
        cursor.execute("SELECT id, usuario, item_nome, tipo, quantidade, finalidade, data_hora FROM historico ORDER BY id DESC")
        registros = [tuple(r) for r in cursor.fetchall()]

    conn.close()
    return render_template("historico.html", historico=registros)

# ==========================================
# NOVA PÁGINA: GERENCIAR ESTOQUE (3 FUNÇÕES)
# 1 - Zerar Estoque
# 2 - Importar CSV
# 3 - Exportar CSV
# ==========================================
@app.route("/gerenciar-estoque")
@app.route("/gerenciar-estoque.html")
@admin_required
def gerenciar_estoque():
    return render_template("gerenciar-estoque.html")

@app.route("/zerar-estoque", methods=['POST'])
@admin_required
def zerar_estoque():
    conn, db_type = get_db()
    cursor = conn.cursor()

    # ZERA O BANCO TODO DE ESTOQUE (USUÁRIOS NÃO ZERAR)
    cursor.execute("DELETE FROM estoque")
    
    # Registra no histórico a ação de zerar estoque
    if db_type == 'mysql':
        cursor.execute("""
            INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
            VALUES (%s, 'TODOS OS ITENS', 'Saída', 0, 'BANCO DE ESTOQUE ZERADO PELO ADMINISTRADOR', NOW())
        """)
    else:
        cursor.execute("""
            INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
            VALUES (?, 'TODOS OS ITENS', 'Saída', 0, 'BANCO DE ESTOQUE ZERADO PELO ADMINISTRADOR', datetime('now'))
        """, (session['usuario'],))

    conn.commit()
    conn.close()
    flash('Todo o banco de dados de estoque foi zerado com sucesso! (Usuários mantidos).', 'success')
    return redirect(url_for('gerenciar_estoque'))

@app.route("/exportar-csv", methods=['GET'])
@admin_required
def exportar_csv():
    conn, db_type = get_db()
    cursor = conn.cursor()

    if db_type == 'mysql':
        cursor.execute("SELECT nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY id ASC")
        itens = cursor.fetchall()
    else:
        cursor.execute("SELECT nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY id ASC")
        itens = [tuple(r) for r in cursor.fetchall()]

    conn.close()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['nome', 'qntd', 'estoque_minimo', 'descricao', 'preco', 'foto', 'categoria'])

    for row in itens:
        writer.writerow(row)

    csv_data = output.getvalue().encode('utf-8-sig')

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=estoque_almoxarifado.csv"}
    )

@app.route("/importar-csv", methods=['POST'])
@admin_required
def importar_csv():
    if 'arquivo_csv' not in request.files:
        flash('Nenhum arquivo enviado.', 'danger')
        return redirect(url_for('gerenciar_estoque'))

    file = request.files['arquivo_csv']
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'warning')
        return redirect(url_for('gerenciar_estoque'))

    if not file.filename.endswith('.csv'):
        flash('Por favor, selecione um arquivo com extensão .csv', 'warning')
        return redirect(url_for('gerenciar_estoque'))

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        # Suporta delimitador vírgula ou ponto e vírgula
        sample = stream.read(1024)
        stream.seek(0)
        delimiter = ';' if ';' in sample else ','
        csv_reader = csv.DictReader(stream, delimiter=delimiter)

        conn, db_type = get_db()
        cursor = conn.cursor()
        contador = 0

        for row in csv_reader:
            nome = row.get('nome') or row.get('Nome')
            if not nome:
                continue

            qntd = int(row.get('qntd') or row.get('Quantidade') or 0)
            estoque_minimo = int(row.get('estoque_minimo') or row.get('Estoque Minimo') or 0)
            descricao = row.get('descricao') or row.get('Descricao') or ''
            preco = float(row.get('preco') or row.get('Preco') or 0.0)
            foto = row.get('foto') or row.get('Foto') or 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500'
            categoria = row.get('categoria') or row.get('Categoria') or 'Geral'

            if db_type == 'mysql':
                cursor.execute("""
                    INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (nome, qntd, estoque_minimo, descricao, preco, foto, categoria))
            else:
                cursor.execute("""
                    INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (nome, qntd, estoque_minimo, descricao, preco, foto, categoria))
            contador += 1

        # Registrar no histórico
        if contador > 0:
            if db_type == 'mysql':
                cursor.execute("""
                    INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
                    VALUES (%s, 'IMPORTAÇÃO CSV', 'Entrada', %s, 'Importação de base de dados via arquivo CSV', NOW())
                """, (session['usuario'], contador))
            else:
                cursor.execute("""
                    INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
                    VALUES (?, 'IMPORTAÇÃO CSV', 'Entrada', ?, 'Importação de base de dados via arquivo CSV', datetime('now'))
                """, (session['usuario'], contador))

        conn.commit()
        conn.close()
        flash(f'Importação concluída! {contador} itens importados para o estoque.', 'success')

    except Exception as e:
        flash(f'Erro ao processar o arquivo CSV: {str(e)}', 'danger')

    return redirect(url_for('gerenciar_estoque'))

# ==========================================
# CADASTRO DE USUÁRIOS (ADMIN)
# ==========================================
@app.route("/criar-conta", methods=['GET', 'POST'])
@app.route("/criar-conta.html", methods=['GET', 'POST'])
@app.route("/cadastrar", methods=['POST'])
@admin_required
def criarconta():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        funcao = request.form.get('funcao', 'user')

        if not usuario or not senha:
            flash('Preencha todos os campos do formulário.', 'warning')
            return redirect(url_for('criarconta'))

        senha_hash = generate_password_hash(senha)

        conn, db_type = get_db()
        cursor = conn.cursor()

        try:
            if db_type == 'mysql':
                cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES (%s, %s, %s)", (usuario, senha_hash, funcao))
            else:
                cursor.execute("INSERT INTO usuarios (usuario, senha, funcao) VALUES (?, ?, ?)", (usuario, senha_hash, funcao))
            conn.commit()
            flash(f'Novo usuário "{usuario}" ({funcao}) cadastrado com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao criar usuário: Nome de usuário já existe.', 'danger')
        finally:
            conn.close()

        return redirect(url_for('criarconta'))

    return render_template("criar-conta.html")

@app.route("/administrador.html")
@admin_required
def administrador():
    return redirect(url_for('criarconta'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
