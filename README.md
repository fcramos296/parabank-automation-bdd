<p align="center">
  <img src="assets/topaz-logo.png" alt="Topaz" width="380" />
</p>

<h1 align="center">ParaBank Automation BDD</h1>

<p align="center">
  Automação funcional E2E com ambiente determinístico, validações UI + API e pipeline CI/CD.
</p>

<p align="center">
  <a href="https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/e2e.yml">
    <img src="https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/e2e.yml/badge.svg" alt="ParaBank E2E" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Playwright-1.62-2EAD33?logo=playwright&logoColor=white" alt="Playwright" />
  <img src="https://img.shields.io/badge/BDD-Behave-6A5ACD" alt="Behave BDD" />
  <img src="https://img.shields.io/badge/Docker-Local-2496ED?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Allure-3.17-FF6A00" alt="Allure 3" />
</p>

---

## 📌 Sobre o projeto

Este projeto automatiza os fluxos de **Login/Logout**, **Registro de Usuário** e **Transferência de Fundos** do ParaBank utilizando **Python + Playwright + Behave**, com cenários escritos em **Gherkin/BDD**, arquitetura baseada em **Page Object Model**, preparação de massa via backend e validações cruzadas entre interface e API.

A proposta não é apenas automatizar cliques. O projeto foi estruturado para demonstrar uma abordagem de QA mais próxima de um cenário real: isolamento de dados, ambiente reproduzível, evidências de falha, assertions de persistência e pipeline de qualidade.

### ✨ Destaques

- **24 cenários E2E** focados em risco e regra de negócio;
- **117 steps** validados na regressão final em Chromium;
- dados exclusivos e dinâmicos por cenário;
- pré-condições preparadas via API quando o comportamento em teste não é a criação da massa;
- validação do resultado visível na UI e do efeito persistido no backend;
- ambiente ParaBank descartável com Docker;
- `BrowserContext` novo por cenário;
- screenshots, URL e erros de console anexados ao Allure em falhas;
- relatório **Allure 3 Awesome** personalizado com identidade visual Topaz;
- CI/CD com regressão completa e smoke cross-browser;
- execução reproduzível em Windows, Linux, macOS e GitHub Actions.

---

## 🧰 Stack

| Tecnologia | Responsabilidade |
| --- | --- |
| **Python** | Linguagem principal do framework |
| **Playwright** | Automação e assertions da interface web |
| **Behave** | Runner BDD |
| **Gherkin** | Especificação funcional dos cenários |
| **Requests** | Setup e validações de backend |
| **Pydantic Settings** | Configuração centralizada do ambiente |
| **Docker / Compose** | Ambiente ParaBank local e descartável |
| **Allure 3** | Evidências e relatório visual |
| **GitHub Actions** | CI/CD e quality gates |

---

## 🧪 Cobertura

A suíte cobre exclusivamente os três fluxos definidos para a entrega.

### 🔐 Login e Logout — 10 cenários

Cobertura principal:

- login com credenciais válidas;
- persistência da sessão após reload;
- login válido após uma tentativa anterior com senha incorreta;
- usuário inexistente;
- senha incorreta para usuário existente;
- username vazio;
- senha vazia;
- username e senha vazios;
- logout encerrando efetivamente a sessão;
- bloqueio de acesso direto a área protegida após logout.

Quando o comportamento em teste é autenticação, o usuário é criado previamente via backend. Dessa forma, falhas no cadastro não contaminam os testes de login.

### 👤 Registro de Usuário — 6 cenários

Cobertura principal:

- cadastro válido com todos os campos;
- persistência dos dados do cliente;
- autenticação backend do cliente recém-cadastrado;
- criação automática da conta inicial `CHECKING`;
- validação do saldo inicial `515.50`;
- cadastro sem telefone opcional;
- persistência do telefone vazio;
- username e senha com exatamente 20 caracteres, validando o limite suportado;
- validação conjunta dos campos obrigatórios;
- confirmação de senha divergente;
- username duplicado.

Quando registro é o comportamento em teste, a criação do usuário é feita pela **UI**. A API é utilizada depois da ação para verificar persistência e efeitos do fluxo.

### 💸 Transferência de Fundos — 8 cenários

Cada cenário recebe um cliente exclusivo com duas contas próprias.

Cobertura principal:

- transferência positiva com valor comum;
- menor valor monetário com duas casas decimais: `0.01`;
- transferência no sentido inverso entre as contas;
- transferência de todo o saldo disponível;
- saldo da conta de origem igual a zero após transferência integral;
- dropdowns exibindo apenas contas do cliente autenticado;
- conta pertencente a outro cliente ausente dos seletores;
- valor vazio;
- valor textual;
- formato monetário com vírgula;
- confirmação de valor, origem e destino na UI;
- lançamento `Debit / Funds Transfer Sent` na origem;
- lançamento `Credit / Funds Transfer Received` no destino;
- validação exata dos saldos após operações válidas;
- saldos inalterados em operações rejeitadas;
- ausência de transações criadas em operações rejeitadas.

