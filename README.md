<h1 align="center">ParaBank Automation BDD 2.0</h1>

<p align="center">
  Framework E2E com <strong>Python + Playwright + Behave</strong>, execução local em Docker<br/>
  e execução remota em <strong>AWS ECS/Fargate</strong> com Terraform, ECR, S3, CloudWatch e GitHub OIDC.
</p>

<p align="center">
  <a href="https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/container-runner.yml">
    <img src="https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/container-runner.yml/badge.svg?branch=release%2F2.0-aws" alt="Container Runner Validation" />
  </a>
  <a href="https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/terraform-validate.yml">
    <img src="https://github.com/fcramos296/parabank-automation-bdd/actions/workflows/terraform-validate.yml/badge.svg?branch=release%2F2.0-aws" alt="Terraform Validation" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Playwright-1.62-2EAD33?logo=playwright&logoColor=white" alt="Playwright" />
  <img src="https://img.shields.io/badge/BDD-Behave-6A5ACD" alt="Behave BDD" />
  <img src="https://img.shields.io/badge/AWS-ECS%20Fargate-FF9900?logo=amazonaws&logoColor=white" alt="AWS ECS Fargate" />
  <img src="https://img.shields.io/badge/IaC-Terraform-844FBA?logo=terraform&logoColor=white" alt="Terraform" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License" />
</p>

---

## 📌 Versionamento do projeto

O repositório mantém duas linhas independentes:

| Versão | Branch | Objetivo |
| --- | --- | --- |
| **1.x** | `main` | versão estável com execução local em Docker e pipeline original |
| **2.0** | `release/2.0-aws` | versão cloud com runner containerizado e execução em AWS ECS/Fargate |

A versão 2.0 **não será mergeada na `main`**. As duas implementações permanecem disponíveis e podem evoluir de forma independente.

A antiga branch `feat/aws-fargate-e2e` representa o histórico de desenvolvimento da versão AWS. A branch mantida para a linha 2.0 é `release/2.0-aws`.

---

## 📌 Sobre o projeto

O projeto automatiza os fluxos de **Login/Logout**, **Registro de Usuário** e **Transferência de Fundos** do ParaBank.

A solução foi construída como um framework de QA Automation sustentável, com:

- isolamento de dados por cenário;
- Page Object Model;
- pré-condições via API;
- validações UI + backend;
- ambiente determinístico e descartável;
- execução local e containerizada;
- quality gates em CI/CD;
- evidências Allure;
- infraestrutura AWS definida como código.

A versão 2.0 preserva a cobertura funcional já estabilizada e adiciona uma segunda camada de execução orientada a cloud.

---

## ✨ Destaques

- **24 cenários E2E** orientados a risco e regra de negócio;
- massa exclusiva e dinâmica por cenário;
- `BrowserContext` independente por cenário;
- API-first para pré-condições técnicas;
- validações cruzadas entre interface e backend;
- `Decimal` para valores monetários;
- polling com deadline em vez de sleeps fixos;
- ParaBank descartável em Docker;
- runner Playwright/Behave containerizado;
- validação local do runner com Docker Compose;
- Terraform para infraestrutura AWS;
- autenticação GitHub → AWS por OIDC, sem access keys persistentes;
- runner publicado em Amazon ECR;
- execução efêmera em Amazon ECS/Fargate;
- logs em CloudWatch;
- resultados Allure persistidos em S3 e publicados como artifact do GitHub Actions;
- quality gate baseado no exit code real do container de testes.

---

## 🧰 Stack

| Tecnologia | Responsabilidade |
| --- | --- |
| **Python** | linguagem principal do framework |
| **Playwright** | automação web e assertions de interface |
| **Behave / Gherkin** | BDD e especificação dos comportamentos |
| **Requests** | setup e validações de backend |
| **Pydantic Settings** | configuração do ambiente e timeouts |
| **Docker / Compose** | ambiente local e validação do runner containerizado |
| **Ruff** | análise estática e formatação |
| **Allure** | evidências e resultados de execução |
| **GitHub Actions** | CI/CD e orquestração da execução AWS |
| **Terraform** | infraestrutura como código |
| **Amazon ECR** | registry da imagem do runner |
| **Amazon ECS/Fargate** | execução efêmera dos testes |
| **Amazon S3** | persistência de resultados Allure |
| **CloudWatch Logs** | logs dos containers |
| **GitHub OIDC / IAM** | autenticação federada entre GitHub Actions e AWS |

