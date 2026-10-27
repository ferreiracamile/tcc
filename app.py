import os
import io
import csv
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
import mysql.connector
import bcrypt

# ========================================================
# CONFIGURAÇÃO DA APLICAÇÃO FLASK
# ========================================================
app = Flask(__name__)
app.secret_key = 'senai_almoxarifado_secret_key_tcc'

# ========================================================
# SUPORTE A CORS (PERMITIR ACESSO DO EXPO GO / REACT NATIVE)
# ========================================================
@app.before_request
def tratar_preflight():
    """Responde a requisições OPTIONS (pre-flight) vindas do Expo Go ou navegadores."""
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

@app.after_request
def adicionar_headers_cors(response):
    """Adiciona cabeçalhos CORS em todas as respostas da API."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# ========================================================
# CONEXÃO COM O BANCO DE DADOS (MySQL)
# ========================================================
# As variáveis abaixo utilizam os valores padrão para rodar localmente,
# mas também podem receber configurações via variáveis de ambiente (Docker).
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "almoxarifado")
DB_PORT = int(os.getenv("DB_PORT", 3306))

def get_db():
    """Cria e retorna uma conexão com o banco de dados MySQL."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        auth_plugin='mysql_native_password'
    )

# ========================================================
# FUNÇÕES DE CRIPTOGRAFIA E AUTENTICAÇÃO (BCRYPT)
# ========================================================
def verificar_senha(senha_digitada, hash_armazenado):
    """
    Verifica se a senha em texto puro digitada pelo usuário corresponde
    ao hash seguro salvo no banco de dados usando a biblioteca bcrypt.
    """
    try:
        # Garante que a senha digitada seja bytes
        if isinstance(senha_digitada, str):
            senha_bytes = senha_digitada.encode('utf-8')
        else:
            senha_bytes = senha_digitada

        # Garante que o hash armazenado seja bytes (se vier str, converte)
        if isinstance(hash_armazenado, str):
            hash_bytes = hash_armazenado.encode('utf-8')
        elif isinstance(hash_armazenado, (bytes, bytearray)):
            hash_bytes = bytes(hash_armazenado)
        else:
            hash_bytes = str(hash_armazenado).encode('utf-8')

        return bcrypt.checkpw(senha_bytes, hash_bytes)
    except Exception as e:
        # Se der erro, imprime no terminal para você debugar o que aconteceu
        print(f"Erro interno na validação do Bcrypt: {e}")
        return False

def gerar_hash_senha(senha):
        senha_bytes = senha.encode('utf-8')
        salt = bcrypt.gensalt(12)  # Força o custo 12 que você usa no sistema
        hash_seguro = bcrypt.hashpw(senha_bytes, salt)
        return hash_seguro.decode('utf-8')
    