> **Nota de domínio:** o ParaBank permite saldo negativo na implementação atual. Por isso, a suíte não cria artificialmente uma regra de rejeição por saldo insuficiente que o produto não implementa.

---

## 🏗️ Arquitetura

```text
Gherkin / Features
        │
        ▼
Behave Steps
        │
        ├──────────────► API Client / Test Data
        │                       │
        ▼                       ▼
Page Objects              Backend ParaBank
        │                       │
        └──────────────┬────────┘
                       ▼
             Validação UI + Estado
```

### Organização de responsabilidades

- **Features** descrevem o comportamento esperado em linguagem de negócio;
- **Steps** coordenam fluxo, massa e assertions;
- **Page Objects** encapsulam seletores e interações da UI;
- **Services** centralizam chamadas ao backend;
- **Utils** concentram geração de dados reutilizáveis;
- **Environment hooks** controlam browser, isolamento e evidências;
- **Runner** prepara dependências, Docker, execução e teardown.

---

## 📁 Estrutura do projeto

```text
.
├── .github/
│   └── workflows/
│       └── e2e.yml
├── assets/
│   └── topaz-logo.png
├── config/
│   └── settings.py
├── features/
│   ├── steps/
│   │   ├── login_steps.py
│   │   ├── registration_steps.py
│   │   └── transfer_steps.py
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
├── allurerc.mjs
├── behave.ini
├── compose.yaml
├── requirements.txt
├── run_tests.bat
└── run_tests.sh
```

---

## 🚀 Execução rápida

### Windows

A forma mais simples é utilizar o runner interativo:

```powershell
run_tests.bat
```

Ou executar diretamente:

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

Os wrappers foram preparados para reduzir o setup manual em uma máquina nova.

### Windows

O fluxo pode preparar, quando necessário e autorizado:

- Python 3.10+;
- WSL 2;
- recursos de virtualização necessários ao WSL;
- Docker Desktop;
- Docker Compose;
- ambiente virtual Python;
- dependências do projeto;
- browser Playwright;
- container ParaBank.

Algumas alterações do Windows podem exigir reinicialização. Virtualização Intel VT-x / AMD-V desabilitada no BIOS/UEFI precisa ser habilitada manualmente.

### Linux

Há suporte para instalação via gerenciadores compatíveis com:

- `apt`;
- `dnf`;
- `yum`;
- `pacman`;
- `zypper`.

O runner pode preparar Python, venv, Docker Engine, Compose, dependências e Playwright.

### macOS

O fluxo pode preparar Python, Homebrew quando necessário, Docker Desktop, dependências e Playwright.

Detalhes adicionais: [`DOCKER_SETUP.md`](DOCKER_SETUP.md).

---

## 🐳 Por que executar o ParaBank localmente?

Durante a homologação da automação, o ambiente público apresentou comportamento inconsistente em operações dependentes de contas de clientes recém-cadastrados, além de possuir estado compartilhado entre usuários.

Para uma suíte de regressão confiável, depender desse ambiente exigiria aceitar interferência externa ou criar workarounds que enfraqueceriam as assertions.

A solução adotada foi utilizar a imagem oficial do ParaBank em Docker e recriar o banco antes de cada execução.

### Benefícios

- ambiente limpo e previsível;
- ausência de dependência de massa compartilhada;
- clientes e contas exclusivos;
- saldos determinísticos;
- assertions mais fortes;
- nenhuma dependência de proxy ou segredo externo;
- mesmo comportamento de execução local e no CI;
- teardown automático após a suíte.

### Ciclo padrão

```text
docker compose down --volumes --remove-orphans
                ↓
docker compose up -d
                ↓
aguarda health/readiness do ParaBank
                ↓
executa a suíte
                ↓
gera evidências
                ↓
docker compose down --volumes --remove-orphans
```

Para manter o ambiente ativo após os testes:

```bash
python scripts/run.py --keep-environment
```

Aplicação local:

```text
http://localhost:8080/parabank
```

---

## 🎯 Comandos úteis

| Objetivo | Comando |
| --- | --- |
| Suíte completa | `python scripts/run.py` |
| Login/Logout | `python scripts/run.py --scope login` |
| Registro | `python scripts/run.py --scope registration` |
| Transferência | `python scripts/run.py --scope transfer` |
| Smoke | `python scripts/run.py --tags "@smoke"` |
| Browser visível | `python scripts/run.py --headed` |
| Firefox | `python scripts/run.py --browser firefox` |
| WebKit | `python scripts/run.py --browser webkit` |
| Manter ParaBank ativo | `python scripts/run.py --keep-environment` |
| Permitir bootstrap Docker | `python scripts/run.py --install-docker` |
| Impedir instalação Docker | `python scripts/run.py --no-docker-install` |

