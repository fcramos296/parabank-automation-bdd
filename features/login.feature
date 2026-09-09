# language: pt

@ui @login
Funcionalidade: Autenticação de Usuário
  Como um cliente cadastrado
  Desejo efetuar login
  Para acessar os serviços disponíveis para minha conta

  Contexto:
    Dado que estou na tela de login

  @smoke
  Cenário: Login efetuado com credenciais válidas
    Dado que existe um usuário registrado via backend com credenciais válidas
    Quando informo o usuário e senha cadastrados
    Então devo estar autenticado e visualizar os serviços da conta

  Cenário: Falha de login com credenciais inexistentes
    Quando realizo login com usuário "inexistente" e senha "wrong_pass"
    Então a tentativa de autenticação deve ser rejeitada com uma mensagem de erro

  Esquema do Cenário: Falha de login com campos obrigatórios vazios
    Quando realizo login com usuário "<usuario>" e senha "<senha>"
    Então devo visualizar a mensagem de erro de autenticação "<mensagem_erro>"

    Exemplos:
      | usuario       | senha | mensagem_erro                           |
      |               | 12345 | Please enter a username and password.   |
      | user_sem_pass |       | Please enter a username and password.   |