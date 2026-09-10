from __future__ import annotations

import getpass
import os
import platform
import re
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

WINDOWS_SYSTEM_DOCKER_BIN = Path(
    r"C:\Program Files\Docker\Docker\resources\bin"
)
WINDOWS_SYSTEM_DOCKER_DESKTOP = Path(
    r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
)
WINDOWS_USER_DOCKER_ROOT = (
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "Programs"
    / "DockerDesktop"
)
WINDOWS_USER_DOCKER_BIN = (
    WINDOWS_USER_DOCKER_ROOT
    / "resources"
    / "bin"
)
WINDOWS_USER_DOCKER_DESKTOP = (
    WINDOWS_USER_DOCKER_ROOT
    / "Docker Desktop.exe"
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

MINIMUM_WSL_VERSION = (
    2,
    1,
    5,
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


def _prepend_path(
    path: Path,
) -> None:
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
            WINDOWS_USER_DOCKER_BIN
        )
        _prepend_path(
            WINDOWS_SYSTEM_DOCKER_BIN
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


def _confirm_install(
    component_label: str,
    system_label: str,
) -> bool:
    print()
    print(
        f"[setup] {component_label} não está disponível."
    )
    print()

    while True:
        answer = input(
            f"Deseja preparar {component_label} "
            f"para {system_label} agora? [S/n]: "
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
            "[setup] Responda S ou N."
        )


def _installation_allowed(
    policy: DockerInstallPolicy,
    component_label: str,
    system_label: str,
) -> bool:
    if policy == "always":
        return True

    if policy == "never":
        return False

    if not _is_interactive():
        return False

    return _confirm_install(
        component_label,
        system_label,
    )


def _windows_virtualization_enabled() -> bool | None:
    command = [
        "powershell.exe",
        "-NoProfile",
        "-Command",
        (
            "$value = Get-CimInstance Win32_Processor "
            "| Select-Object -First 1 "
            "-ExpandProperty VirtualizationFirmwareEnabled; "
            "if ($null -eq $value) { 'Unknown' } "
            "elseif ($value) { 'True' } "
            "else { 'False' }"
        ),
    ]

    try:
        result = _run(
            command,
            check=False,
            capture_output=True,
            timeout=20,
        )
    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return None

    value = (
        result.stdout
        .strip()
        .lower()
    )

    if value == "true":
        return True

    if value == "false":
        return False

    return None


def _windows_wsl_version() -> tuple[int, int, int] | None:
    try:
        result = _run(
            [
                "wsl.exe",
                "--version",
            ],
            check=False,
            capture_output=True,
            timeout=20,
        )
    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return None

    text = (
        (result.stdout or "")
        + "\n"
        + (result.stderr or "")
    )

    first_line = (
        text.strip()
        .splitlines()[0]
        if text.strip()
        else ""
    )

    match = re.search(
        r"(\d+)\.(\d+)\.(\d+)",
        first_line,
    )

    if match is None:
        match = re.search(
            r"(\d+)\.(\d+)\.(\d+)",
            text,
        )

    if match is None:
        return None

    return tuple(
        int(part)
        for part in match.groups()
    )


def _run_windows_elevated(
    executable: str,
    arguments: Sequence[str],
) -> None:
    escaped_file = executable.replace(
        "'",
        "''",
    )

    escaped_args = ", ".join(
        "'"
        + argument.replace(
            "'",
            "''",
        )
        + "'"
        for argument in arguments
    )

    script = (
        "$process = Start-Process "
        f"-FilePath '{escaped_file}' "
        f"-ArgumentList @({escaped_args}) "
        "-Verb RunAs -Wait -PassThru; "
        "exit $process.ExitCode"
    )

    _run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ]
    )


