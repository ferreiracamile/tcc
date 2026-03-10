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

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)