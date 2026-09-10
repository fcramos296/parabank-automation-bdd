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
    Dado navego para a tela de transferência de fundos
    Quando realizo a transferência da quantia de "17.31" entre contas distintas
    Então a transferência deve ser concluída exibindo o valor "17.31" e as contas envolvidas
    E os lançamentos de débito e crédito devem registrar a transferência
    E os saldos das duas contas devem refletir a transferência

  Cenário: Transferência do menor valor monetário com duas casas decimais
    Dado navego para a tela de transferência de fundos
    Quando realizo a transferência da quantia de "0.01" entre contas distintas
    Então a transferência deve ser concluída exibindo o valor "0.01" e as contas envolvidas
    E os lançamentos de débito e crédito devem registrar a transferência
    E os saldos das duas contas devem refletir a transferência

  Cenário: Transferência no sentido inverso entre as duas contas
    Dado navego para a tela de transferência de fundos
    Quando realizo a transferência da quantia de "25.00" da segunda conta para a primeira
    Então a transferência deve ser concluída exibindo o valor "25.00" e as contas envolvidas
    E os lançamentos de débito e crédito devem registrar a transferência
    E os saldos das duas contas devem refletir a transferência

  Cenário: Transferência de todo o saldo disponível da conta de origem
    Dado navego para a tela de transferência de fundos
    Quando transfiro todo o saldo disponível da conta de origem
    Então a transferência do saldo total deve ser concluída entre as contas
    E os lançamentos de débito e crédito devem registrar a transferência
    E os saldos das duas contas devem refletir a transferência
    E a conta de origem deve ficar com saldo zero

  Cenário: Seletores de transferência exibem somente contas do cliente autenticado
    Dado que existe uma conta pertencente a outro cliente
    E navego para a tela de transferência de fundos
    Então os seletores devem listar somente as contas do cliente autenticado

  @known_defect
  Esquema do Cenário: Entrada monetária inválida é rejeitada sem alterar estado
    Dado navego para a tela de transferência de fundos
    Quando realizo a tentativa de transferência com valor "<valor>"
    Então a transferência deve ser rejeitada sem confirmação de sucesso
    E nenhuma transação deve ser criada para a tentativa rejeitada
    E os saldos das duas contas devem permanecer inalterados

    Exemplos:
      | valor       |
      | [vazio]     |
      | valor_texto |
      | 10,50       |
