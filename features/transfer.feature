# language: pt
@ui @transfer
Funcionalidade: Transferência de Fundos
  Como um correntista autenticado
  Desejo transferir valores entre contas distintas
  Para gerenciar meus saldos disponíveis

  Contexto:
    Dado que estou autenticado com um usuário existente do ambiente público e possuo duas contas
    E navego para a tela de transferência de fundos

  @smoke
  Cenário: Transferência de fundos entre contas distintas realizada com sucesso
    Quando realizo a transferência da quantia de "17.31" entre contas distintas
    Então a transferência deve ser concluída exibindo o valor "17.31" e as contas envolvidas
    E os lançamentos de débito e crédito devem registrar a transferência

  Esquema do Cenário: Transferência com formato de valor inválido
    Quando realizo a tentativa de transferência com valor "<valor>"
    Então o sistema deve apresentar o erro de transferência "An internal error has occurred and has been logged."

    Exemplos:
      | valor       |
      |             |
      | valor_texto |
