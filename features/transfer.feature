# language: pt
Funcionalidade: Transferência de Fundos
  Como um correntista autenticado
  Desejo transferir valores entre contas
  Para gerenciar meus saldos disponíveis

  Contexto:
    Dado que estou autenticado no sistema com usuário provisionado via API
    E navego para a tela de transferência de fundos

  Cenário: Transferência de fundos com valor válido realizada com sucesso
    Quando realizo a transferência da quantia de "150.00" entre as contas
    Então a transferência deve ser concluída exibindo o valor "150.00" e as contas envolvidas

  Esquema do Cenário: Validação de transferência com entradas inválidas
    Quando realizo a tentativa de transferência com valor "<valor>"
    Então o sistema deve impedir a operação apresentando indicativo de erro

    Exemplos:
      | valor       |
      | 0           |
      | -50.00      |
      | valor_texto |