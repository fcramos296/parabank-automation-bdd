<h1 align="center">ParaBank Automation BDD</h1>

<p align="center">
  Framework E2E com <strong>Python + Playwright + Behave</strong>, ambiente determinístico em Docker,<br/>
  validações UI + API, Allure Report e CI/CD cross-browser.
</p>

<p align="center">
  <a href="https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/e2e.yml">
    <img src="https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/e2e.yml/badge.svg" alt="ParaBank E2E" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Playwright-1.62-2EAD33?logo=playwright&logoColor=white" alt="Playwright" />
  <img src="https://img.shields.io/badge/BDD-Behave-6A5ACD" alt="Behave BDD" />
  <img src="https://img.shields.io/badge/Docker-Local-2496ED?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Allure-Report-FF6A00" alt="Allure Report" />
</p>

---

## 📌 Sobre o projeto

Este projeto automatiza os fluxos de **Login/Logout**, **Registro de Usuário** e **Transferência de Fundos** do ParaBank.

A solução foi estruturada como um framework de automação sustentável, com isolamento de dados, pré-condições via API, validação de efeitos persistidos, Page Object Model, ambiente reproduzível e quality gates em CI/CD.

### ✨ Destaques

- **24 cenários E2E** orientados a risco e regra de negócio;
- massa exclusiva e dinâmica por cenário;
- `BrowserContext` independente por cenário;
- API-first para pré-condições técnicas;
- validações cruzadas entre interface e backend;
- `Decimal` para valores monetários;
- polling com deadline em vez de sleeps fixos para consistência backend;
- ambiente ParaBank descartável em Docker;
- Ruff + `behave --dry-run` como gates estáticos;
- regressão completa em Chromium;
- smoke cross-browser em Firefox e WebKit;
- screenshots no Allure em caso de falha;
- bootstrap para Windows, Linux e macOS.

---

## 🧰 Stack

| Tecnologia | Responsabilidade |
| --- | --- |
| **Python** | Linguagem principal do framework |
| **Playwright** | Automação web e assertions de interface |
| **Behave / Gherkin** | BDD e especificação dos comportamentos |
| **Requests** | Setup e validações de backend |
| **Pydantic Settings** | Configuração do ambiente e timeouts |
| **Docker / Compose** | Ambiente ParaBank descartável |
| **Ruff** | Análise estática |
| **Allure Report** | Evidências e relatório HTML |
| **GitHub Actions** | CI/CD e quality gates |

---

## 🧠 Estratégia de testes

A automação separa claramente pré-condição, comportamento e validação persistida:

```text
pré-condição técnica      → API / backend
comportamento do usuário  → UI / Playwright
efeito persistido         → API / backend
evidência                 → Allure
```

Isso evita executar pela interface etapas que não fazem parte do comportamento em teste e reduz tempo, acoplamento e flakiness.

### 🔐 Login e Logout — 10 cenários

Cobertura:

- login válido;
- persistência da sessão após reload;
- recuperação após tentativa com senha incorreta;
- usuário inexistente;
- senha incorreta para usuário existente;
- username vazio;
- senha vazia;
- ambos os campos vazios;
- logout encerrando a sessão;
- bloqueio de área protegida após logout.

Usuários necessários como pré-condição são provisionados via backend para que o cenário exercite exclusivamente autenticação e sessão.

### 👤 Registro de Usuário — 6 cenários

Cobertura:

- cadastro completo válido;
- persistência dos dados informados;
- autenticação backend do cliente criado;
- criação automática da conta `CHECKING`;
- validação do saldo inicial;
- telefone opcional;
- username e senha no boundary de 20 caracteres;
- campos obrigatórios;
- confirmação de senha divergente;
- username duplicado.

Quando **registro** é o comportamento em teste, o cadastro acontece pela interface. O backend é utilizado depois da ação para confirmar os efeitos persistidos.

### 💸 Transferência de Fundos — 8 cenários

Cobertura:

- transferência com valor monetário comum;
- boundary mínimo de `0.01`;
- transferência no sentido inverso;
- transferência de todo o saldo disponível;
- saldo final da origem igual a `0.00`;
- isolamento das contas exibidas nos seletores;
- valor vazio;
- valor textual;
- formato monetário com vírgula.

Nas transferências válidas a suíte verifica:

```text
confirmação na UI
      ↓
conta origem / destino
      ↓
Debit - Funds Transfer Sent
      ↓
Credit - Funds Transfer Received
      ↓
saldos exatos no backend
```

Nas tentativas rejeitadas:

```text
sem confirmação de sucesso
      ↓
janela de estabilização
      ↓
nenhuma transação criada
      ↓
saldos inalterados
```

Os exemplos de entrada monetária inválida são marcados com `@known_defect` porque a versão atual do ParaBank expõe uma mensagem genérica de erro interno. A suíte **não protege o texto do erro como contrato**: ela continua validando as invariantes de negócio. O comportamento está documentado em [`docs/findings.md`](docs/findings.md).

> O projeto não espera rejeição por saldo insuficiente porque o domínio atual do ParaBank permite saldo negativo. A cobertura segue o comportamento implementado em vez de inventar uma regra inexistente.

---

## 🏗️ Arquitetura

```text
.
├── .github/
│   └── workflows/
│       └── e2e.yml
├── config/
│   └── settings.py
├── docs/
│   └── findings.md
├── features/
│   ├── environment.py
│   ├── login.feature
│   ├── registration.feature
│   ├── transfer.feature
│   └── steps/
│       ├── login_steps.py
│       ├── registration_steps.py
│       └── transfer_steps.py
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
├── behave.ini
├── compose.yaml
├── pyproject.toml
├── requirements.txt
├── run_tests.bat
└── run_tests.sh
```