def _ensure_windows_wsl(
    policy: DockerInstallPolicy,
) -> None:
    virtualization = (
        _windows_virtualization_enabled()
    )

    if virtualization is False:
        raise RuntimeError(
            "A virtualização de hardware está desabilitada "
            "no BIOS/UEFI. O Docker Desktop com WSL 2 não "
            "pode ser iniciado até que Intel VT-x/AMD-V "
            "seja habilitado no firmware da máquina."
        )

    current_version = (
        _windows_wsl_version()
    )

    if (
        current_version is not None
        and current_version
        >= MINIMUM_WSL_VERSION
    ):
        print(
            "[wsl] WSL "
            + ".".join(
                str(part)
                for part in current_version
            )
            + " disponível."
        )
        return

    if not _installation_allowed(
        policy,
        "WSL 2 / Virtual Machine Platform",
        "Windows",
    ):
        raise RuntimeError(
            "WSL 2 não atende aos requisitos do Docker "
            "Desktop. Execute novamente e autorize o "
            "bootstrap, ou prepare WSL 2 manualmente."
        )

    if current_version is None:
        print(
            "[wsl] Habilitando WSL 2 e Virtual Machine Platform..."
        )

        _run_windows_elevated(
            "wsl.exe",
            [
                "--install",
                "--no-distribution",
            ],
        )
    else:
        print(
            "[wsl] Atualizando WSL..."
        )

    update_result = _run(
        [
            "wsl.exe",
            "--update",
        ],
        check=False,
        capture_output=True,
        timeout=180,
    )

    if update_result.returncode != 0:
        print(
            "[wsl] Atualização normal não concluiu; "
            "tentando com elevação..."
        )
        _run_windows_elevated(
            "wsl.exe",
            [
                "--update",
            ],
        )

    _run(
        [
            "wsl.exe",
            "--set-default-version",
            "2",
        ],
        check=False,
        capture_output=True,
        timeout=30,
    )

    updated_version = (
        _windows_wsl_version()
    )

    if (
        updated_version is None
        or updated_version
        < MINIMUM_WSL_VERSION
    ):
        raise RuntimeError(
            "WSL/Virtual Machine Platform foram preparados, "
            "mas o Windows ainda não expôs uma versão WSL "
            "compatível. Reinicie o Windows e execute "
            "novamente o mesmo comando. O bootstrap "
            "continuará automaticamente após o reboot."
        )

    print(
        "[wsl] WSL "
        + ".".join(
            str(part)
            for part in updated_version
        )
        + " pronto para Docker Desktop."
    )


def _install_windows() -> None:
    if shutil.which("winget") is None:
        raise RuntimeError(
            "Docker Desktop não está instalado e o "
            "WinGet não foi encontrado. O wrapper "
            "run_tests.bat consegue instalar Python, "
            "mas esta instalação do Docker requer "
            "WinGet ou instalação manual do Desktop."
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


def _install_macos_direct() -> None:
    if shutil.which("curl") is None:
        raise RuntimeError(
            "curl não foi encontrado no macOS. "
            "Não foi possível baixar Docker Desktop."
        )

    if (
        os.geteuid() != 0
        and shutil.which("sudo") is None
    ):
        raise RuntimeError(
            "A instalação do Docker Desktop no macOS "
            "exige privilégios administrativos."
        )

    machine = (
        platform.machine()
        .lower()
    )

    architecture = (
        "arm64"
        if machine in {
            "arm64",
            "aarch64",
        }
        else "amd64"
    )

    download_url = (
        "https://desktop.docker.com/mac/main/"
        f"{architecture}/Docker.dmg"
    )

    prefix: list[str] = []

    if os.geteuid() != 0:
        prefix = ["sudo"]

    with tempfile.TemporaryDirectory(
        prefix="parabank-docker-mac-"
    ) as directory:
        dmg_path = (
            Path(directory)
            / "Docker.dmg"
        )

        print(
            "[docker] Baixando Docker Desktop oficial para macOS..."
        )

        _run(
            [
                "curl",
                "-fL",
                download_url,
                "-o",
                dmg_path,
            ]
        )

        _run(
            [
                *prefix,
                "hdiutil",
                "attach",
                dmg_path,
                "-nobrowse",
            ]
        )

        try:
            _run(
                [
                    *prefix,
                    (
                        "/Volumes/Docker/Docker.app/"
                        "Contents/MacOS/install"
                    ),
                    "--user",
                    getpass.getuser(),
                ]
            )
        finally:
            _run(
                [
                    *prefix,
                    "hdiutil",
                    "detach",
                    "/Volumes/Docker",
                ],
                check=False,
            )

    _refresh_docker_path()


def _install_macos() -> None:
    if shutil.which("brew") is not None:
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
        return

    _install_macos_direct()


def _linux_admin_prefix() -> list[str]:
    if os.geteuid() == 0:
        return []

    if shutil.which("sudo") is None:
        raise RuntimeError(
            "A operação exige privilégios administrativos "
            "e sudo não foi encontrado."
        )

    return ["sudo"]


def _ensure_linux_curl() -> None:
    if shutil.which("curl") is not None:
        return

    prefix = _linux_admin_prefix()

    print(
        "[docker] curl não encontrado; instalando..."
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
                "curl",
                "ca-certificates",
            ]
        )
    elif shutil.which("dnf"):
        _run(
            [
                *prefix,
                "dnf",
                "install",
                "-y",
                "curl",
                "ca-certificates",
            ]
        )
    elif shutil.which("yum"):
        _run(
            [
                *prefix,
                "yum",
                "install",
                "-y",
                "curl",
                "ca-certificates",
            ]
        )
    elif shutil.which("pacman"):
        _run(
            [
                *prefix,
                "pacman",
                "-S",
                "--noconfirm",
                "curl",
                "ca-certificates",
            ]
        )
    elif shutil.which("zypper"):
        _run(
            [
                *prefix,
                "zypper",
                "--non-interactive",
                "install",
                "curl",
                "ca-certificates",
            ]
        )
    else:
        raise RuntimeError(
            "curl não está disponível e nenhum gerenciador "
            "de pacotes Linux suportado foi encontrado."
        )

    if shutil.which("curl") is None:
        raise RuntimeError(
            "curl foi solicitado ao gerenciador de pacotes, "
            "mas continua indisponível."
        )


