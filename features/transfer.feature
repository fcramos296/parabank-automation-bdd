# language: pt

@ui @transfer
Funcionalidade: Transferência de Fundos
  Como um correntista autenticado
  Desejo transferir valores entre contas distintas
  Para gerenciar meus saldos disponíveis

  Contexto:
    Dado que estou autenticado com um usuário exclusivo e possuo duas contas

  @smoke
  Cenário: Transferência de fundos entre contas distintas realizada com sucesso
    E navego para a tela de transferência de fundos
    Quando realizo a transferência da quantia de "17.31" entre contas distintas
    Então a transferência deve ser concluída exibindo o valor "17.31" e as contas envolvidas
    E os lançamentos de débito e crédito devem registrar a transferência
    E os saldos das duas contas devem refletir a transferência

  Cenário: Transferência do menor valor monetário com duas casas decimais
    E navego para a tela de transferência de fundos
    Quando realizo a transferência da quantia de "0.01" entre contas distintas
    Então a transferência deve ser concluída exibindo o valor "0.01" e as contas envolvidas
    E os lançamentos de débito e crédito devem registrar a transferência
    E os saldos das duas contas devem refletir a transferência

  Cenário: Transferência no sentido inverso entre as duas contas
    E navego para a tela de transferência de fundos
    Quando realizo a transferência da quantia de "25.00" da segunda conta para a primeira
    Então a transferência deve ser concluída exibindo o valor "25.00" e as contas envolvidas
    E os lançamentos de débito e crédito devem registrar a transferência
    E os saldos das duas contas devem refletir a transferência

  Cenário: Transferência de todo o saldo disponível da conta de origem
    E navego para a tela de transferência de fundos
    Quando transfiro todo o saldo disponível da conta de origem
    Então a transferência do saldo total deve ser concluída entre as contas
    E os lançamentos de débito e crédito devem registrar a transferência
    E os saldos das duas contas devem refletir a transferência
    E a conta de origem deve ficar com saldo zero

  Cenário: Seletores de transferência exibem somente contas do cliente autenticado
    Dado que existe uma conta pertencente a outro cliente
    E navego para a tela de transferência de fundos
    Então os seletores devem listar somente as contas do cliente autenticado

  Esquema do Cenário: Transferência com formato de valor inválido
    E navego para a tela de transferência de fundos
    Quando realizo a tentativa de transferência com valor "<valor>"
    Então o sistema deve apresentar o erro de transferência "An internal error has occurred and has been logged."
    E os saldos das duas contas devem permanecer inalterados
    E nenhuma transação deve ser criada para a tentativa rejeitada

    Exemplos:
      | valor       |
      |             |
      | valor_texto |
      | 10,50       |
