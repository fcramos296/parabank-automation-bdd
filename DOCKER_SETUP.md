# Docker bootstrap para a suíte local

Esta branch executa o ParaBank em um ambiente Docker descartável e tenta preparar o runtime automaticamente antes dos testes.

## Execução padrão

Windows:

```powershell
python scripts/run.py
```

ou:

```powershell
run_tests.bat
```

Linux/macOS:

```bash
python3 scripts/run.py
```

ou:

```bash
./run_tests.sh
```

Quando Docker já está instalado, o runner apenas garante que o runtime esteja ativo, valida `docker compose` e sobe o ParaBank.

Quando Docker não está instalado e existe um terminal interativo, o runner solicita autorização antes de instalar qualquer componente do sistema.

## Políticas de instalação

Autorizar instalação sem confirmação interativa:

```bash
python scripts/run.py --install-docker
```

Impedir qualquer tentativa de instalação:

```bash
python scripts/run.py --no-docker-install
```

O modo padrão fica entre os dois: detecta a ausência do Docker e pergunta antes de alterar a máquina.

## Windows

Estratégia:

1. procura o Docker CLI;
2. também verifica a instalação padrão do Docker Desktop;
3. quando ausente e autorizado, utiliza WinGet para instalar `Docker.DockerDesktop`;
4. tenta iniciar Docker Desktop pela Docker Desktop CLI;
5. usa o executável do Docker Desktop como fallback;
6. espera `docker info` responder;
7. valida `docker compose version`.

A primeira instalação pode depender de WSL 2, virtualização do Windows ou reinicialização. Se o Docker Desktop não puder concluir essas etapas durante a execução atual, o runner encerra com uma mensagem objetiva e pode ser executado novamente depois que o requisito do sistema for resolvido.

## macOS

Estratégia:

1. procura o Docker CLI e a instalação padrão em `/Applications/Docker.app`;
2. quando ausente e autorizado, utiliza Homebrew (`brew install --cask docker`) quando disponível;
3. tenta iniciar Docker Desktop pela Docker Desktop CLI;
4. usa `open -a Docker` como fallback;
5. espera `docker info` responder;
6. valida `docker compose version`.

Docker Desktop pode exigir uma primeira inicialização para concluir configurações do macOS ou aceite de licença.

## Linux

Estratégia:

1. procura Docker Engine;
2. quando ausente e autorizado, baixa o script oficial `https://get.docker.com` e executa a instalação com privilégios administrativos;
3. tenta habilitar/iniciar o serviço `docker` via `systemctl` ou `service`;
4. usa `docker` diretamente quando o usuário possui permissão;
5. caso necessário, utiliza `sudo docker` durante a execução atual;
6. valida o Docker Compose plugin;
7. quando o Compose plugin estiver ausente, tenta instalá-lo via `apt-get`, `dnf` ou `yum`.

O script oficial `get.docker.com` é apropriado para ambientes de desenvolvimento/testes, mas não é tratado aqui como estratégia de provisionamento para servidores de produção.

## Ciclo de vida do ParaBank

Depois que Docker está disponível, toda execução normal faz:

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

Isso deixa a massa de dados isolada entre execuções.

Para manter o ambiente ativo para inspeção manual:

```bash
python scripts/run.py --keep-environment
```

## Pré-requisitos que o projeto não tenta instalar

- Python 3.10 ou superior;
- acesso à internet na primeira instalação/download de imagens;
- virtualização suportada e habilitada quando exigida pela plataforma;
- permissão administrativa quando o sistema operacional exigir instalação de componentes.

## Referências oficiais

- Docker Desktop: https://docs.docker.com/desktop/
- Docker Desktop CLI: https://docs.docker.com/desktop/features/desktop-cli/
- Docker Engine: https://docs.docker.com/engine/install/
- Docker Compose: https://docs.docker.com/compose/install/
- Docker Desktop para macOS: https://docs.docker.com/desktop/setup/install/mac-install/
