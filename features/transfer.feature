# language: pt
@ui @transfer
Funcionalidade: Transferência de Fundos
  Como um correntista autenticado
  Desejo transferir valores entre contas distintas
  Para gerenciar meus saldos disponíveis

  Contexto:
    Dado que estou autenticado com um usuário provisionado via backend e possuo duas contas
    E navego para a tela de transferência de fundos

  @smoke
  Cenário: Transferência de fundos entre contas distintas realizada com sucesso
    Quando realizo a transferência da quantia de "25.00" entre contas distintas
    Então a transferência deve ser concluída exibindo o valor "25.00" e as contas envolvidas
    E os saldos das duas contas devem refletir a transferência

  Esquema do Cenário: Transferência com formato de valor inválido
    Quando realizo a tentativa de transferência com valor "<valor>"
    Então o sistema deve apresentar o erro de transferência "An internal error has occurred and has been logged."
    E os saldos das duas contas devem permanecer inalterados

    Exemplos:
      | valor       |
      |             |
      | valor_texto |