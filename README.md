# ParaBank Automation BDD

[![ParaBank E2E](https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/e2e.yml/badge.svg)](https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/e2e.yml)

Projeto de automação funcional end-to-end para o **ParaBank**, desenvolvido com **Python, Playwright e Behave**, utilizando **BDD/Gherkin**, **Page Object Model**, preparação de dados via backend, validações cruzadas entre UI e API, ambiente descartável com **Docker** e evidências com **Allure Report**.

A estratégia final executa a aplicação oficial ParaBank localmente em container e recria o ambiente a cada execução. Isso elimina dependência de estado compartilhado do ambiente público e permite trabalhar com massa exclusiva, saldos determinísticos e assertions mais fortes.

---

## Objetivo

O projeto demonstra uma estratégia de qualidade próxima de um cenário real, evitando tratar automação como uma coleção de scripts de interface.

Principais decisões:

- UI utilizada para validar os comportamentos que o usuário realmente executa;
- backend utilizado para preparar pré-condições e validar efeitos persistidos;
- cliente e contas exclusivos por cenário quando necessário;
- ambiente ParaBank recriado antes de cada execução;
- isolamento por `BrowserContext` do Playwright;
- Page Object Model para abstração da interface;
- BDD para descrição dos comportamentos;
- validações de estado, saldo e transações no backend;
- screenshots automáticos em falhas;
- relatório Allure;
- bootstrap cross-platform;
- CI/CD com regressão completa e smoke cross-browser.

---

## Stack

| Tecnologia | Uso |
| --- | --- |
| Python | Linguagem do framework |
| Playwright | Automação web |
| Behave | Runner BDD |
| Gherkin | Especificação dos cenários |
| Requests | Setup e validações de backend |
| Pydantic Settings | Configuração do ambiente |
| Docker / Docker Compose | Ambiente ParaBank descartável |
| Allure | Evidências e relatório |
| GitHub Actions | CI/CD |

---

## Cobertura

A suíte cobre exclusivamente os três fluxos definidos para o projeto: **login/logout, registro de usuário e transferência de fundos**.

Atualmente são **24 cenários gerados**.

### Login e logout

Cobertura relevante:

- login com credenciais válidas;
- persistência da sessão após reload;
- recuperação de uma tentativa inválida seguida por login válido;
- usuário inexistente;
- senha incorreta para usuário existente;
- username vazio;
- senha vazia;
- ambos os campos vazios;
- logout encerrando a sessão;
- bloqueio de área protegida após logout.

Usuários necessários como pré-condição são criados via backend para que os cenários de login testem apenas autenticação e sessão.

### Registro de usuário

Cobertura relevante:

- cadastro completo válido;
- persistência dos dados informados;
- autenticação backend do cliente recém-cadastrado;
- criação da conta CHECKING inicial;
- validação do saldo inicial `515.50` da configuração padrão do ParaBank;
- cadastro sem telefone, validando o campo como opcional;
- persistência do telefone vazio;
- username e senha no limite suportado de 20 caracteres;
- validação conjunta de todos os campos obrigatórios;
- confirmação de senha divergente;
- username duplicado.

Quando registro é o comportamento em teste, o cadastro é feito pela interface. A API é usada apenas depois da ação para validar persistência e efeitos do fluxo.

### Transferência de fundos

Cada cenário recebe um cliente exclusivo com duas contas próprias.

Cobertura relevante:

- transferência positiva com valor monetário comum;
- transferência mínima de `0.01`;
- transferência no sentido inverso entre as contas;
- transferência de todo o saldo disponível, validando saldo de origem igual a zero;
- seletores exibindo apenas contas pertencentes ao cliente autenticado;
- exclusão de conta pertencente a outro cliente dos seletores;
- valor vazio;
- valor textual;
- formato monetário com vírgula;
- confirmação da transferência na UI;
- conferência de conta origem e destino apresentadas na confirmação;
- validação de `Debit / Funds Transfer Sent` na origem;
- validação de `Credit / Funds Transfer Received` no destino;
- validação exata dos saldos após transferências válidas;
- validação de saldos inalterados após tentativas rejeitadas;
- validação de que tentativas rejeitadas não criam transações.

O projeto não cria uma expectativa de rejeição por saldo insuficiente porque a própria implementação do ParaBank permite saldo negativo. Os testes seguem o comportamento de domínio existente em vez de inventar uma regra não implementada.

---

## Estrutura

```text
.
├── .github/
│   └── workflows/
│       └── e2e.yml
├── config/
│   └── settings.py
├── features/
│   ├── steps/
│   ├── environment.py
│   ├── login.feature
│   ├── registration.feature
│   └── transfer.feature
├── pages/
│   ├── base_page.py
│   ├── login_page.py
│   ├── register_page.py
│   └── transfer_page.py
├── scripts/
│   ├── bootstrap_docker.py
│   ├── bootstrap_python_windows.ps1
│   ├── configure_env.py
│   ├── parabank_env.py
│   └── run.py
├── services/
│   ├── http_transport.py
│   └── parabank_api_client.py
├── utils/
│   └── test_data.py
├── compose.yaml
├── requirements.txt
├── run_tests.bat
└── run_tests.sh
```

---

## Execução rápida

### Windows

Para experiência guiada:

```powershell
run_tests.bat
```

Quando Python já estiver instalado, também é possível executar diretamente:

```powershell
python scripts/run.py
```

### Linux / macOS

```bash
chmod +x run_tests.sh
./run_tests.sh
```

Ou, quando Python já estiver disponível:

