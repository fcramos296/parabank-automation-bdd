# language: pt
Funcionalidade: Registro de Usuário
  Como um novo cliente do Parabank
  Desejo realizar meu cadastro
  Para acessar os serviços bancários da plataforma

  Contexto:
    Dado que estou na página de registro

  Cenário: Cadastro com sucesso fornecendo todos os campos válidos
    Quando preencho o formulário de cadastro com dados dinâmicos válidos
    E submeto o formulário de registro
    Então devo visualizar a mensagem de boas-vindas do usuário registrado

  Cenário: Tentativa de cadastro com confirmação de senha divergente
    Quando preencho o formulário informando a senha "Secr3t!2026" e confirmação "Mismatch!2026"
    E submeto o formulário de registro
    Então devo visualizar o erro de validação de confirmação de senha "Passwords did not match."

  Cenário: Tentativa de cadastro com nome de usuário já existente
    Dado que um usuário "existing_qa_user" foi previamente provisionado via API
    Quando preencho o formulário de cadastro utilizando o username "existing_qa_user"
    E submeto o formulário de registro
    Então devo visualizar a mensagem de erro "This username already exists."