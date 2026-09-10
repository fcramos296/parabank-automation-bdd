# Zero-setup local execution with Docker

A versão final executa o ParaBank em um ambiente Docker descartável e reduz ao mínimo os pré-requisitos manuais de quem clona o projeto.

## Entrada recomendada

Windows:

```powershell
run_tests.bat
```

Linux/macOS:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

Se Python 3.10+ já estiver instalado, também é possível usar diretamente:

```bash
python scripts/run.py
```

ou:

```bash
python3 scripts/run.py
```

## Responsabilidades do bootstrap

Os wrappers resolvem o único pré-requisito que `run.py` não consegue instalar sozinho: o próprio interpretador Python.

Depois que Python está disponível, `scripts/run.py` assume o restante:

```text
run_tests.bat / run_tests.sh
        ↓
Python 3.10+ disponível?
        ├── não → oferece instalação
        └── sim
        ↓
scripts/run.py
        ↓
Docker + Compose
        ↓
ParaBank baseline
        ↓
.venv + requirements
        ↓
Playwright + browser
        ↓
Behave + Allure results
```

`requirements.txt` instala dependências Python; ele não instala o próprio Python.

## Windows

O wrapper procura Python 3.10+ e, quando necessário e autorizado, instala Python 3.12 via WinGet ou instalador oficial.

Depois, o bootstrap Docker:

1. verifica uma instalação Docker já funcional;
2. verifica virtualização de hardware;
3. valida WSL 2;
4. atualiza WSL quando necessário;
5. habilita WSL/Virtual Machine Platform quando autorizado;
6. informa claramente quando uma reinicialização do Windows é necessária;
7. instala Docker Desktop quando ausente;
8. inicia Docker Desktop;
9. espera `docker info` responder;
10. valida Docker Compose.

Virtualização Intel VT-x/AMD-V desabilitada no BIOS/UEFI não é alterada pelo projeto. Nesse caso, o runner informa o requisito pendente.

## Linux

O wrapper suporta famílias que disponibilizam `apt-get`, `dnf`, `yum`, `pacman` ou `zypper` para preparar Python e dependências básicas.

A estratégia de container utiliza Docker Engine nativo, não Docker Desktop. Portanto VM/KVM não é requisito para esta suíte.

Quando necessário, o bootstrap:

1. instala dependências básicas;
2. instala Docker Engine usando o bootstrap oficial do Docker;
3. inicia o serviço;
4. valida permissões de execução;
5. utiliza `sudo docker` durante a sessão quando necessário;
6. valida/instala o Compose plugin.

## macOS

Quando necessário, o wrapper prepara Python via Homebrew. Se Homebrew ainda não existir, o fluxo pode oferecê-lo como pré-requisito de bootstrap.

Para Docker Desktop, o runner utiliza uma instalação existente ou prepara o aplicativo via Homebrew/download oficial, inicia o runtime e espera `docker info` ficar disponível.

A primeira inicialização pode exigir permissões do sistema e aceite dos termos do Docker Desktop.

## Ciclo de vida do ParaBank

O `compose.yaml` utiliza `parasoft/parabank:baseline`, evitando depender diretamente do canal `latest`.

Cada execução normal faz:

```text
docker compose down --volumes --remove-orphans
                ↓
docker compose up -d
                ↓
readiness HTTP em /parabank/index.htm
                ↓
executa os testes
                ↓
docker compose down --volumes --remove-orphans
```

A checagem HTTP no host é a fonte única de readiness do SUT: além de validar que o container iniciou, ela confirma que a aplicação ParaBank já responde antes de liberar a execução dos cenários.

Para manter o ambiente ativo após os testes:

```bash
python scripts/run.py --keep-environment
```

## Políticas de instalação

Modo padrão, perguntando antes de instalar Docker/WSL:

```bash
python scripts/run.py
```

Autorizar bootstrap sem confirmação textual:

```bash
python scripts/run.py --install-docker
```

Proibir instalação automática:

```bash
python scripts/run.py --no-docker-install
```

Os wrappers encaminham argumentos para `run.py`:

```powershell
run_tests.bat --scope login --headed
```

```bash
./run_tests.sh --scope transfer
```

## Limites inevitáveis do host

Continuam externos ao projeto:

- sistema operacional suportado;
- acesso à internet para downloads iniciais;
- permissão administrativa quando exigida;
- espaço em disco/memória suficientes;
- hardware compatível com Docker Desktop;
- virtualização habilitada no firmware quando necessária;
- reinicialização do Windows após habilitação inicial de recursos;
- aceite de termos/licenças apresentado pelos softwares instalados.

O objetivo do bootstrap é detectar esses casos e explicar o que falta, em vez de terminar apenas com `command not found`.

## Referências oficiais

- Microsoft WSL: https://learn.microsoft.com/windows/wsl/install
- Docker Desktop Windows: https://docs.docker.com/desktop/setup/install/windows-install/
- Docker Desktop WSL 2: https://docs.docker.com/desktop/features/wsl/
- Docker Desktop macOS: https://docs.docker.com/desktop/setup/install/mac-install/
- Docker Engine: https://docs.docker.com/engine/install/
- Docker Compose: https://docs.docker.com/compose/install/
- Python: https://www.python.org/downloads/
