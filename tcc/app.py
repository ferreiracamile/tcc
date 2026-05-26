from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def login():
    return render_template ("login.html")

@app.route("/login.html")
def loginhtml():
    return render_template ("login.html")

@app.route("/home.html")
def home():
    return render_template ("home.html")
@app.route("/entrada-saida.html")
def entradasaida():
    return render_template ("entrada-saida.html")

@app.route("/novos-itens.html")
def novositens():
    return render_template ("novos-itens.html")

@app.route("/administrador.html")
def administrador():
    return render_template ("/administrador.html")

if __name__ == "__main__":
app.run(host='0.0.0.0', debug=True)

from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

# Chave de segurança da sessão
app.secret_key = "senha_super_secreta"

# =========================================
# BANCO TEMPORÁRIO (depois você troca por BD)
# =========================================

usuarios = {
    "admin": {
        "senha": "123",
        "adm": True
    },
    "user": {
        "senha": "123",
        "adm": False
    }
}

# =========================================
# LOGIN
# =========================================

@app.route("/")
def login():
    return render_template("login.html")

# =========================================
# VALIDAR LOGIN
# =========================================

@app.route("/logar", methods=["POST"])
def logar():

    usuario = request.form.get("usuario")
    senha = request.form.get("senha")
    adm = request.form.get("adm")

    # verifica se usuário existe
    if usuario in usuarios:

        # verifica senha
        if usuarios[usuario]["senha"] == senha:

            # salva sessão
            session["usuario"] = usuario
            session["adm"] = usuarios[usuario]["adm"]

            # se for ADM
            if usuarios[usuario]["adm"]:
                return redirect(url_for("administrador"))

            # usuário normal
            return redirect(url_for("home"))

    return "Usuário ou senha inválidos"


# =========================================
# HOME
# =========================================

@app.route("/home.html")
def home():

    # verifica login
    if "usuario" not in session:
        return redirect(url_for("login"))

    return render_template("home.html")


# =========================================
# ADMIN
# =========================================

@app.route("/administrador.html")
def administrador():

    # verifica login
    if "usuario" not in session:
        return redirect(url_for("login"))

    # verifica ADM
    if not session.get("adm"):
        return "Acesso negado"

    return render_template("administrador.html")


# =========================================
# ENTRADA E SAÍDA
# =========================================

@app.route("/entrada-saida.html")
def entradasaida():

    if "usuario" not in session:
        return redirect(url_for("login"))

    return render_template("entrada-saida.html")


# =========================================
# NOVOS ITENS
# =========================================

@app.route("/novos-itens.html")
def novositens():

    if "usuario" not in session:
        return redirect(url_for("login"))

    return render_template("novos-itens.html")


# =========================================
# CRIAR CONTA
# =========================================

@app.route("/criar-conta.html")
def criarconta():
    return render_template("criar-conta.html")


# =========================================
# SALVAR NOVA CONTA
# =========================================

@app.route("/cadastrar", methods=["POST"])
def cadastrar():

    usuario = request.form.get("usuario")
    senha = request.form.get("senha")
    email = request.form.get("email")

    # cria usuário
    usuarios[usuario] = {
        "senha": senha,
        "adm": False
    }

    return redirect(url_for("login"))


# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================
# INICIAR APP
# =========================================

if __name__ == "__main__":
    app.run(debug=True)
