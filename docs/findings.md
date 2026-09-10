# Findings de qualidade

Este documento registra comportamentos observados durante a construção da suíte que são relevantes para a estratégia de teste, mas não devem ser transformados em contratos funcionais artificiais.

## 1. Entrada monetária inválida em Transfer Funds

### Comportamento observado

Na imagem oficial do ParaBank utilizada pelo projeto, tentativas de transferência com entradas como:

- valor vazio;
- texto não numérico;
- valor com vírgula decimal, como `10,50`;

são rejeitadas, porém a interface apresenta a mensagem genérica:

```text
An internal error has occurred and has been logged.
```

### Avaliação de QA

A rejeição da operação é correta, mas expor um erro interno para uma entrada inválida é tratado como **defeito conhecido de validação/experiência**, não como comportamento funcional esperado.

Por esse motivo, os cenários `@known_defect` não afirmam o texto do erro interno. Eles validam as invariantes de negócio observáveis:

- não existe confirmação de transferência concluída;
- nenhuma nova transação é criada;
- saldo de origem permanece inalterado;
- saldo de destino permanece inalterado.

A ausência de transações é observada durante uma janela limitada de estabilização para reduzir o risco de falso positivo causado por uma eventual persistência assíncrona.

## 2. Saldo negativo

### Comportamento observado

O domínio atual do ParaBank permite débito que leve uma conta a saldo negativo. A implementação exercitada pela aplicação não rejeita uma transferência apenas porque o valor é maior que o saldo disponível.

### Decisão de teste

A suíte não cria um cenário de "saldo insuficiente deve rejeitar a transferência", pois isso inventaria uma regra de negócio que o SUT atual não implementa.

Caso essa regra seja introduzida futuramente, a cobertura deverá ser atualizada a partir do requisito correspondente.

## 3. Ambiente público do ParaBank

Durante a investigação inicial, a instância pública apresentou estado compartilhado e comportamentos instáveis entre execuções, incluindo respostas inconsistentes para clientes recém-criados.

A versão final do projeto utiliza a imagem oficial do ParaBank em Docker e recria o ambiente para cada execução. Essa decisão não esconde defeitos do produto: ela remove interferência externa e permite que falhas observadas sejam reproduzidas sobre um estado conhecido e controlado.
