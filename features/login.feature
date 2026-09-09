# language: pt
Funcionalidade: Autenticação de Usuário
  Como um cliente cadastrado
  Desejo efetuar login
  Para gerenciar minhas contas

  Contexto:
    Dado que estou na tela de login

  Cenário: Login efetuado com credenciais válidas
    Dado que existe um usuário registrado via API com credenciais válidas
    Quando informo o usuário e senha cadastrados
    Então sou direcionado para a tela de visão geral da conta

  Esquema do Cenário: Falha de login com credenciais incorretas ou vazias
    Quando realizo login com usuário "<usuario>" e senha "<senha>"
    Então devo visualizar a mensagem de erro de autenticação "<mensagem_erro>"

    Exemplos:
      | usuario            | senha        | mensagem_erro                                    |
      | nao_existe_qa_user | wrong_pass   | The username and password could not be verified. |
      |                    | 12345        | Please enter a username and password.            |
      | user_sem_pass      |              | Please enter a username and password.            |