```bash
python3 scripts/run.py
```

---

## Bootstrap automático

Os wrappers foram preparados para reduzir os pré-requisitos de uma máquina nova.

### Windows

`run_tests.bat` pode preparar Python quando ausente. Depois o `run.py` verifica e prepara, quando autorizado:

- WSL 2;
- Virtual Machine Platform através da instalação do WSL;
- atualização do WSL;
- Docker Desktop;
- Docker Compose;
- ambiente virtual Python;
- dependências;
- browser Playwright;
- container ParaBank.

Se o Windows exigir reinicialização após habilitar WSL/recursos de virtualização, o runner encerra com orientação para reiniciar e executar novamente.

Virtualização Intel VT-x / AMD-V desabilitada no BIOS/UEFI não pode ser alterada com segurança pelo projeto; nesse caso o runner informa o requisito.

### Linux

O fluxo pode preparar:

- Python, pip e venv através de gerenciadores de pacotes suportados;
- Docker Engine;
- Docker Compose plugin;
- dependências Python;
- browser Playwright;
- ParaBank.

São suportados caminhos baseados em `apt`, `dnf`, `yum`, `pacman` e `zypper` quando disponíveis.

### macOS

O fluxo pode preparar:

- Python;
- Homebrew quando necessário e autorizado;
- Docker Desktop;
- Docker Compose;
- dependências Python;
- browser Playwright;
- ParaBank.

A primeira inicialização do Docker Desktop pode exigir permissões ou aceite de termos do próprio produto.

Detalhes adicionais estão em [`DOCKER_SETUP.md`](DOCKER_SETUP.md).

---

## Ciclo do ambiente

Em uma execução normal:

```text
docker compose down --volumes --remove-orphans
                ↓
docker compose up -d
                ↓
aguarda ParaBank responder
                ↓
executa a suíte
                ↓
gera evidências
                ↓
docker compose down --volumes --remove-orphans
```

O ambiente é recriado antes da suíte para evitar acúmulo de massa e interferência entre execuções.

Para manter o ParaBank ativo após os testes:

```bash
python scripts/run.py --keep-environment
```

Aplicação:

```text
http://localhost:8080/parabank
```

---

## Comandos úteis

Suíte completa:

```bash
python scripts/run.py
```

Somente login/logout:

```bash
python scripts/run.py --scope login
```

Somente registro:

```bash
python scripts/run.py --scope registration
```

Somente transferência:

```bash
python scripts/run.py --scope transfer
```

Smoke:

```bash
python scripts/run.py --tags "@smoke"
```

Browser visível:

```bash
python scripts/run.py --headed
```

Firefox:

```bash
python scripts/run.py --browser firefox
```

WebKit:

```bash
python scripts/run.py --browser webkit
```

Autorizar bootstrap do Docker sem pergunta interativa:

```bash
python scripts/run.py --install-docker
```

Impedir instalação de Docker na máquina:

```bash
python scripts/run.py --no-docker-install
```

---

## Estratégia de dados

Os dados são gerados dinamicamente e evitam dependência de usuários fixos.

Exemplo conceitual:

```text
cenário
  ↓
cliente exclusivo
  ↓
pré-condições via backend
  ↓
UI executa comportamento em teste
  ↓
UI valida resultado visível
  ↓
API valida persistência/efeitos
```

Username e SSN são únicos por execução. Cenários independentes não reutilizam a mesma sessão de navegador.

---

## Page Object Model

Os Page Objects concentram interação e assertions específicas da interface.

As steps do Behave descrevem o comportamento e coordenam Page Objects, dados e serviços, sem espalhar seletores CSS pelas features.

---

## Evidências e Allure

Em falhas, o hook do Behave captura screenshot automaticamente.

Resultados:

```text
reports/allure-results
```

Os wrappers interativos permitem gerar e abrir o relatório Allure ao final.

No CI, os resultados e o HTML do Allure são publicados como artifacts mesmo quando a regressão falha, permitindo análise posterior.

---

## CI/CD

Workflow:

```text
.github/workflows/e2e.yml
```

### Pull Request para `main`

Executa:

```text
Python 3.12
↓
validação de Docker/Compose
↓
instalação das dependências
↓
compileall dos fontes Python
↓
Chromium + dependências Playwright
↓
ParaBank Docker com banco limpo
↓
regressão completa
↓
Allure artifacts
```

A regressão completa em Chromium funciona como **quality gate** do PR.

### Push em `main`

Executa em paralelo:

1. regressão completa em Chromium;
2. smoke em Firefox;
3. smoke em WebKit.

Com todos os gates verdes, o relatório Allure da regressão pode ser publicado em GitHub Pages quando Pages estiver habilitado no repositório.

### Execução manual

`workflow_dispatch` permite escolher:

- `full`;
- `smoke`;
- `login`;
- `registration`;
- `transfer`;

E também:

- Chromium;
- Firefox;
- WebKit.

O CI não depende de secrets de terceiros e não utiliza o ambiente público do ParaBank.

---

## Princípios aplicados

- testes independentes;
- preparação API-first de pré-condições;
- UI focada no comportamento em teste;
- dados dinâmicos;
- ambiente determinístico;
- assertions de backend após ações críticas;
- isolamento de sessão;
- ausência de sleeps fixos para sincronização funcional;
- uso de auto-wait e assertions do Playwright;
- falhas com mensagens diagnósticas;
- evidências automáticas;
- execução reproduzível local/CI;
- cobertura orientada a risco e regra de negócio, não a quantidade de cenários.
