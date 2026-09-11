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
  <img src="https://img.shields.io/badge/Release-v2.0-blue" alt="Release v2.0" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License" />
</p>

---

## Status da versão 2.0

A versão **v2.0** está homologada para execução em AWS ECS/Fargate e é mantida na branch:

```text
release/2.0-aws
```

A release `v2.0` aponta para o commit homologado da linha AWS. A `main` continua representando a linha estável 1.x e não recebe merge automático da arquitetura cloud.

Homologação final da 2.0:

```text
AWS Fargate E2E #7
3 features passed
3 scenarios passed
16 steps passed
0 failed
Quality Gate passed
```

Além da execução Fargate, também foi validado um **clone limpo** do repositório usando o backend remoto do Terraform, sem cópia manual de state e sem novos imports.

---

## Versionamento do projeto

| Versão | Branch | Objetivo |
| --- | --- | --- |
| **1.x** | `main` | versão estável com execução local em Docker e pipeline original |
| **2.0** | `release/2.0-aws` | versão cloud com runner containerizado e execução em AWS ECS/Fargate |

A antiga branch `feat/aws-fargate-e2e` permanece apenas como histórico de desenvolvimento da versão AWS.

---

## Sobre o projeto

O projeto automatiza os fluxos de **Login/Logout**, **Registro de Usuário** e **Transferência de Fundos** do ParaBank.

A solução aplica práticas de QA Automation voltadas a manutenção, isolamento e confiabilidade:

- Page Object Model;
- BDD com Behave/Gherkin;
- pré-condições técnicas via API;
- validações UI + backend;
- massa exclusiva e dinâmica por cenário;
- `BrowserContext` independente por cenário;
- `Decimal` para valores monetários;
- polling com deadline em vez de sleeps fixos;
- execução local determinística com Docker;
- execução remota efêmera com AWS Fargate;
- quality gates em CI/CD;
- evidências Allure;
- infraestrutura como código com Terraform.

---

## Cobertura funcional

### Login e Logout — 10 cenários

Cobertura principal:

- login válido;
- persistência de sessão;
- recuperação após credencial inválida;
- usuário inexistente;
- senha incorreta;
- campos vazios;
- logout;
- bloqueio de área protegida após logout.

### Registro de Usuário — 6 cenários

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

### Transferência de Fundos — 8 cenários

Cobertura principal:

- transferência válida;
- valor mínimo `0.01`;
- transferência reversa;
- transferência de todo o saldo;
- validação de saldo final;
- isolamento das contas exibidas;
- entradas inválidas;
- verificação de débito/crédito no backend.

Total da regressão:

```text
3 features
24 scenarios
```

Comportamentos conhecidos do ParaBank permanecem registrados em [`docs/findings.md`](docs/findings.md).

---

## Stack

| Tecnologia | Responsabilidade |
| --- | --- |
| **Python** | linguagem principal do framework |
| **Playwright** | automação web e assertions de interface |
| **Behave / Gherkin** | BDD e especificação dos comportamentos |
| **Requests** | setup e validações de backend |
| **Pydantic Settings** | configuração e timeouts |
| **Docker / Compose** | ambiente local e runner containerizado |
| **Ruff** | lint e formatação |
| **Allure** | evidências de execução |
| **GitHub Actions** | CI/CD e orquestração AWS |
| **Terraform** | infraestrutura como código |
| **Amazon ECR** | registry da imagem do runner |
| **Amazon ECS/Fargate** | execução efêmera dos testes |
| **Amazon S3** | Allure e backend remoto do Terraform |
| **CloudWatch Logs** | logs dos containers |
| **GitHub OIDC / IAM** | autenticação federada GitHub → AWS |

---

## Estratégia de testes

A automação separa pré-condição, comportamento e validação persistida:

```text
pré-condição técnica      → API / backend
comportamento do usuário  → UI / Playwright
efeito persistido         → API / backend
evidência                 → Allure
```

Essa separação reduz tempo de execução, acoplamento e flakiness.

---

## Arquitetura 2.0

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

Os containers `parabank` e `tests` executam na mesma task Fargate. O runner acessa o SUT diretamente em:

```text
http://localhost:8080/parabank
```

Por isso não há necessidade de load balancer nem regra de entrada no security group.

---

## Estrutura relevante

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

## Execução local

### Windows

```powershell
run_tests.bat
```

ou:

```powershell
python scripts/run.py
```

### Linux / macOS

```bash
chmod +x run_tests.sh
./run_tests.sh
```

ou:

```bash
python3 scripts/run.py
```

---

## Runner containerizado

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

## Infraestrutura AWS

A infraestrutura da versão 2.0 está em:

```text
infra/terraform/
```

Principais recursos:

- VPC dedicada;
- duas subnets públicas;
- security group sem ingress;
- Amazon ECR;
- cluster ECS `parabank-qa-test`;
- task definition Fargate;
- CloudWatch log group;
- bucket S3 privado para Allure;
- ECS execution role;
- ECS task role;
- GitHub Actions role;
- GitHub OIDC provider.

A região utilizada pelo ambiente homologado é:

```text
us-east-1
```

No console AWS, a execução pode ser acompanhada em:

```text
ECS → Clusters → parabank-qa-test → Tasks
```

Logs:

```text
CloudWatch → Log groups → /ecs/parabank-qa-test
```

