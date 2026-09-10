<p align="center">
  <img src="assets/topaz-readme.jpeg" alt="Topaz | Stefanini" width="334" />
</p>

<h1 align="center">ParaBank Automation BDD</h1>

<p align="center">
  Framework E2E com <strong>Python + Playwright + Behave</strong>, ambiente determinístico em Docker,<br/>
  validações UI + API, relatórios Allure e CI/CD cross-browser.
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

A solução foi estruturada para demonstrar uma estratégia de automação sustentável, com **isolamento de dados**, **pré-condições via API**, **validação de efeitos persistidos**, **ambiente reproduzível**, **evidências de falha** e **quality gates em CI/CD**.

### ✨ Destaques

- **24 cenários E2E** orientados a risco e regra de negócio;
- **117 steps** na regressão completa de referência;
- execução contra uma instância limpa do ParaBank em Docker;
- massa exclusiva e dinâmica por cenário;
- Page Object Model para desacoplar UI e comportamento;
- preparação de pré-condições via backend quando apropriado;
- validações cruzadas entre interface e API;
- `BrowserContext` independente por cenário;
- screenshot anexado ao Allure em caso de falha;
- regressão completa em Chromium como quality gate;
- smoke cross-browser em Firefox e WebKit;
- bootstrap para Windows, Linux e macOS.

---

## 🧰 Stack

| Tecnologia | Responsabilidade |
| --- | --- |
| **Python** | Linguagem principal do framework |
| **Playwright** | Automação web e assertions de interface |
| **Behave** | Runner BDD |
| **Gherkin** | Especificação dos comportamentos |
| **Requests** | Setup e validações de backend |
| **Pydantic Settings** | Configuração centralizada |
| **Docker / Compose** | Ambiente ParaBank descartável |
| **Allure Report** | Evidências e relatório HTML |
| **GitHub Actions** | CI/CD e quality gates |

---

## 🧠 Estratégia de testes

A automação segue uma separação clara de responsabilidades:

```text
pré-condição técnica      → API / backend
comportamento do usuário  → UI / Playwright
efeito persistido         → API / backend
evidência                  → Allure
```

Isso evita executar pela interface etapas que não são o comportamento em teste e reduz tempo, acoplamento e flakiness.

### 🔐 Login e Logout — 10 cenários

Cobertura:

- login válido;
- persistência da sessão após reload;
- recuperação após uma tentativa com senha incorreta;
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
- validação do saldo inicial `515.50`;
- telefone opcional não informado;
- persistência do telefone vazio;
- username e senha no boundary de 20 caracteres;
- validação conjunta de campos obrigatórios;
- confirmação de senha divergente;
- username duplicado.

Quando **registro** é o comportamento em teste, o cadastro ocorre pela interface. A API é utilizada somente depois da ação para confirmar os efeitos persistidos.

### 💸 Transferência de Fundos — 8 cenários

Cobertura:

- transferência com valor monetário comum;
- boundary mínimo de `0.01`;
- transferência no sentido inverso entre duas contas;
- transferência de todo o saldo disponível;
- saldo de origem final igual a `0.00`;
- seletores exibindo somente contas do cliente autenticado;
- exclusão de conta pertencente a outro cliente;
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
erro funcional
      ↓
saldo origem inalterado
      ↓
saldo destino inalterado
      ↓
nenhuma transação criada
```

> O projeto não cria uma expectativa de rejeição por saldo insuficiente porque a implementação atual do ParaBank permite saldo negativo. A cobertura segue o comportamento de domínio existente em vez de inventar uma regra não implementada.

---

## 🏗️ Arquitetura

```text
.
├── .github/
│   └── workflows/
│       └── e2e.yml
├── assets/
│   └── topaz-readme.jpeg
├── config/
│   └── settings.py
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
├── requirements.txt
├── run_tests.bat
└── run_tests.sh
```

### Page Object Model

Os Page Objects concentram seletores, ações e assertions específicas da interface. As steps do Behave descrevem o comportamento e coordenam Page Objects, dados e serviços, sem espalhar detalhes de UI pelas features.

### Isolamento

Cada cenário recebe um novo `BrowserContext` do Playwright. Dados de negócio são gerados dinamicamente e usuários/contas são exclusivos quando necessário.

---

## 🐳 Por que executar o ParaBank localmente?

Durante o desenvolvimento, a instância pública do ParaBank apresentou comportamento instável e estado compartilhado entre usuários. Isso dificultava distinguir defeitos reais de interferência externa e impedia assertions determinísticas sobre contas, saldos e transações.

A versão final utiliza a imagem oficial do ParaBank em Docker:

```text
docker compose down --volumes --remove-orphans
                ↓