### Page Object Model

Page Objects concentram seletores, ações e assertions de interface. Steps coordenam comportamento, massa e serviços sem acessar HTTP diretamente.

### Service layer

`ParabankApiClient` encapsula setup e consultas REST, incluindo contas e transações. O transporte HTTP é **direto e único**, pois a versão final executa exclusivamente contra o ParaBank local em Docker.

### Isolamento

Cada cenário recebe um novo `BrowserContext`. Usuários e contas são gerados dinamicamente e de forma exclusiva quando necessário.

---

## 🐳 Por que executar o ParaBank localmente?

A instância pública do ParaBank apresentou estado compartilhado e comportamentos instáveis durante o desenvolvimento. Isso impedia assertions determinísticas sobre contas, saldos e transações.

A versão final usa a imagem oficial `parasoft/parabank:baseline`. A Parasoft atualmente publica os canais `baseline`, `latest` e `feature`; `baseline` foi escolhido para evitar depender diretamente do canal `latest`.

```text
docker compose down --volumes --remove-orphans
                ↓
docker compose up -d
                ↓
healthcheck + readiness HTTP
                ↓
executa os testes
                ↓
gera evidências
                ↓
docker compose down --volumes --remove-orphans
```

Benefícios:

- banco limpo a cada execução;
- ausência de usuários compartilhados;
- estado previsível;
- massa exclusiva;
- assertions mais fortes;
- mesma topologia local e CI;
- nenhuma dependência do ambiente público ou de proxy externo.

---

## 🚀 Execução rápida

### Windows

```powershell
run_tests.bat
```

Se Python já estiver disponível:

```powershell
python scripts/run.py
```

### Linux / macOS

```bash
chmod +x run_tests.sh
./run_tests.sh
```

Ou:

```bash
python3 scripts/run.py
```

Detalhes do bootstrap: [`DOCKER_SETUP.md`](DOCKER_SETUP.md).

---

## ⚙️ Configuração

O `.env` contém apenas configuração de ambiente/SUT e timeouts. Browser e modo de execução são opções do runner, não configurações persistidas no `.env`.

Exemplo:

```dotenv
LOCAL_BASE_URL=http://localhost:8080/parabank
LOCAL_STARTUP_TIMEOUT_SECONDS=180
PW_TIMEOUT_MS=10000
PW_NAVIGATION_TIMEOUT_MS=15000
REQUEST_TIMEOUT_SECONDS=30
BLOCK_NONESSENTIAL_RESOURCES=true
UI_SCENARIO_DELAY_SECONDS=0
```

Browser e modo visual:

```bash
python scripts/run.py --browser firefox
python scripts/run.py --headed
```

---

## 🧪 Comandos úteis

Suíte completa:

```bash
python scripts/run.py
```

Por domínio:

```bash
python scripts/run.py --scope login
python scripts/run.py --scope registration
python scripts/run.py --scope transfer
```

Smoke:

```bash
python scripts/run.py --tags "@smoke"
```

Cross-browser:

```bash
python scripts/run.py --browser firefox
python scripts/run.py --browser webkit
```

Manter o ambiente ativo:

```bash
python scripts/run.py --keep-environment
```

---

## 📊 Allure Report

Resultados:

```text
reports/allure-results
```

Relatório HTML:

```text
reports/allure-report
```

Os wrappers podem gerar e abrir o relatório padrão do Allure ao final da execução. Em falhas de step, uma screenshot é anexada automaticamente.

---

## 🔄 CI/CD

Workflow:

```text
.github/workflows/e2e.yml
```

### Pull Request para `main`

```text
checkout
  ↓
Python 3.12
  ↓
Ruff
  ↓
behave --dry-run
  ↓
Docker / Compose
  ↓
Playwright Chromium
  ↓
ParaBank local + banco limpo
  ↓
regressão completa
  ↓
Allure artifacts
  ↓
quality gate
```

A regressão completa em Chromium é o quality gate do PR.

### Push em `main`

```text
                    ┌── Full Regression / Chromium
merge em main ──────┼── Smoke / Firefox
                    └── Smoke / WebKit
```

O job de execução de testes possui apenas permissões de leitura. `pages: write` e `id-token: write` ficam restritos ao job responsável por publicar o Allure em GitHub Pages.

### Execução manual

`workflow_dispatch` permite escolher escopo (`full`, `smoke`, `login`, `registration`, `transfer`) e browser (`chromium`, `firefox`, `webkit`).

---

## ✅ Boas práticas aplicadas

- cenários independentes;
- cobertura orientada a risco;
- BDD focado em comportamento;
- POM para abstração da interface;
- API-first para pré-condições técnicas;
- HTTP encapsulado na camada de serviço;
- validação backend após operações críticas;
- dados dinâmicos;
- isolamento de sessão;
- `Decimal` para valores monetários;
- polling com deadline para consistência;
- janela de estabilização para assertions negativas;
- ambiente determinístico e descartável;
- auto-wait e assertions do Playwright;
- Ruff e dry-run de BDD no CI;
- evidências automáticas;
- execução reproduzível local/CI.

---

## 📈 Resultado de referência

Regressão completa esperada:

```text
3 features
24 scenarios
0 failed
```

O número de steps pode evoluir conforme refatorações internas sem alterar a cobertura funcional declarada.

---

<p align="center">
  Python · Playwright · Behave · Docker · Ruff · Allure · GitHub Actions
</p>
