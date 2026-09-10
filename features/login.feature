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
    Dado que possuo credenciais válidas de um usuário existente no ambiente público
    Quando informo as credenciais válidas desse usuário
    Então devo estar autenticado e visualizar os serviços da conta

  @known_issue
  Esquema do Cenário: Falha de login com credenciais inválidas
    Quando realizo login com usuário "<usuario>" e senha "<senha>"
    Então a tentativa de autenticação deve ser rejeitada com uma mensagem de erro

    Exemplos:
      | usuario     | senha      |
      | inexistente | wrong_pass |
      | existente   | wrong_pass |

  Esquema do Cenário: Falha de login com campos obrigatórios vazios
    Quando realizo login com usuário "<usuario>" e senha "<senha>"
    Então devo visualizar a mensagem de erro de autenticação "<mensagem_erro>"

    Exemplos:
      | usuario       | senha | mensagem_erro                         |
      |               | 12345 | Please enter a username and password. |
      | user_sem_pass |       | Please enter a username and password. |
      |               |       | Please enter a username and password. |

  Cenário: Logout encerra a sessão autenticada
    Dado que possuo credenciais válidas de um usuário existente no ambiente público
    Quando informo as credenciais válidas desse usuário
    E solicito o logout
    Então devo retornar à tela de login sem sessão autenticada

  Cenário: Área protegida exige nova autenticação após logout
    Dado que possuo credenciais válidas de um usuário existente no ambiente público
    Quando informo as credenciais válidas desse usuário
    E solicito o logout
    E tento acessar diretamente a transferência de fundos
    Então devo ser solicitado a autenticar novamente com a mensagem "You must be logged in to use this feature."