docker compose up -d
                ↓
aguarda ParaBank ficar disponível
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
- maior força nas assertions;
- mesma topologia de execução local e CI;
- nenhuma dependência do ambiente público ou de serviços de terceiros.

---

## 🚀 Execução rápida

### Windows

Experiência guiada:

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

---

## ⚙️ Bootstrap automático

Os wrappers reduzem ao mínimo os pré-requisitos de uma máquina nova.

### Windows

O fluxo pode preparar, mediante autorização:

- Python 3.10+;
- WSL 2;
- Virtual Machine Platform;
- atualização do WSL;
- Docker Desktop;
- Docker Compose;
- `.venv`;
- dependências Python;
- browser do Playwright;
- container ParaBank.

Se o Windows exigir reinicialização após habilitar WSL/virtualização, o runner encerra de forma controlada e orienta a nova execução.

> Virtualização Intel VT-x / AMD-V desabilitada no BIOS/UEFI não pode ser habilitada com segurança pelo projeto; nesse caso o requisito é informado ao usuário.

### Linux

O fluxo suporta caminhos baseados em `apt`, `dnf`, `yum`, `pacman` e `zypper` para preparar Python e dependências de sistema. Docker Engine e Compose plugin são utilizados nativamente.

### macOS

O fluxo pode preparar Python, Homebrew quando necessário, Docker Desktop, Compose, Playwright e o ParaBank. A primeira inicialização do Docker Desktop pode exigir permissões do sistema ou aceite dos termos do produto.

Detalhes adicionais: [`DOCKER_SETUP.md`](DOCKER_SETUP.md).

---

## 🧪 Comandos úteis

Suíte completa:

```bash
python scripts/run.py
```

Login/logout:

```bash
python scripts/run.py --scope login
```

Registro:

```bash
python scripts/run.py --scope registration
```

Transferência:

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

Manter o ParaBank ativo após os testes:

```bash
python scripts/run.py --keep-environment
```

Autorizar instalação automática de Docker:

```bash
python scripts/run.py --install-docker
```

Impedir instalação automática de Docker:

```bash
python scripts/run.py --no-docker-install
```

---

## 📊 Allure Report

Os testes geram resultados compatíveis com Allure em:

```text
reports/allure-results
```

Os wrappers `run_tests.bat` e `run_tests.sh` podem gerar o relatório HTML padrão ao final da execução. Em caso de falha de um step, a suíte anexa automaticamente uma screenshot da página ao resultado.

HTML gerado:

```text
reports/allure-report
```

Geração manual:

```bash
allure generate reports/allure-results --output reports/allure-report
```

Abrir o relatório:

```bash
allure open reports/allure-report
```

O CI também armazena tanto os resultados brutos quanto o relatório HTML como artifacts quando disponíveis.

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
Docker / Compose
  ↓
dependências
  ↓
compileall
  ↓
Playwright Chromium
  ↓
ParaBank local + banco limpo
  ↓
regressão completa
  ↓
Allure Report
  ↓
quality gate
```

A regressão completa em Chromium funciona como **quality gate** do PR.

### Push em `main`

```text
                    ┌── Full Regression / Chromium
merge em main ──────┼── Smoke / Firefox
                    └── Smoke / WebKit
```

Quando todos os gates passam, o relatório Allure pode ser publicado via GitHub Pages, se Pages estiver habilitado no repositório.

### Execução manual

`workflow_dispatch` permite escolher:

- `full`;
- `smoke`;
- `login`;
- `registration`;
- `transfer`;
- Chromium;
- Firefox;
- WebKit.

O pipeline não depende de secrets ou serviços externos para acessar o SUT.

---

## ✅ Boas práticas aplicadas

- cenários independentes;
- cobertura orientada a risco;
- BDD focado em comportamento;
- POM para abstração da interface;
- API-first para pré-condições técnicas;
- validação backend após operações críticas;
- dados dinâmicos;
- isolamento de sessão;
- ambiente determinístico e descartável;
- ausência de sleeps fixos para sincronização funcional;
- auto-wait e assertions do Playwright;
- falhas com mensagens diagnósticas;
- evidências automáticas;
- execução reproduzível local/CI;
- regressão e smoke com responsabilidades distintas;
- nenhum workaround dependente do ambiente público.

---

## 📈 Resultado de referência

Regressão completa validada no pipeline:

```text
3 features passed
24 scenarios passed
117 steps passed
0 failed
```

---

<p align="center">
  Python · Playwright · Behave · Docker · Allure · GitHub Actions
</p>