---

## 🧬 Estratégia de dados

A massa é criada dinamicamente para evitar dependência entre execuções.

```text
Cenário
  ↓
Cliente exclusivo
  ↓
Pré-condições via backend
  ↓
Ação funcional pela UI
  ↓
Validação visual
  ↓
Validação de persistência / saldo / transação via API
```

Princípios utilizados:

- username e SSN únicos;
- contas exclusivas para transferência;
- nenhum cenário depende da execução de outro;
- nenhuma sessão de navegador é compartilhada;
- preparação via API evita navegar pela UI apenas para montar pré-condição.

---

## 🧱 Page Object Model

Os Page Objects concentram:

- seletores;
- ações de interface;
- esperas específicas da tela;
- assertions visuais associadas à página.

As steps do Behave ficam responsáveis por expressar o comportamento e coordenar Page Objects, dados e serviços.

Isso reduz duplicação e evita espalhar detalhes de UI pelas features.

---

## 📊 Allure Report personalizado

O projeto utiliza **Allure Report 3** com o **Awesome plugin**.

Configuração:

```text
allurerc.mjs
```

O relatório foi personalizado com:

- logo Topaz;
- tema escuro;
- interface em português;
- título próprio do projeto;
- informações de projeto, ambiente, escopo e browser;
- labels de `epic`, `feature`, browser, ambiente, layer e severity;
- identificação do GitHub Actions quando gerado pelo CI;
- categorias específicas para timeout, falha funcional e falha de automação/infraestrutura;
- metadata do ambiente de execução;
- screenshot automático em falhas;
- URL atual anexada em falhas;
- erros do console do navegador anexados quando disponíveis.

Resultados brutos:

```text
reports/allure-results
```

Gerar o HTML manualmente:

```bash
allure generate \
  reports/allure-results \
  --config ./allurerc.mjs \
  --output reports/allure-report
```

Abrir o relatório:

```bash
allure open reports/allure-report
```

Os runners interativos também oferecem a geração do relatório ao final da execução.

---

## 🔄 CI/CD

Workflow:

```text
.github/workflows/e2e.yml
```

### Pull Request → `main`

```text
Checkout
   ↓
Python 3.12
   ↓
Docker / Compose validation
   ↓
Dependencies
   ↓
Python compileall
   ↓
Playwright Chromium
   ↓
ParaBank Docker + banco limpo
   ↓
Regressão completa
   ↓
Allure personalizado
   ↓
Quality Gate
```

A regressão completa em Chromium é o **quality gate** do Pull Request.

### Push → `main`

Após merge, o pipeline executa:

```text
                ┌─ Full Regression / Chromium
main ───────────┼─ Smoke / Firefox
                └─ Smoke / WebKit
```

Quando todos os gates ficam verdes, o relatório da regressão pode ser publicado em **GitHub Pages**, caso Pages esteja habilitado no repositório.

### Execução manual

O `workflow_dispatch` permite escolher:

- `full`;
- `smoke`;
- `login`;
- `registration`;
- `transfer`;

E o browser:

- Chromium;
- Firefox;
- WebKit.

O pipeline não depende de secrets de terceiros.

---

## 🛡️ Boas práticas aplicadas

- ✅ testes independentes;
- ✅ dados dinâmicos e exclusivos;
- ✅ API-first para preparação de pré-condições;
- ✅ UI focada no comportamento realmente testado;
- ✅ POM para reduzir acoplamento com seletores;
- ✅ `BrowserContext` isolado por cenário;
- ✅ auto-wait do Playwright em vez de sleeps funcionais fixos;
- ✅ assertions de backend após operações críticas;
- ✅ validação de ausência de efeitos colaterais em cenários negativos;
- ✅ ambiente limpo por execução;
- ✅ teardown automático;
- ✅ mensagens de erro diagnósticas;
- ✅ evidências automáticas no Allure;
- ✅ dependências principais versionadas;
- ✅ CI reproduzindo a mesma arquitetura usada localmente;
- ✅ cobertura orientada a risco e comportamento, não à quantidade de testes.

---

## ✅ Validação final

A regressão da versão final foi validada no GitHub Actions em Chromium com:

```text
3 features passed
24 scenarios passed
117 steps passed
0 failed
0 skipped
```

Além da regressão principal, o pipeline está preparado para validar o smoke em Firefox e WebKit após integração em `main`.

---

## 👨‍💻 Autor

**Fernando Ramos**  
QA Automation / Software Quality

Projeto desenvolvido como entrega técnica, com foco em arquitetura de automação, estratégia de testes, confiabilidade e manutenibilidade.
