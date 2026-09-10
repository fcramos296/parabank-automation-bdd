# language: pt

@ui @registration
Funcionalidade: Registro de Usuário
  Como um novo cliente do ParaBank
  Desejo realizar meu cadastro
  Para acessar os serviços bancários da plataforma

  Contexto:
    Dado que estou na página de registro

  @smoke
  Cenário: Cadastro com sucesso fornecendo todos os campos válidos
    Quando preencho o formulário de cadastro com dados dinâmicos válidos
    E submeto o formulário de registro
    Então devo visualizar a mensagem de boas-vindas do usuário registrado
    E os dados do novo cliente devem estar persistidos corretamente
    E o cliente deve possuir uma conta corrente inicial com saldo "515.50"

  Cenário: Cadastro com sucesso sem informar o telefone opcional
    Quando preencho o formulário de cadastro com dados válidos sem informar telefone
    E submeto o formulário de registro
    Então devo visualizar a mensagem de boas-vindas do usuário registrado
    E os dados do novo cliente devem estar persistidos corretamente
    E o telefone persistido deve permanecer vazio

  Cenário: Cadastro aceita credenciais no limite máximo suportado
    Quando preencho o cadastro com username e senha de 20 caracteres
    E submeto o formulário de registro
    Então devo visualizar a mensagem de boas-vindas do usuário registrado
    E os dados do novo cliente devem estar persistidos corretamente

  Cenário: Tentativa de cadastro sem preencher os campos obrigatórios
    Quando submeto o formulário de registro
    Então devo visualizar os erros de todos os campos obrigatórios do cadastro

  Cenário: Tentativa de cadastro com confirmação de senha divergente
    Quando preencho o formulário informando a senha "Secr3t!2026" e confirmação "Mismatch!2026"
    E submeto o formulário de registro
    Então devo visualizar o erro de validação de confirmação de senha "Passwords did not match."

  Cenário: Tentativa de cadastro com nome de usuário já existente
    Dado que existe um usuário previamente provisionado via backend
    Quando preencho o formulário de cadastro utilizando esse username
    E submeto o formulário de registro
    Então devo visualizar a mensagem de erro "This username already exists."