# ========================================================
# CONTROLE DE ACESSO (DECORADORES PARA APLICAÇÃO WEB)
# ========================================================
def login_required(f):
    """Exige que o usuário esteja logado na sessão web para acessar a rota."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Por favor, faça login para acessar o sistema.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Exige que o usuário esteja logado E possua função de 'admin'."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        if session.get('funcao') != 'admin':
            flash('Acesso negado. Esta página requer privilégios de Administrador.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ========================================================
# ROTAS DA APLICAÇÃO WEB (SESSÃO E TEMPLATES HTML)
# ========================================================


@app.route("/", methods=["GET", "POST"])
@app.route("/login.html", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    """Autenticação web com verificação bcrypt e tratamento de erros."""

    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").strip()
        senha = request.form.get("senha") or ""

        if not usuario or not senha:
            return render_template(
                "login.html",
                erro="Informe o usuário e a senha."
            )

        conn = None
        cursor = None

        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT usuario, senha, funcao
                FROM usuarios
                WHERE usuario = %s
                LIMIT 1
                """,
                (usuario,)
            )

            user = cursor.fetchone()

        except mysql.connector.Error as err:
            # AJUSTE AQUI: Captura o erro real e exibe no terminal do VS Code / Prompt
            print("\n" + "="*50)
            print(f"ERRO DE CONEXÃO COM O MYSQL: {err}")
            print(f"Tentando conectar em: {DB_HOST}:{DB_PORT} com o usuário '{DB_USER}'")
            print("="*50 + "\n")

            app.logger.exception(
                "Erro ao consultar o usuário no banco de dados."
            )

            # Também mostra o erro técnico temporariamente na tela do navegador
            return render_template(
                "login.html",
                erro=f"Erro de Banco de Dados: {err}"
            ), 500

        finally:
            if cursor is not None:
                cursor.close()

            if conn is not None and conn.is_connected():
                conn.close()

        if user is None:
            flash("Usuário ou senha inválidos!", "danger")
            return render_template(
                "login.html",
                erro="Credenciais inválidas"
            )

        db_usuario, db_hash, db_funcao = user

        # Aceita hashes retornados pelo MySQL como str ou bytes.
        try:
            if isinstance(db_hash, str):
                hash_bytes = db_hash.encode("utf-8")
            else:
                hash_bytes = bytes(db_hash)

            senha_valida = bcrypt.checkpw(
                senha.encode("utf-8"),
                hash_bytes
            )

        except (ValueError, TypeError, AttributeError):
            app.logger.warning(
                "Hash bcrypt inválido para o usuário %s.",
                db_usuario
            )
            senha_valida = False

        if not senha_valida:
            flash("Usuário ou senha inválidos!", "danger")
            return render_template(
                "login.html",
                erro="Credenciais inválidas"
            )

        # Login válido: salva os dados na sessão.
        session.clear()
        session["usuario"] = db_usuario
        session["funcao"] = db_funcao

        flash(f"Bem-vindo, {db_usuario}!", "success")
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Encerra a sessão do usuário conectado."""
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

@app.route("/home.html")
@app.route("/home")
@login_required
def home():
    """Página inicial com painel de métricas e lista de itens em estoque."""
    conn = get_db()
    cursor = conn.cursor()

    # Consulta todos os produtos cadastrados
    cursor.execute("SELECT id, nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY nome ASC")
    itens = cursor.fetchall()

    # Total de entradas no dia de hoje
    cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM historico WHERE tipo = 'Entrada' AND DATE(data_hora) = CURDATE()")
    entradas_hoje = cursor.fetchone()[0]

    # Total de saídas no dia de hoje
    cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM historico WHERE tipo = 'Saída' AND DATE(data_hora) = CURDATE()")
    saidas_hoje = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    total_itens = sum(item[2] for item in itens) if itens else 0

    return render_template(
        "home.html",
        itens=itens,
        total_itens=total_itens,
        entradas_hoje=entradas_hoje,
        saidas_hoje=saidas_hoje
    )

@app.route("/novos-itens.html", methods=['GET', 'POST'])
@app.route("/novos-itens", methods=['GET', 'POST'])
@login_required
def novositens():
    """Cadastro e listagem de novos itens no estoque."""
    conn = get_db()
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

        cursor.execute("""
            INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nome, qntd, estoque_minimo, descricao, preco, foto, categoria))

        cursor.execute("""
            INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (session['usuario'], nome, 'Entrada', qntd, 'Cadastro inicial de novo item'))

        conn.commit()
        cursor.close()
        conn.close()

        flash(f'Item "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('novositens'))

    cursor.execute("SELECT id, nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY id DESC")
    itens = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("novos-itens.html", itens=itens)

@app.route("/entrada-saida.html", methods=['GET', 'POST'])
@app.route("/entrada-saida", methods=['GET', 'POST'])
@login_required
def entradasaida():
    """Registro de entradas e saídas de produtos no almoxarifado."""
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        tipo = request.form.get('tipo')  # 'Entrada' ou 'Saída'
        item_id = request.form.get('item_id')
        quantidade = int(request.form.get('quantidade', 0))
        finalidade = request.form.get('finalidade', 'Não informada')

        if not item_id or quantidade <= 0:
            flash('Selecione um item válido e informe uma quantidade maior que zero.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('entradasaida'))

        cursor.execute("SELECT id, nome, qntd FROM estoque WHERE id = %s", (item_id,))
        item = cursor.fetchone()

        if not item:
            flash('Item não encontrado!', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('entradasaida'))

        item_nome = item[1]
        qntd_atual = item[2]

        if tipo == 'Saída' and quantidade > qntd_atual:
            flash(f'Estoque insuficiente! Quantidade disponível: {qntd_atual}', 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('entradasaida'))

        nova_qntd = (qntd_atual + quantidade) if tipo == 'Entrada' else (qntd_atual - quantidade)

        cursor.execute("UPDATE estoque SET qntd = %s WHERE id = %s", (nova_qntd, item_id))
        cursor.execute("""
            INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (session['usuario'], item_nome, tipo, quantidade, finalidade))

        conn.commit()
        cursor.close()
        conn.close()

        flash(f'Movimentação de {tipo} para "{item_nome}" ({quantidade} un.) registrada!', 'success')
        return redirect(url_for('entradasaida'))

    cursor.execute("SELECT id, nome, qntd FROM estoque ORDER BY nome ASC")
    itens = cursor.fetchall()

    cursor.execute("""
        SELECT id, usuario, item_nome, tipo, quantidade, finalidade, data_hora 
        FROM historico 
        ORDER BY data_hora DESC 
        LIMIT 10
    """)
    historico_recent = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("entrada-saida.html", itens=itens, historico=historico_recent)