---

## 🧠 Estratégia de testes

A automação separa claramente pré-condição, comportamento e validação persistida:

```text
pré-condição técnica      → API / backend
comportamento do usuário  → UI / Playwright
efeito persistido         → API / backend
evidência                 → Allure
```

Isso evita executar pela interface etapas que não pertencem ao comportamento em teste e reduz tempo, acoplamento e flakiness.

### 🔐 Login e Logout — 10 cenários

Cobertura principal:

- login válido;
- persistência de sessão;
- recuperação após credencial inválida;
- usuário inexistente;
- senha incorreta;
- campos vazios;
- logout;
- bloqueio de área protegida após logout.

### 👤 Registro de Usuário — 6 cenários

Cobertura principal:

- cadastro válido;
- persistência dos dados;
- autenticação backend do cliente criado;
- criação automática da conta `CHECKING`;
- saldo inicial;
- telefone opcional;
- boundaries de username/senha;
- obrigatoriedade dos campos;
- confirmação de senha divergente;
- username duplicado.

### 💸 Transferência de Fundos — 8 cenários

Cobertura principal:

- transferência válida;
- valor mínimo `0.01`;
- transferência reversa;
- transferência de todo o saldo;
- validação de saldo final;
- isolamento das contas exibidas;
- entradas inválidas;
- verificação das transações debit/credit no backend.

Os casos conhecidos de entrada monetária inválida permanecem documentados em [`docs/findings.md`](docs/findings.md).

---

## 🏗️ Arquitetura 2.0

```text
GitHub Actions
      │
      │ OIDC
      ▼
AWS IAM Role
      │
      ├──────────────► Amazon ECR
      │                   │
      │                   ▼
      │              test runner image
      │
      ▼
Amazon ECS / Fargate
      │
      ├── container: parabank
      │
      └── container: tests
              │
              ├────────► CloudWatch Logs
              │
              └────────► Amazon S3 / Allure
                              │
                              ▼
                      GitHub Actions artifact
```

Os containers `parabank` e `tests` executam na mesma task Fargate. O runner acessa o SUT por:

```text
http://localhost:8080/parabank
```

Por isso a aplicação não precisa ser exposta por load balancer ou regra de entrada.

---

## 📁 Estrutura relevante

```text
.
├── .github/
│   └── workflows/
│       ├── aws-fargate-e2e.yml
│       ├── container-runner.yml
│       ├── e2e.yml
│       └── terraform-validate.yml
├── config/
├── docs/
│   ├── AWS_FARGATE_RUNNER.md
│   └── findings.md
├── features/
├── pages/
├── services/
├── utils/
├── scripts/
│   ├── run.py
│   └── run_container.py
├── infra/
│   └── terraform/
├── Dockerfile.tests
├── compose.yaml
├── compose.runner.yaml
├── behave.ini
├── pyproject.toml
└── requirements.txt
```

---

## 🐳 Execução local tradicional

A execução local da suíte continua disponível:

### Windows

```powershell
run_tests.bat
```

Ou:

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

## 📦 Validação do runner containerizado

A mesma suíte pode ser executada usando o container de testes usado como base da arquitetura AWS.

Suíte completa:

```bash
docker compose -f compose.runner.yaml up --build --abort-on-container-exit --exit-code-from tests
```

Smoke:

```bash
docker compose -f compose.runner.yaml up -d parabank
docker compose -f compose.runner.yaml run --rm tests --tags "@smoke"
docker compose -f compose.runner.yaml down --volumes --remove-orphans
```

Resultados locais:

```text
reports/allure-results
```

---

## ☁️ Infraestrutura AWS

A definição Terraform está em:

```text
infra/terraform/
```

Principais recursos:

- VPC dedicada;
- duas subnets públicas;
- security group sem ingress;
- ECR;
- ECS cluster;
- task definition Fargate;
- CloudWatch log group;
- S3 privado para Allure;
- ECS execution role;
- ECS task role;
- GitHub Actions role;
- GitHub OIDC provider.

Detalhes: [`infra/terraform/README.md`](infra/terraform/README.md).

---

## 🔐 GitHub OIDC

A versão 2.0 não utiliza AWS access key e secret key persistentes no GitHub Actions.

O workflow solicita um token OIDC do GitHub e assume uma IAM role criada pelo Terraform.

