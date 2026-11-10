import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, FlatList, Alert } from 'react-native';

// IP DO SEU COMPUTADOR ONDE O FLASK ESTÁ RODANDO
const IP = '10.154.20.130';

export default function App() {
  // Controle de Login
  const [usuarioLogado, setUsuarioLogado] = useState(null);
  const [usuario, setUsuario] = useState('');
  const [senha, setSenha] = useState('');

  // Controle de Estoque
  const [lista, setLista] = useState([]);
  const [nome, setNome] = useState('');
  const [qntd, setQntd] = useState('');

  // 1. FAZER LOGIN NO FLASK
  const fazerLogin = () => {
    if (!usuario || !senha) {
      Alert.alert('Aviso', 'Preencha usuário e senha!');
      return;
    }

    fetch(`http://${IP}:5000/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        usuario: usuario,
        senha: senha,
      }),
    })
      .then((res) => res.json())
      .then((dados) => {
        if (dados.success) {
          setUsuarioLogado(dados.usuario);
          setSenha(''); // Limpa a senha
          buscarItens(); // Carrega os produtos do banco
        } else {
          Alert.alert('Erro', dados.message || 'Usuário ou senha incorretos!');
        }
      })
      .catch(() => Alert.alert('Erro', 'Não conectou ao Flask. Ele está rodando?'));
  };

  // 2. FAZER LOGOUT (SAIR)
  const sair = () => {
    setUsuarioLogado(null);
    setLista([]);
  };

  // 3. CARREGAR ITENS DO BANCO
  const buscarItens = () => {
    fetch(`http://${IP}:5000/api/estoque`)
      .then((res) => res.json())
      .then((dados) => setLista(dados))
      .catch(() => Alert.alert('Erro', 'Falha ao buscar estoque.'));
  };

  // 4. CADASTRAR NOVO ITEM
  const cadastrar = () => {
    if (!nome) {
      Alert.alert('Aviso', 'Digite o nome da ferramenta!');
      return;
    }

    fetch(`http://${IP}:5000/api/estoque`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nome: nome,
        qntd: parseInt(qntd) || 0,
        usuario: usuarioLogado,
      }),
    })
      .then((res) => res.json())
      .then(() => {
        Alert.alert('Sucesso', 'Item cadastrado!');
        setNome('');
        setQntd('');
        buscarItens();
      })
      .catch(() => Alert.alert('Erro', 'Falha ao salvar no banco.'));
  };

  // 5. ENTRADA OU SAÍDA (+1 ou -1)
  const movimentar = (id, tipo, quantidadeAtual) => {
    if (tipo === 'Saída' && quantidadeAtual <= 0) {
      Alert.alert('Aviso', 'Estoque já está zerado!');
      return;
    }

    fetch(`http://${IP}:5000/api/entrada-saida`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tipo: tipo,
        item_id: id,
        quantidade: 1,
        finalidade: 'Ajuste pelo celular',
        usuario: usuarioLogado,
      }),
    })
      .then(() => buscarItens())
      .catch(() => Alert.alert('Erro', 'Falha na movimentação.'));
  };

  // 6. ZERAR TODO O ESTOQUE
  const zerarTudo = () => {
    Alert.alert('Zerar Estoque', 'Deseja realmente apagar todo o estoque?', [
      { text: 'Cancelar' },
      {
        text: 'Sim, Zerar',
        onPress: () => {
          fetch(`http://${IP}:5000/api/zerar-estoque`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario: usuarioLogado }),
          })
            .then(() => {
              Alert.alert('Sucesso', 'Estoque zerado!');
              buscarItens();
            })
            .catch(() => Alert.alert('Erro', 'Não foi possível zerar.'));
        },
      },
    ]);
  };

  // ==========================================
  // TELA 1: SE NÃO ESTIVER LOGADO -> MOSTRA LOGIN
  // ==========================================
  if (!usuarioLogado) {
    return (
      <View style={styles.loginContainer}>
        <View style={styles.blocoLogin}>
          <Text style={styles.titulo}>Almoxarifado</Text>
          <Text style={styles.subtitulo}>Acesso ao Sistema</Text>

          <TextInput
            style={styles.input}
            placeholder="Nome de usuário"
            value={usuario}
            onChangeText={setUsuario}
            autoCapitalize="none"
          />

          <TextInput
            style={styles.input}
            placeholder="Senha"
            secureTextEntry={true}
            value={senha}
            onChangeText={setSenha}
          />

          <TouchableOpacity style={styles.botaoAzul} onPress={fazerLogin}>
            <Text style={styles.textoBotao}>Entrar</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // ==========================================
  // TELA 2: SE ESTIVER LOGADO -> MOSTRA ESTOQUE
  // ==========================================
  return (
    <View style={styles.container}>
      {/* BARRA DO TOPO COM O NOME DO USUÁRIO E BOTÃO SAIR */}
      <View style={styles.barraTopo}>
        <Text style={styles.usuarioTexto}>Olá, {usuarioLogado}!</Text>
        <TouchableOpacity style={styles.botaoSair} onPress={sair}>
          <Text style={styles.textoBotaoSair}>Sair</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.titulo}>Controle de Estoque</Text>

      {/* FORMULÁRIO DE CADASTRO */}
      <View style={styles.blocoCadastro}>
        <TextInput
          style={styles.input}
          placeholder="Nome da ferramenta (ex: Martelo)"
          value={nome}
          onChangeText={setNome}
        />
        <TextInput
          style={styles.input}
          placeholder="Quantidade inicial"
          keyboardType="numeric"
          value={qntd}
          onChangeText={setQntd}
        />
        <TouchableOpacity style={styles.botaoAzul} onPress={cadastrar}>
          <Text style={styles.textoBotao}>+ Cadastrar Ferramenta</Text>
        </TouchableOpacity>
      </View>

      {/* BOTÕES GERAIS */}
      <View style={styles.linhaGeral}>
        <TouchableOpacity style={styles.botaoCinza} onPress={buscarItens}>
          <Text style={styles.textoBotao}>🔄 Atualizar Lista</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.botaoVermelho} onPress={zerarTudo}>
          <Text style={styles.textoBotao}>🗑️ Zerar Estoque</Text>
        </TouchableOpacity>
      </View>

      {/* LISTA DE FERRAMENTAS */}
      <FlatList
        data={lista}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <View style={styles.itemCard}>
            <View>
              <Text style={styles.itemNome}>{item.nome}</Text>
              <Text style={styles.itemQtd}>Qtd no banco: {item.qntd}</Text>
            </View>

            <View style={styles.botoesAcao}>
              <TouchableOpacity
                style={styles.botaoVerde}
                onPress={() => movimentar(item.id, 'Entrada', item.qntd)}
              >
                <Text style={styles.textoBotao}>+ Entrada</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.botaoLaranja}
                onPress={() => movimentar(item.id, 'Saída', item.qntd)}
              >
                <Text style={styles.textoBotao}>- Saída</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      />
    </View>
  );
}

