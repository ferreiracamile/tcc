function teste(){
    let item = document.getElementById("nomeitem").value
    let qtde = document.getElementById("qtde").value
    let conteudoanterior = document.getElementById("tabeladeitens").innerHTML
    document.getElementById("tabeladeitens").innerHTML= conteudoanterior + '<br>' + item + ' ' + qtde
    Swal.fire({
    title: "CADASTRADO",
    icon: "success",
    draggable: true
});
}

function teste2(){
    let conteudoanterior = document.getElementById("historico-lista").innerHTML
    let item = document.getElementById("nomeitem").value
    let tipo = document.getElementById("tipo").value
    let qtde = document.getElementById("qtde").value
    document.getElementById("historico-lista").innerHTML= conteudoanterior + '<br>' + item + ' ' + qtde + ' ' + tipo
    Swal.fire({
    title: "REGISTRADO",
    icon: "success",
    draggable: true
});
}

function alerta(){
    Swal.fire({
  title: "REGISTRADO",
  icon: "success",
  draggable: true
});
}

function entrar(){
  window.location.href = "home.html";
}

function criarConta(){
  if(document.getElementById("adm").checked){
    window.location.href = "administrador.html";
  }
}

function entrarHome(){
    window.location.href = "home.html";
}

function criarConta() {
    window.location = "criar-conta.html";
}

function cadastrarItem() {

    var nome = document.getElementById("nome-item").value;

    if(nome == "") {
        alert("Digite o nome do item");
        return;
    }

    alert("Item cadastrado!");
}

function entradaItem() {
    alert("Entrada registrada!");
}

function saidaItem() {
    alert("Saída registrada!");
}

function criarUsuario() {
    alert("Usuário criado!");
}

function logout() {
    window.location = "login.html";
}
