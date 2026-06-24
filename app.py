from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)

@app.route("/")
def login():
    return render_template ("login.html")

@app.route("/login.html")
def loginhtml():
    return render_template ("login.html")

@app.route("/home.html", methods=['POST', 'GET'])
def home():
    
    senha_digitada = request.form.get('senha')

    conexao = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        port=3306,
        database='almoxarifado'
    )

    cursor = conexao.cursor()
    cursor.execute("SELECT senha FROM usuarios WHERE usuario = 'admin'")
    resultado = cursor.fetchone()
    
    print(resultado[0])

    if senha_digitada == resultado[0]:
        return render_template ("home.html")
    
    return "Credenciais invalidas"

@app.route("/entrada-saida.html")
def entradasaida():
    return render_template ("entrada-saida.html")

@app.route("/novos-itens.html")
def novositens():
    return render_template ("novos-itens.html")

@app.route("/administrador.html")
def administrador():
    return render_template ("/administrador.html")

@app.route("/criar-conta.html")
def criarconta():
    return render_template("criar-conta.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

