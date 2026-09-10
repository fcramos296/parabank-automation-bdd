# language: pt

@ui @login
Funcionalidade: Autenticação e Encerramento de Sessão
  Como um cliente cadastrado
  Desejo autenticar e encerrar minha sessão
  Para acessar os serviços da conta com segurança

  Contexto:
    Dado que estou na tela de login

  @smoke
  Cenário: Login efetuado com credenciais válidas
    Dado que existe um usuário exclusivo cadastrado para autenticação
    Quando informo as credenciais válidas desse usuário
    Então devo estar autenticado e visualizar os serviços da conta

  Cenário: Falha de login com usuário inexistente
    Quando realizo login com usuário "inexistente" e senha "wrong_pass"
    Então devo visualizar a mensagem de erro de autenticação "The username and password could not be verified."

  Cenário: Falha de login com senha incorreta para usuário existente
    Dado que existe um usuário exclusivo cadastrado para autenticação
    Quando realizo login com esse usuário e senha "wrong_pass"
    Então devo visualizar a mensagem de erro de autenticação "The username and password could not be verified."

  Esquema do Cenário: Falha de login com campos obrigatórios vazios
    Quando realizo login com usuário "<usuario>" e senha "<senha>"
    Então devo visualizar a mensagem de erro de autenticação "<mensagem_erro>"

    Exemplos:
      | usuario       | senha | mensagem_erro                         |
      |               | 12345 | Please enter a username and password. |
      | user_sem_pass |       | Please enter a username and password. |
      |               |       | Please enter a username and password. |

  Cenário: Logout encerra a sessão autenticada
    Dado que existe um usuário exclusivo cadastrado para autenticação
    Quando informo as credenciais válidas desse usuário
    E solicito o logout
    Então devo retornar à tela de login sem sessão autenticada

  Cenário: Área protegida exige nova autenticação após logout
    Dado que existe um usuário exclusivo cadastrado para autenticação
    Quando informo as credenciais válidas desse usuário
    E solicito o logout
    E tento acessar diretamente a transferência de fundos
    Então devo ser solicitado a autenticar novamente com a mensagem "You must be logged in to use this feature."
