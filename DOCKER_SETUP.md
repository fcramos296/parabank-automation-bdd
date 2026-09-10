# Zero-setup local execution with Docker

A branch `docker/local-e2e` foi preparada para executar o ParaBank em um ambiente Docker descartável e reduzir ao mínimo os pré-requisitos manuais do avaliador.

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

Se Python já estiver instalado, também é possível usar diretamente:

```bash
python scripts/run.py
```

ou:

```bash
python3 scripts/run.py
```

## O que cada camada prepara

Os wrappers `run_tests.bat` e `run_tests.sh` são responsáveis pelo único problema que `run.py` não consegue resolver sozinho: uma máquina sem interpretador Python.

Depois que Python está disponível, `scripts/run.py` assume o restante do bootstrap.

Fluxo:

```text
run_tests.bat / run_tests.sh
        ↓
Python 3.10+ disponível?
        ├── não → oferece instalação automática
        └── sim
        ↓
scripts/run.py
        ↓
pré-requisitos Docker do SO
        ↓
Docker + Compose
        ↓
ParaBank local limpo
        ↓
venv + requirements.txt
        ↓
Playwright + browser
        ↓
Behave + Allure results
```

`requirements.txt` não instala Python. Ele descreve dependências que o `pip` instala depois que um interpretador Python já existe.

## Windows

Quando executado via `run_tests.bat` em uma máquina sem Python:

1. procura Python 3.10+;
2. procura também o Python Launcher (`py`);
3. oferece instalar Python 3.12;
4. usa WinGet quando disponível;
5. usa como fallback o instalador oficial Python 3.12.10 para x86-64 ou ARM64;
6. atualiza o PATH da sessão e continua a execução.

Depois que `run.py` inicia, o bootstrap Docker:

1. verifica se um Docker já funcional está disponível;
2. verifica virtualização de hardware via `Win32_Processor.VirtualizationFirmwareEnabled`;
3. verifica a versão do WSL;
4. exige WSL 2.1.5 ou superior;
5. quando necessário e autorizado, executa `wsl --install --no-distribution` com elevação;
6. executa `wsl --update`;
7. configura WSL 2 como padrão;
8. se o Windows ainda exigir reinicialização, encerra com uma mensagem específica para que o mesmo comando seja executado novamente após o reboot;
9. instala Docker Desktop via WinGet quando necessário;
10. inicia Docker Desktop;
11. espera `docker info` responder;
12. valida `docker compose version`.

Docker Desktop não precisa de uma distribuição Ubuntu do usuário para o backend WSL 2; por isso o bootstrap usa `--no-distribution`.

A única configuração que o projeto não tenta modificar é virtualização desabilitada no BIOS/UEFI. Quando detectada, a execução para com uma mensagem objetiva, porque essa alteração pertence ao firmware da máquina.

## macOS

Quando Python não existe, `run_tests.sh`:

1. procura `python3`/`python` 3.10+;
2. oferece instalar Python;
3. utiliza Homebrew;
4. se Homebrew ainda não existir, oferece o bootstrap oficial do Homebrew;
5. instala Python 3.12 e continua.

Depois, `run.py` prepara Docker Desktop:

1. usa uma instalação existente quando disponível;
2. se Homebrew estiver disponível, utiliza `brew install --cask docker`;
3. sem Homebrew, baixa diretamente o `Docker.dmg` oficial correto para Apple Silicon ou Intel;
4. instala em `/Applications/Docker.app`;
5. inicia Docker Desktop;
6. espera `docker info` responder;
7. valida Docker Compose.

Na primeira inicialização, o macOS/Docker Desktop ainda pode solicitar senha administrativa, permissões do sistema ou aceite dos termos do Docker Desktop.

## Linux

`run_tests.sh` suporta bootstrap de Python nas famílias de distribuição que disponibilizam um dos seguintes gerenciadores:

- `apt-get`;
- `dnf`;
- `yum`;
- `pacman`;
- `zypper`.

Quando necessário, instala Python 3, pip, suporte a `venv`, `curl` e certificados. A versão final encontrada precisa ser Python 3.10+.

Para Docker, a estratégia é Docker Engine nativo, não Docker Desktop. Portanto uma VM/KVM não é necessária para executar esta suíte.

O runner:

1. instala `curl` se necessário;
2. baixa o bootstrap oficial `get.docker.com`;
3. instala Docker Engine com root/sudo;
4. inicia o serviço via `systemctl` ou `service`;
5. usa `docker` diretamente quando permitido;
6. usa `sudo docker` durante a sessão quando necessário;
7. valida o Docker Compose plugin;
8. tenta instalar `docker-compose-plugin` quando necessário em distribuições compatíveis.

O convenience script do Docker é apropriado aqui porque esta branch representa um ambiente descartável de desenvolvimento/teste, não provisionamento de servidor de produção.

## Ciclo de vida do ParaBank

Depois que Docker está disponível, cada execução normal faz:

```text
docker compose down --volumes --remove-orphans
                ↓
docker compose up -d
                ↓
aguarda http://localhost:8080/parabank/index.htm
                ↓
executa os testes
                ↓
docker compose down --volumes --remove-orphans
```

Isso evita acúmulo de usuários e mantém a massa de dados isolada entre execuções.

Para manter o ambiente ativo após os testes:

```bash
python scripts/run.py --keep-environment
```

## Políticas de instalação do Docker

Modo padrão, com confirmação quando componentes do host estiverem ausentes:

```bash
python scripts/run.py
```

Autorizar automaticamente o bootstrap Docker/WSL sem confirmação textual:

```bash
python scripts/run.py --install-docker
```

Impedir instalação automática de Docker/WSL:

```bash
python scripts/run.py --no-docker-install
```

Os wrappers também aceitam argumentos e os encaminham ao `run.py`. Exemplos:

Windows:

```powershell
run_tests.bat --scope login --headed
```

Linux/macOS:

```bash
./run_tests.sh --scope transfer
```

## O que ainda é inevitável no host

Uma automação não consegue garantir todos os aspectos de uma máquina física totalmente sem configuração. Permanecem requisitos externos:

- sistema operacional suportado;
- acesso à internet para downloads iniciais;
- usuário com permissão administrativa quando o SO exigir;
- espaço em disco/memória suficientes;
- hardware compatível com Docker Desktop;
- virtualização habilitada no BIOS/UEFI no Windows quando exigida pelo backend WSL 2;
- possibilidade de reiniciar o Windows após habilitação inicial de recursos;
- aceite de termos/licenças quando apresentado pelo software instalado.

O objetivo do bootstrap é detectar esses casos e informar precisamente o que está pendente, em vez de falhar apenas com mensagens como `command not found`.

## Referências oficiais

- Microsoft WSL: https://learn.microsoft.com/windows/wsl/install
- Docker Desktop Windows: https://docs.docker.com/desktop/setup/install/windows-install/
- Docker Desktop WSL 2: https://docs.docker.com/desktop/features/wsl/
- Docker Desktop macOS: https://docs.docker.com/desktop/setup/install/mac-install/
- Docker Engine: https://docs.docker.com/engine/install/
- Docker Compose: https://docs.docker.com/compose/install/
- Python downloads: https://www.python.org/downloads/