@app.route("/historico.html")
@app.route("/historico")
@login_required
def historico():
    """Tela de histórico completo de todas as movimentações."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, usuario, item_nome, tipo, quantidade, finalidade, data_hora 
        FROM historico 
        ORDER BY id DESC 
        LIMIT 100
    """)
    registros = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("historico.html", historico=registros)

@app.route("/gerenciar-estoque.html")
@app.route("/gerenciar-estoque")
@admin_required
def gerenciar_estoque():
    """Painel de gerenciamento avançado do estoque (Zerar e CSV)."""
    return render_template("gerenciar-estoque.html")

@app.route("/zerar-estoque", methods=['GET', 'POST'])
@admin_required
def zerar_estoque():
    """Remove todos os produtos do estoque e registra a ação no histórico."""
    conn = get_db()
    cursor = conn.cursor()

    # Zera a tabela de estoque (mantém usuários)
    cursor.execute("DELETE FROM estoque")

    usuario_atual = session.get('usuario', 'admin')

    # Registra no histórico
    cursor.execute("""
        INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
        VALUES (%s, 'TODOS OS ITENS', 'Saída', 0, 'BANCO DE ESTOQUE ZERADO PELO ADMINISTRADOR', NOW())
    """, (usuario_atual,))

    conn.commit()
    cursor.close()
    conn.close()

    flash('Todo o estoque foi zerado com sucesso! (Usuários mantidos).', 'success')
    return redirect(url_for('gerenciar_estoque'))

@app.route("/exportar-csv", methods=['GET'])
@admin_required
def exportar_csv():
    """Gera e baixa um arquivo CSV com todos os itens do estoque."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY id ASC")
    itens = cursor.fetchall()

    cursor.close()
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
    """Importa uma lista de produtos a partir de um arquivo CSV."""
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
        sample = stream.read(1024)
        stream.seek(0)
        delimiter = ';' if ';' in sample else ','
        csv_reader = csv.DictReader(stream, delimiter=delimiter)

        conn = get_db()
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

            cursor.execute("""
                INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nome, qntd, estoque_minimo, descricao, preco, foto, categoria))
            contador += 1

        if contador > 0:
            cursor.execute("""
                INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
                VALUES (%s, 'IMPORTAÇÃO CSV', 'Entrada', %s, 'Importação de base de dados via arquivo CSV', NOW())
            """, (session['usuario'], contador))

        conn.commit()
        cursor.close()
        conn.close()

        flash(f'Importação concluída! {contador} itens importados para o estoque.', 'success')

    except Exception as e:
        flash(f'Erro ao processar o arquivo CSV: {str(e)}', 'danger')

    return redirect(url_for('gerenciar_estoque'))