// ESTILOS SIMPLES
const styles = StyleSheet.create({
  loginContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#e9ecef',
  },
  blocoLogin: {
    backgroundColor: '#ffffff',
    padding: 20,
    borderRadius: 10,
    elevation: 3,
  },
  subtitulo: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  barraTopo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  usuarioTexto: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  botaoSair: {
    backgroundColor: '#dc3545',
    paddingVertical: 5,
    paddingHorizontal: 12,
    borderRadius: 5,
  },
  textoBotaoSair: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
  },
  container: {
    flex: 1,
    paddingTop: 45,
    paddingHorizontal: 15,
    backgroundColor: '#f2f2f2',
  },
  titulo: {
    fontSize: 22,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  blocoCadastro: {
    backgroundColor: '#ffffff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
    elevation: 2,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 5,
    padding: 8,
    marginBottom: 8,
    backgroundColor: '#fff',
  },
  linhaGeral: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  botaoAzul: {
    backgroundColor: '#0066cc',
    padding: 10,
    borderRadius: 5,
    alignItems: 'center',
  },
  botaoVerde: {
    backgroundColor: '#28a745',
    padding: 8,
    borderRadius: 5,
    marginRight: 5,
  },
  botaoLaranja: {
    backgroundColor: '#fd7e14',
    padding: 8,
    borderRadius: 5,
  },
  botaoVermelho: {
    backgroundColor: '#dc3545',
    padding: 10,
    borderRadius: 5,
    flex: 1,
    marginLeft: 5,
    alignItems: 'center',
  },
  botaoCinza: {
    backgroundColor: '#6c757d',
    padding: 10,
    borderRadius: 5,
    flex: 1,
    marginRight: 5,
    alignItems: 'center',
  },
  textoBotao: {
    color: '#fff',
    fontWeight: 'bold',
  },
  itemCard: {
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    elevation: 1,
  },
  itemNome: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  itemQtd: {
    fontSize: 14,
    color: '#555',
  },
  botoesAcao: {
    flexDirection: 'row',
  },
});