def _install_linux() -> None:
    prefix = _linux_admin_prefix()

    _ensure_linux_curl()

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

        _run(
            [
                *prefix,
                "sh",
                installer,
            ]
        )


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


def _windows_desktop_executable() -> Path | None:
    candidates = (
        WINDOWS_USER_DOCKER_DESKTOP,
        WINDOWS_SYSTEM_DOCKER_DESKTOP,
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


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

    executable = (
        _windows_desktop_executable()
    )

    if executable is not None:
        subprocess.Popen(
            [str(executable)],
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

    prefix = _linux_admin_prefix()

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

    prefix = _linux_admin_prefix()

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
    Ensures that the host prerequisites, Docker runtime and
    Compose plugin are available for this test execution.

    Windows uses Docker Desktop + WSL 2.
    macOS uses Docker Desktop.
    Linux uses Docker Engine directly.

    Returns ["docker"] in the common case and may return
    ["sudo", "docker"] on Linux when daemon access still
    requires elevated privileges.
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

    docker_command = (
        _resolve_running_command(
            system
        )
    )

    if docker_command is not None:
        _ensure_compose(
            docker_command,
            system,
        )
        return _print_versions(
            docker_command
        )

    if system == "Windows":
        _ensure_windows_wsl(
            install_policy
        )

    docker_installed = (
        shutil.which("docker")
        is not None
    )

    if not docker_installed:
        if not _installation_allowed(
            install_policy,
            "Docker",
            system_labels[system],
        ):
            raise RuntimeError(
                "Docker não está instalado. Execute "
                "novamente e aceite o bootstrap, ou "
                "use --install-docker para autorizar "
                "a instalação automaticamente."
            )

        _install_docker(
            system
        )
        _refresh_docker_path()

        if shutil.which("docker") is None:
            raise RuntimeError(
                "A instalação do Docker terminou, mas "
                "o executável ainda não está acessível. "
                "Feche e abra o terminal e execute a "
                "suíte novamente."
            )

    _start_runtime(
        system
    )

    if system == "Linux":
        if not _wait_for_docker(
            ["docker"],
            timeout_seconds=30,
        ):
            docker_command = (
                _resolve_linux_command()
            )
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
                "Verifique WSL 2, virtualização de "
                "hardware e se existe reinicialização "
                "pendente após habilitar recursos do Windows."
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

    return _print_versions(
        docker_command
    )


def _print_versions(
    docker_command: Sequence[str],
) -> list[str]:
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
