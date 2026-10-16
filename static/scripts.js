// SweetAlert 2 Helpers e Manipulação de Fotos / Modais

function verFoto(nome, fotoUrl, descricao, categoria, qntd, preco, estoqueMinimo) {
    let statusEstoque = qntd <= estoqueMinimo 
        ? '<span style="color: #DC3545; font-weight: bold;">⚠️ Atenção: Estoque Baixo!</span>' 
        : '<span style="color: #28A745; font-weight: bold;">✅ Estoque OK</span>';

    Swal.fire({
        title: `<strong>${nome}</strong>`,
        html: `
            <div style="text-align: center; margin-bottom: 15px;">
                <img src="${fotoUrl}" alt="${nome}" style="max-width: 100%; max-height: 220px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); object-fit: cover;">
            </div>
            <div style="text-align: left; background: #F8FAFC; padding: 15px; border-radius: 8px; border: 1px solid #E2E8F0; font-size: 0.95rem; line-height: 1.6;">
                <p><strong>Categoria:</strong> ${categoria}</p>
                <p><strong>Descrição:</strong> ${descricao || 'Sem descrição cadastrada.'}</p>
                <p><strong>Quantidade em Estoque:</strong> ${qntd} un. (${statusEstoque})</p>
                <p><strong>Estoque Mínimo:</strong> ${estoqueMinimo} un.</p>
                <p><strong>Preço Estimado:</strong> R$ ${parseFloat(preco).toFixed(2)}</p>
            </div>
        `,
        showCloseButton: true,
        confirmButtonText: 'Fechar',
        confirmButtonColor: '#0054A6'
    });
}

function confirmarZerarEstoque() {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Tem certeza absoluta?',
            text: "Essa ação irá APAGAR TODOS os itens do estoque! A lista de usuários NÃO será afetada.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#DC3545',
            cancelButtonColor: '#6C757D',
            confirmButtonText: 'Sim, ZERAR ESTOQUE!',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                document.getElementById('form-zerar-estoque').submit();
            }
        });
    } else {
        if (confirm("Tem certeza absoluta? Essa ação irá APAGAR TODOS os itens do estoque!")) {
            document.getElementById('form-zerar-estoque').submit();
        }
    }
}

function confirmarImportacaoCSV() {
    let input = document.getElementById('arquivo_csv');
    if (!input || !input.files || input.files.length === 0) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: 'Nenhum Arquivo!',
                text: 'Por favor, selecione um arquivo .CSV antes de importar.',
                icon: 'warning',
                confirmButtonColor: '#0054A6'
            });
        } else {
            alert('Por favor, selecione um arquivo .CSV antes de importar.');
        }
        return false;
    }
    return true;
}

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
