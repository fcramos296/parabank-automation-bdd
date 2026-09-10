from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Literal, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DockerInstallPolicy = Literal[
    "ask",
    "always",
    "never",
]

WINDOWS_DOCKER_BIN = Path(
    r"C:\Program Files\Docker\Docker\resources\bin"
)
WINDOWS_DOCKER_DESKTOP = Path(
    r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
)
MAC_DOCKER_APP = Path(
    "/Applications/Docker.app"
)
MAC_DOCKER_BIN = (
    MAC_DOCKER_APP
    / "Contents"
    / "Resources"
    / "bin"
)

DOCKER_START_TIMEOUT_SECONDS = 180.0
DOCKER_POLL_INTERVAL_SECONDS = 2.0


def _run(
    command: Sequence[str | Path],
    *,
    check: bool = True,
    capture_output: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess:
    normalized = [
        str(item)
        for item in command
    ]

    return subprocess.run(
        normalized,
        cwd=PROJECT_ROOT,
        check=check,
        text=True,
        capture_output=capture_output,
        timeout=timeout,
    )


def _command_succeeds(
    command: Sequence[str | Path],
    *,
    timeout: float = 15.0,
) -> bool:
    try:
        _run(
            command,
            check=True,
            capture_output=True,
            timeout=timeout,
        )
        return True
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        return False


def _prepend_path(path: Path) -> None:
    if not path.exists():
        return

    current_entries = os.environ.get(
        "PATH",
        "",
    ).split(os.pathsep)

    path_text = str(path)

    if path_text not in current_entries:
        os.environ["PATH"] = (
            path_text
            + os.pathsep
            + os.environ.get("PATH", "")
        )


def _refresh_docker_path() -> None:
    system = platform.system()

    if system == "Windows":
        _prepend_path(
            WINDOWS_DOCKER_BIN
        )
    elif system == "Darwin":
        _prepend_path(
            MAC_DOCKER_BIN
        )


def _is_interactive() -> bool:
    return (
        sys.stdin.isatty()
        and sys.stdout.isatty()
    )


def _confirm_install(system_label: str) -> bool:
    print()
    print(
        "[docker] Docker não foi encontrado."
    )
    print(
        "[docker] O ambiente local do ParaBank "
        "depende de Docker e Docker Compose."
    )
    print()

    while True:
        answer = input(
            f"Deseja instalar o Docker para {system_label} agora? "
            "[S/n]: "
        ).strip().lower()

        if answer in {
            "",
            "s",
            "sim",
            "y",
            "yes",
        }:
            return True

        if answer in {
            "n",
            "nao",
            "não",
            "no",
        }:
            return False

        print(
            "[docker] Responda S ou N."
        )


def _installation_allowed(
    policy: DockerInstallPolicy,
    system_label: str,
) -> bool:
    if policy == "always":
        return True

    if policy == "never":
        return False

    if not _is_interactive():
        return False

    return _confirm_install(
        system_label
    )


def _install_windows() -> None:
    if shutil.which("winget") is None:
        raise RuntimeError(
            "Docker Desktop não está instalado e o "
            "WinGet não foi encontrado. Instale o "
            "Docker Desktop manualmente e execute a "
            "suíte novamente."
        )

    print(
        "[docker] Instalando Docker Desktop via WinGet..."
    )

    _run(
        [
            "winget",
            "install",
            "--exact",
            "--id",
            "Docker.DockerDesktop",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]
    )

    _refresh_docker_path()


def _install_macos() -> None:
    if shutil.which("brew") is None:
        raise RuntimeError(
            "Docker Desktop não está instalado e o "
            "Homebrew não foi encontrado. Instale o "
            "Docker Desktop para macOS e execute a "
            "suíte novamente."
        )

    print(
        "[docker] Instalando Docker Desktop via Homebrew..."
    )

    _run(
        [
            "brew",
            "install",
            "--cask",
            "docker",
        ]
    )

    _refresh_docker_path()


def _install_linux() -> None:
    if shutil.which("curl") is None:
        raise RuntimeError(
            "curl não foi encontrado. Instale curl "
            "para que o bootstrap oficial do Docker "
            "possa ser executado."
        )

    if (
        os.geteuid() != 0
        and shutil.which("sudo") is None
    ):
        raise RuntimeError(
            "A instalação do Docker Engine exige "
            "privilégios administrativos. sudo não "
            "foi encontrado."
        )

    print(
        "[docker] Instalando Docker Engine pelo "
        "bootstrap oficial get.docker.com..."
    )

    with tempfile.TemporaryDirectory(
        prefix="parabank-docker-"
    ) as directory:
        installer = (
            Path(directory)
            / "get-docker.sh"
        )

        _run(
            [
                "curl",
                "-fsSL",
                "https://get.docker.com",
                "-o",
                installer,
            ]
        )

        command: list[str | Path] = [
            "sh",
            installer,
        ]

        if os.geteuid() != 0:
            command.insert(
                0,
                "sudo",
            )

        _run(command)


def _install_docker(
    system: str,
) -> None:
    if system == "Windows":
        _install_windows()
        return

    if system == "Darwin":
        _install_macos()
        return

    if system == "Linux":
        _install_linux()
        return

    raise RuntimeError(
        "Sistema operacional não suportado pelo "
        f"bootstrap automático do Docker: {system}."
    )


def _start_windows_desktop() -> None:
    print(
        "[docker] Iniciando Docker Desktop..."
    )

    if _command_succeeds(
        [
            "docker",
            "desktop",
            "start",
            "--timeout",
            "120",
        ],
        timeout=130,
    ):
        return

    if WINDOWS_DOCKER_DESKTOP.exists():
        subprocess.Popen(
            [str(WINDOWS_DOCKER_DESKTOP)],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    raise RuntimeError(
        "Docker Desktop foi encontrado, mas não foi "
        "possível iniciá-lo automaticamente."
    )


def _start_macos_desktop() -> None:
    print(
        "[docker] Iniciando Docker Desktop..."
    )

    if _command_succeeds(
        [
            "docker",
            "desktop",
            "start",
            "--timeout",
            "120",
        ],
        timeout=130,
    ):
        return

    try:
        _run(
            [
                "open",
                "-a",
                "Docker",
            ]
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Docker Desktop foi encontrado, mas não "
            "foi possível iniciá-lo automaticamente."
        ) from exc


def _start_linux_daemon() -> None:
    print(
        "[docker] Iniciando Docker Engine..."
    )

    prefix: list[str] = []

    if os.geteuid() != 0:
        prefix = ["sudo"]

    if shutil.which("systemctl"):
        _run(
            [
                *prefix,
                "systemctl",
                "enable",
                "--now",
                "docker",
            ],
            check=False,
        )
        return

    if shutil.which("service"):
        _run(
            [
                *prefix,
                "service",
                "docker",
                "start",
            ],
            check=False,
        )
        return


def _wait_for_docker(
    command: Sequence[str],
    timeout_seconds: float = DOCKER_START_TIMEOUT_SECONDS,
) -> bool:
    deadline = (
        time.monotonic()
        + timeout_seconds
    )

    while time.monotonic() < deadline:
        if _command_succeeds(
            [
                *command,
                "info",
            ]
        ):
            return True

        time.sleep(
            DOCKER_POLL_INTERVAL_SECONDS
        )

    return False


def _resolve_linux_command() -> list[str] | None:
    if _command_succeeds(
        [
            "docker",
            "info",
        ]
    ):
        return ["docker"]

    if (
        os.geteuid() != 0
        and shutil.which("sudo")
        and _command_succeeds(
            [
                "sudo",
                "docker",
                "info",
            ],
            timeout=30,
        )
    ):
        print(
            "[docker] Docker requer privilégios nesta "
            "sessão; os comandos usarão sudo."
        )
        return [
            "sudo",
            "docker",
        ]

    return None


def _resolve_running_command(
    system: str,
) -> list[str] | None:
    if shutil.which("docker") is None:
        return None

    if system == "Linux":
        return _resolve_linux_command()

    if _command_succeeds(
        [
            "docker",
            "info",
        ]
    ):
        return ["docker"]

    return None


def _start_runtime(
    system: str,
) -> None:
    if system == "Windows":
        _start_windows_desktop()
        return

    if system == "Darwin":
        _start_macos_desktop()
        return

    if system == "Linux":
        _start_linux_daemon()
        return


def _ensure_compose(
    docker_command: Sequence[str],
    system: str,
) -> None:
    if _command_succeeds(
        [
            *docker_command,
            "compose",
            "version",
        ]
    ):
        return

    if system != "Linux":
        raise RuntimeError(
            "Docker está disponível, mas o Docker "
            "Compose não foi encontrado. Atualize ou "
            "reinstale o Docker Desktop."
        )

    prefix: list[str] = []

    if os.geteuid() != 0:
        prefix = ["sudo"]

    print(
        "[docker] Instalando Docker Compose plugin..."
    )

    if shutil.which("apt-get"):
        _run(
            [
                *prefix,
                "apt-get",
                "update",
            ]
        )
        _run(
            [
                *prefix,
                "apt-get",
                "install",
                "-y",
                "docker-compose-plugin",
            ]
        )
    elif shutil.which("dnf"):
        _run(
            [
                *prefix,
                "dnf",
                "install",
                "-y",
                "docker-compose-plugin",
            ]
        )
    elif shutil.which("yum"):
        _run(
            [
                *prefix,
                "yum",
                "install",
                "-y",
                "docker-compose-plugin",
            ]
        )
    else:
        raise RuntimeError(
            "Docker Engine está instalado, mas o "
            "Compose plugin não está disponível e o "
            "gerenciador de pacotes não é suportado "
            "pelo bootstrap automático."
        )

    if not _command_succeeds(
        [
            *docker_command,
            "compose",
            "version",
        ]
    ):
        raise RuntimeError(
            "O Docker Compose plugin foi instalado, "
            "mas ainda não está disponível."
        )


def ensure_docker(
    *,
    install_policy: DockerInstallPolicy = "ask",
) -> list[str]:
    """
    Ensures that a usable Docker runtime and Compose plugin
    are available for this test execution.

    Returns the command prefix used by the environment
    lifecycle. It is normally ["docker"]. On Linux systems
    where the current user cannot access the daemon directly,
    it may be ["sudo", "docker"].
    """

    system = platform.system()

    system_labels = {
        "Windows": "Windows",
        "Darwin": "macOS",
        "Linux": "Linux",
    }

    if system not in system_labels:
        raise RuntimeError(
            "Sistema operacional não suportado: "
            f"{system}."
        )

    _refresh_docker_path()

    docker_command = _resolve_running_command(
        system
    )

    if docker_command is None:
        docker_installed = (
            shutil.which("docker")
            is not None
        )

        if not docker_installed:
            if not _installation_allowed(
                install_policy,
                system_labels[system],
            ):
                raise RuntimeError(
                    "Docker não está instalado. Execute "
                    "novamente e aceite o bootstrap, ou "
                    "use --install-docker para autorizar "
                    "a instalação automaticamente."
                )

            _install_docker(system)
            _refresh_docker_path()

            if shutil.which("docker") is None:
                raise RuntimeError(
                    "A instalação do Docker terminou, mas "
                    "o executável ainda não está acessível. "
                    "Feche e abra o terminal e execute a "
                    "suíte novamente."
                )

        _start_runtime(system)

        if system == "Linux":
            if not _wait_for_docker(
                ["docker"],
                timeout_seconds=30,
            ):
                docker_command = _resolve_linux_command()
            else:
                docker_command = ["docker"]
        else:
            if _wait_for_docker(
                ["docker"]
            ):
                docker_command = ["docker"]

        if docker_command is None:
            if system == "Windows":
                detail = (
                    "O Windows pode exigir WSL 2, "
                    "virtualização habilitada ou uma "
                    "reinicialização após a instalação."
                )
            elif system == "Darwin":
                detail = (
                    "Abra o Docker Desktop uma vez para "
                    "concluir qualquer configuração ou "
                    "aceite de licença pendente."
                )
            else:
                detail = (
                    "Verifique o serviço docker e as "
                    "permissões do usuário."
                )

            raise RuntimeError(
                "Docker foi encontrado/instalado, mas o "
                "daemon não ficou disponível. "
                + detail
            )

    _ensure_compose(
        docker_command,
        system,
    )

    version = _run(
        [
            *docker_command,
            "--version",
        ],
        capture_output=True,
    ).stdout.strip()

    compose_version = _run(
        [
            *docker_command,
            "compose",
            "version",
        ],
        capture_output=True,
    ).stdout.strip()

    print(
        f"[docker] {version}"
    )
    print(
        f"[docker] {compose_version}"
    )
    print(
        "[docker] Runtime pronto para a suíte."
    )

    return list(
        docker_command
    )