@app.route("/cadastrar", methods=['GET', 'POST'])
@app.route("/criar-conta.html", methods=['GET', 'POST'])
@app.route("/criar-conta", methods=['GET', 'POST'])
@admin_required
def criarconta():
    """Cadastro de novas contas de usuário com senha criptografada via bcrypt."""
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        funcao = request.form.get('funcao', 'user')

        if not usuario or not senha:
            flash('Preencha todos os campos do formulário.', 'warning')
            return redirect(url_for('criarconta'))

        senha_hash = gerar_hash_senha(senha)

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO usuarios (usuario, senha, funcao) 
                VALUES (%s, %s, %s)
            """, (usuario, senha_hash, funcao))
            conn.commit()
            flash(f'Novo usuário "{usuario}" ({funcao}) cadastrado com sucesso!', 'success')
        except Exception:
            flash('Erro ao criar usuário: Nome de usuário já cadastrado no sistema.', 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('criarconta'))

    return render_template("criar-conta.html")

@app.route("/administrador.html")
@admin_required
def administrador():
    """Atalho para a tela de cadastro de usuários."""
    return redirect(url_for('criarconta'))

# ========================================================
# ROTAS EXTERNAS / API REST (PARA EXPO GO / REACT NATIVE)
# ========================================================

@app.route("/api/login", methods=['POST'])
def api_login():
    """
    Autenticação para o aplicativo Expo Go.
    Recebe JSON: { "usuario": "admin", "senha": "123" }
    Retorna: { "success": true, "usuario": "admin", "funcao": "admin" }
    """
    dados = request.get_json(silent=True) or request.form.to_dict() or {}
    usuario = dados.get('usuario')
    senha = dados.get('senha')

    if not usuario or not senha:
        return jsonify({"success": False, "message": "Usuário e senha são obrigatórios"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, senha, funcao FROM usuarios WHERE usuario = %s", (usuario,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and verificar_senha(senha, user[1]):
        return jsonify({
            "success": True,
            "usuario": user[0],
            "funcao": user[2],
            "message": f"Bem-vindo, {user[0]}!"
        }), 200

    return jsonify({"success": False, "message": "Usuário ou senha inválidos"}), 401

@app.route("/api/resumo", methods=['GET'])
def api_resumo():
    """
    Métricas gerais para o painel inicial do aplicativo Expo Go.
    Retorna: { "total_itens": 0, "entradas_hoje": 0, "saidas_hoje": 0 }
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(qntd), 0) FROM estoque")
    total_itens = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM historico WHERE tipo = 'Entrada' AND DATE(data_hora) = CURDATE()")
    entradas_hoje = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM historico WHERE tipo = 'Saída' AND DATE(data_hora) = CURDATE()")
    saidas_hoje = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify({
        "total_itens": int(total_itens),
        "entradas_hoje": int(entradas_hoje),
        "saidas_hoje": int(saidas_hoje)
    }), 200

@app.route("/api/estoque", methods=['GET', 'POST'])
def api_estoque():
    """
    GET: Lista todos os itens do estoque em formato JSON.
    POST: Cadastra um novo produto vindo do aplicativo Expo Go.
    """
    if request.method == 'POST':
        dados = request.get_json(silent=True) or request.form.to_dict() or {}
        nome = dados.get('nome')
        qntd = int(dados.get('qntd', 0))
        estoque_minimo = int(dados.get('estoque_minimo', 0))
        descricao = dados.get('descricao', '')
        preco = float(dados.get('preco', 0.0))
        foto = dados.get('foto') or 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500'
        categoria = dados.get('categoria', 'Geral')
        usuario = dados.get('usuario', 'App Expo')

        if not nome:
            return jsonify({"success": False, "message": "O nome do item é obrigatório"}), 400

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO estoque (nome, qntd, estoque_minimo, descricao, preco, foto, categoria)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nome, qntd, estoque_minimo, descricao, preco, foto, categoria))

        cursor.execute("""
            INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
            VALUES (%s, %s, 'Entrada', %s, 'Cadastro via App Expo', NOW())
        """, (usuario, nome, qntd))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": f'Item "{nome}" cadastrado com sucesso!'}), 201

    # Método GET: Listar estoque
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, qntd, estoque_minimo, descricao, preco, foto, categoria FROM estoque ORDER BY nome ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    itens = []
    for r in rows:
        itens.append({
            "id": r[0],
            "nome": r[1],
            "qntd": r[2],
            "estoque_minimo": r[3],
            "descricao": r[4] or "",
            "preco": float(r[5]) if r[5] is not None else 0.0,
            "foto": r[6] or "",
            "categoria": r[7] or "Geral"
        })

    return jsonify(itens), 200