A trust policy está restrita a:

```text
refs/heads/release/2.0-aws
```

A `main` não está autorizada a assumir a role AWS da versão 2.0.

> Se a infraestrutura AWS existente ainda estiver configurada com a antiga branch de desenvolvimento, execute um novo `terraform apply` uma vez para atualizar a trust policy real da IAM role.

---

## 🚀 Execução AWS Fargate

Workflow:

```text
.github/workflows/aws-fargate-e2e.yml
```

A execução é manual via `workflow_dispatch`.

Entradas disponíveis:

- expressão de tags do Behave;
- browser: `chromium`, `firefox` ou `webkit`.

Fluxo:

```text
checkout
  ↓
OIDC / AssumeRole
  ↓
login no ECR
  ↓
build Dockerfile.tests
  ↓
push da imagem imutável
  ↓
nova revisão da ECS task definition
  ↓
ecs run-task
  ↓
ParaBank + Playwright/Behave
  ↓
exit code do container tests
  ↓
CloudWatch logs
  ↓
Allure no S3
  ↓
artifact no GitHub Actions
  ↓
quality gate
```

A execução só passa quando:

1. o container `tests` finaliza com exit code `0`;
2. os resultados Allure são recuperados com sucesso.

---

## 🔄 CI/CD da versão 2.0

### Container Runner Validation

```text
.github/workflows/container-runner.yml
```

Executa na `release/2.0-aws` quando arquivos relacionados ao runner são alterados.

Valida:

- build do container;
- inicialização do ParaBank;
- smoke suite;
- geração de evidências;
- cleanup do ambiente.

### Terraform Validation

```text
.github/workflows/terraform-validate.yml
```

Executa:

```bash
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate -no-color
```

O workflow não aplica infraestrutura.

### AWS Fargate E2E

```text
.github/workflows/aws-fargate-e2e.yml
```

Orquestra a execução real na AWS e aplica o quality gate remoto.

---

## 📊 Evidências

### Local

```text
reports/allure-results
reports/allure-report
```

### AWS

- logs: CloudWatch Logs;
- resultados Allure: bucket privado S3;
- artifact final: GitHub Actions.

A retenção dos recursos AWS é configurável via Terraform.

---

## 🛡️ Segurança aplicada

- nenhuma access key AWS persistente no GitHub;
- OIDC limitado à branch `release/2.0-aws`;
- `iam:PassRole` limitado às roles ECS do projeto;
- S3 com acesso público bloqueado;
- criptografia server-side no bucket de evidências;
- security group sem regras de entrada;
- execução efêmera no Fargate;
- imagens ECR imutáveis;
- permissões IAM reduzidas ao necessário sempre que há suporte a resource-level permissions.

---

## ✅ Boas práticas aplicadas

- cenários independentes;
- cobertura orientada a risco;
- BDD focado em comportamento;
- POM para abstração da interface;
- API-first para pré-condições;
- HTTP encapsulado na camada de serviço;
- validação backend após operações críticas;
- dados dinâmicos;
- isolamento de sessão;
- `Decimal` para valores monetários;
- polling com deadline;
- ambiente determinístico;
- auto-wait do Playwright;
- quality gates locais e cloud;
- infraestrutura como código;
- autenticação federada com OIDC;
- evidências automáticas.

---

## 📈 Resultado funcional de referência

Regressão completa esperada:

```text
3 features
24 scenarios
0 failed
```

O número de steps pode evoluir conforme refatorações internas sem alterar a cobertura funcional declarada.

---

## 📚 Documentação adicional

- [`docs/AWS_FARGATE_RUNNER.md`](docs/AWS_FARGATE_RUNNER.md) — arquitetura e operação AWS/Fargate;
- [`infra/terraform/README.md`](infra/terraform/README.md) — provisionamento e atualização da infraestrutura;
- [`docs/findings.md`](docs/findings.md) — comportamentos e defeitos conhecidos do ParaBank;
- [`DOCKER_SETUP.md`](DOCKER_SETUP.md) — preparação do ambiente local.

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License**. Consulte [`LICENSE`](LICENSE).

O ParaBank é um sistema de demonstração da Parasoft e permanece sujeito aos termos aplicáveis do respectivo fornecedor.

---

<p align="center">
  Python · Playwright · Behave · Docker · AWS · ECS/Fargate · Terraform · Allure · GitHub Actions
</p>