Detalhes adicionais: [`infra/terraform/README.md`](infra/terraform/README.md).

---

## Terraform state remoto

A versão 2.0 utiliza um backend remoto S3 dedicado para o Terraform, separado do bucket de evidências Allure.

O backend possui:

- criptografia server-side;
- versionamento;
- public access block;
- locking nativo via `use_lockfile = true`.

O state recuperado foi migrado para esse backend e o fluxo de clone limpo foi validado com sucesso.

### Clone novo

Depois que o backend já existe, não é necessário copiar `terraform.tfstate`, executar imports ou rodar novamente o bootstrap.

```powershell
git clone https://github.com/fcramos296/parabank-automation-bdd.git
cd parabank-automation-bdd
git switch release/2.0-aws

$env:AWS_PROFILE="parabank"

cd infra\terraform
terraform init
terraform plan
```

Resultado esperado em um ambiente sincronizado:

```text
No changes. Your infrastructure matches the configuration.
```

### Bootstrap do backend

O script `infra/terraform/bootstrap_backend.ps1` existe apenas para a criação/configuração inicial do bucket de state.

```powershell
$env:AWS_PROFILE="parabank"
powershell -ExecutionPolicy Bypass -File .\bootstrap_backend.ps1
```

Para migrar um state local existente:

```powershell
terraform init -migrate-state
```

Não combine `-migrate-state` com `-reconfigure`.

---

## GitHub OIDC

A versão 2.0 não utiliza AWS access key/secret key persistentes no GitHub Actions.

O workflow obtém um token OIDC do GitHub e assume a IAM role criada pelo Terraform.

A trust policy aplicada no ambiente homologado está restrita a:

```text
refs/heads/release/2.0-aws
```

A `main` não está autorizada a assumir a role AWS da versão 2.0.

---

## AWS Fargate E2E

Workflow:

```text
.github/workflows/aws-fargate-e2e.yml
```

A execução é manual via `workflow_dispatch` e permite informar:

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

A execução somente passa quando:

1. o container `tests` termina com exit code `0`;
2. os resultados Allure são recuperados do S3;
3. o quality gate final é aprovado.

### Homologação final

A execução `AWS Fargate E2E #7`, realizada na `release/2.0-aws`, validou:

- OIDC GitHub → AWS;
- login e push no ECR;
- criação de nova revisão da task definition;
- execução real em Fargate;
- ParaBank disponível em `localhost:8080/parabank`;
- smoke suite em Chromium;
- CloudWatch Logs;
- upload Allure para S3;
- download das evidências para GitHub Actions;
- Quality Gate.

Resultado funcional:

```text
3 features passed
3 scenarios passed
16 steps passed
0 failed
```

Artifact produzido:

```text
aws-fargate-allure-7
```

---

## CI/CD da versão 2.0

### Container Runner Validation

```text
.github/workflows/container-runner.yml
```

Valida:

- build do runner;
- inicialização do ParaBank;
- smoke suite;
- evidências;
- cleanup.

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

Esse workflow não aplica infraestrutura.

### AWS Fargate E2E

```text
.github/workflows/aws-fargate-e2e.yml
```

Orquestra a execução real na AWS e aplica o quality gate remoto.

---

## Evidências

### Local

```text
reports/allure-results
reports/allure-report
```

### AWS

- logs: CloudWatch Logs;
- resultados Allure: bucket privado S3;
- artifact final: GitHub Actions.

---

## Segurança aplicada

- nenhuma access key AWS persistente no GitHub;
- OIDC limitado à `release/2.0-aws`;
- `iam:PassRole` limitado às roles ECS do projeto;
- bucket Allure com acesso público bloqueado;
- bucket Terraform state privado, criptografado e versionado;
- locking nativo do state no S3;
- security group sem regras de entrada;
- execução efêmera no Fargate;
- imagens ECR imutáveis;
- permissões IAM reduzidas ao necessário.

---

## Boas práticas aplicadas

- cenários independentes;
- cobertura orientada a risco;
- BDD focado em comportamento;
- Page Object Model;
- API-first para pré-condições;
- camada de serviço para HTTP;
- validação backend após operações críticas;
- dados dinâmicos;
- isolamento de sessão;
- `Decimal` para valores monetários;
- polling com deadline;
- auto-wait do Playwright;
- ambiente determinístico;
- quality gates locais e cloud;
- infraestrutura como código;
- autenticação federada OIDC;
- evidências automáticas.

---

## Documentação adicional

- [`docs/AWS_FARGATE_RUNNER.md`](docs/AWS_FARGATE_RUNNER.md) — arquitetura e operação AWS/Fargate;
- [`infra/terraform/README.md`](infra/terraform/README.md) — infraestrutura, backend remoto e operação Terraform;
- [`docs/findings.md`](docs/findings.md) — comportamentos e defeitos conhecidos do ParaBank;
- [`DOCKER_SETUP.md`](DOCKER_SETUP.md) — preparação do ambiente local.

---

## Licença

Este projeto está licenciado sob a **MIT License**. Consulte [`LICENSE`](LICENSE).

O ParaBank é um sistema de demonstração da Parasoft e permanece sujeito aos termos aplicáveis do respectivo fornecedor.

---

<p align="center">
  Python · Playwright · Behave · Docker · AWS · ECS/Fargate · Terraform · Allure · GitHub Actions
</p>