@app.route("/api/entrada-saida", methods=['POST'])
def api_entrada_saida():
    """
    Registra uma movimentação de entrada ou saída no aplicativo Expo Go.
    Recebe JSON: { "tipo": "Entrada"|"Saída", "item_id": 1, "quantidade": 5, "finalidade": "...", "usuario": "admin" }
    """
    dados = request.get_json(silent=True) or request.form.to_dict() or {}
    tipo = dados.get('tipo')
    item_id = dados.get('item_id')
    quantidade = int(dados.get('quantidade', 0))
    finalidade = dados.get('finalidade', 'Não informada')
    usuario = dados.get('usuario', 'App Expo')

    if not item_id or quantidade <= 0 or tipo not in ['Entrada', 'Saída']:
        return jsonify({"success": False, "message": "Informe tipo (Entrada/Saída), item_id e quantidade válida"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, qntd FROM estoque WHERE id = %s", (item_id,))
    item = cursor.fetchone()

    if not item:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Item não encontrado no estoque"}), 404

    item_nome = item[1]
    qntd_atual = item[2]

    if tipo == 'Saída' and quantidade > qntd_atual:
        cursor.close()
        conn.close()
        return jsonify({
            "success": False, 
            "message": f"Estoque insuficiente! Quantidade disponível: {qntd_atual}"
        }), 400

    nova_qntd = (qntd_atual + quantidade) if tipo == 'Entrada' else (qntd_atual - quantidade)

    cursor.execute("UPDATE estoque SET qntd = %s WHERE id = %s", (nova_qntd, item_id))
    cursor.execute("""
        INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (usuario, item_nome, tipo, quantidade, finalidade))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Movimentação de {tipo} registrada para {item_nome}!",
        "nova_quantidade": nova_qntd
    }), 200

@app.route("/api/historico", methods=['GET'])
def api_historico():
    """
    Retorna a lista das últimas movimentações em formato JSON para o Expo Go.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, usuario, item_nome, tipo, quantidade, finalidade, data_hora 
        FROM historico 
        ORDER BY id DESC 
        LIMIT 50
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    registros = []
    for r in rows:
        registros.append({
            "id": r[0],
            "usuario": r[1],
            "item_nome": r[2],
            "tipo": r[3],
            "quantidade": r[4],
            "finalidade": r[5] or "",
            "data_hora": str(r[6])
        })

    return jsonify(registros), 200

@app.route("/api/zerar-estoque", methods=['POST'])
def api_zerar_estoque():
    """
    Permite zerar o estoque via API JSON.
    """
    dados = request.get_json(silent=True) or request.form.to_dict() or {}
    usuario = dados.get('usuario', 'App Expo')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM estoque")
    cursor.execute("""
        INSERT INTO historico (usuario, item_nome, tipo, quantidade, finalidade, data_hora)
        VALUES (%s, 'TODOS OS ITENS', 'Saída', 0, 'ESTOQUE ZERADO VIA APP EXPO', NOW())
    """, (usuario,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True, "message": "Todo o estoque foi zerado com sucesso!"}), 200

# ========================================================
# INICIALIZAÇÃO DO SERVIDOR LOCAL
# ========================================================
if __name__ == "__main__":
    # Rodar localmente na porta 5000 acessível na rede local (host 0.0.0.0)
    app.run(host='0.0.0.0', port=5000, debug=True)
