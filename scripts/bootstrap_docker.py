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
DockerInstallPolicy = Literal["ask", "always", "never"]

LOCAL_APPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
WINDOWS_DOCKER_BINS = (
    LOCAL_APPDATA / "Programs" / "DockerDesktop" / "resources" / "bin",
    Path(r"C:\Program Files\Docker\Docker\resources\bin"),
)
WINDOWS_DOCKER_APPS = (
    LOCAL_APPDATA / "Programs" / "DockerDesktop" / "Docker Desktop.exe",
    Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe"),
)
MAC_DOCKER_APP = Path("/Applications/Docker.app")
MAC_DOCKER_BIN = MAC_DOCKER_APP / "Contents" / "Resources" / "bin"

MINIMUM_WSL_VERSION = (2, 1, 5)
DOCKER_START_TIMEOUT_SECONDS = 300.0
WINDOWS_DOCKER_CLI_TIMEOUT_SECONDS = 30.0
POLL_INTERVAL_SECONDS = 2.0


def _run(
    command: Sequence[str | Path],
    *,
    check: bool = True,
    capture_output: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(item) for item in command],
        cwd=PROJECT_ROOT,
        check=check,
        text=True,
        capture_output=capture_output,
        timeout=timeout,
    )


def _succeeds(
    command: Sequence[str | Path],
    *,
    timeout: float = 15.0,
) -> bool:
    try:
        _run(
            command,
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
    if path.exists():
        os.environ["PATH"] = str(path) + os.pathsep + os.environ.get("PATH", "")


def _refresh_docker_path() -> None:
    system = platform.system()

    if system == "Windows":
        for path in WINDOWS_DOCKER_BINS:
            _prepend_path(path)
    elif system == "Darwin":
        _prepend_path(MAC_DOCKER_BIN)


def _interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _allowed(
    policy: DockerInstallPolicy,
    component: str,
    system: str,
) -> bool:
    if policy == "always":
        return True

    if policy == "never" or not _interactive():
        return False

    while True:
        answer = (
            input(f"\nDeseja preparar {component} para {system} agora? [S/n]: ")
            .strip()
            .lower()
        )

        if answer in {"", "s", "sim", "y", "yes"}:
            return True

        if answer in {"n", "nao", "não", "no"}:
            return False

        print("[setup] Responda S ou N.")


def _windows_virtualization() -> bool | None:
    try:
        result = _run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                (
                    "$v=Get-CimInstance Win32_Processor | "
                    "Select-Object -First 1 "
                    "-ExpandProperty VirtualizationFirmwareEnabled; "
                    "if($null -eq $v){'Unknown'}elseif($v){'True'}else{'False'}"
                ),
            ],
            check=False,
            capture_output=True,
            timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    value = result.stdout.strip().lower()

    if value == "true":
        return True

    if value == "false":
        return False

    return None


def _windows_wsl_version() -> tuple[int, int, int] | None:
    # Capture and parse WSL output inside PowerShell. On some localized Windows
    # installations wsl.exe writes redirected output using an encoding that
    # Python's default text decoding does not interpret reliably. Returning
    # only ASCII digits from PowerShell avoids locale/encoding false negatives.
    powershell = (
        "$raw = & wsl.exe --version 2>&1; "
        "$exitCode = $LASTEXITCODE; "
        "if ($exitCode -ne 0) { exit $exitCode }; "
        "$line = $raw | Where-Object { "
        "[string]$_ -match 'WSL.*?([0-9]+)\\.([0-9]+)\\.([0-9]+)' "
        "} | Select-Object -First 1; "
        "if ($null -eq $line) { "
        "$line = $raw | Where-Object { "
        "[string]$_ -match '([0-9]+)\\.([0-9]+)\\.([0-9]+)' "
        "} | Select-Object -First 1 "
        "}; "
        "if ($null -eq $line) { exit 1 }; "
        "$m = [regex]::Match([string]$line, "
        "'([0-9]+)\\.([0-9]+)\\.([0-9]+)'); "
        "if (-not $m.Success) { exit 1 }; "
        "Write-Output ($m.Groups[1].Value + '.' + "
        "$m.Groups[2].Value + '.' + $m.Groups[3].Value)"
    )

    try:
        result = _run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                powershell,
            ],
            check=False,
            capture_output=True,
            timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None

    match = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout)

    if match is None:
        return None

    return tuple(int(part) for part in match.groups())


def _windows_wsl_status_ok() -> bool:
    return _succeeds(["wsl.exe", "--status"], timeout=20)


def _windows_elevated(
    executable: str,
    arguments: Sequence[str],
) -> None:
    file_name = executable.replace("'", "''")
    args = ", ".join(
        f"'{argument.replace(chr(39), chr(39) * 2)}'" for argument in arguments
    )
    script = (
        "$p=Start-Process "
        f"-FilePath '{file_name}' "
        f"-ArgumentList @({args}) "
        "-Verb RunAs -Wait -PassThru; exit $p.ExitCode"
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


def _print_wsl_diagnostics(
    version: tuple[int, int, int],
    virtualization: bool | None,
) -> None:
    if virtualization is False:
        print(
            "[wsl][AVISO] O WMI reportou virtualização de firmware como "
            "desabilitada, mas o WSL está instalado. A propriedade WMI pode "
            "retornar falso negativo; a validação funcional continuará."
        )

    if not _windows_wsl_status_ok():
        print(
            "[wsl][AVISO] 'wsl --status' não retornou sucesso. Isso pode ocorrer "
            "sem uma distribuição instalada ou por um aviso de rede do WSL. "
            "Como 'wsl --version' está válido, o bootstrap continuará e o "
            "Docker será a validação funcional definitiva."
        )

    print("[wsl] WSL " + ".".join(str(part) for part in version) + " disponível.")


def _ensure_windows_wsl(policy: DockerInstallPolicy) -> None:
    version = _windows_wsl_version()
    virtualization = _windows_virtualization()

    if version is not None and version >= MINIMUM_WSL_VERSION:
        _print_wsl_diagnostics(version, virtualization)
        return

    if virtualization is False:
        print(
            "[wsl][AVISO] O WMI reportou virtualização de firmware como "
            "desabilitada. Essa propriedade pode retornar falso negativo; "
            "o bootstrap tentará preparar o WSL antes de concluir que existe "
            "um bloqueio de firmware."
        )

    if not _allowed(
        policy,
        "WSL 2 / Virtual Machine Platform",
        "Windows",
    ):
        raise RuntimeError("WSL 2 não está pronto para o Docker Desktop.")

    if version is None:
        print("[wsl] Habilitando WSL 2 e Virtual Machine Platform...")
        _windows_elevated(
            "wsl.exe",
            ["--install", "--no-distribution"],
        )

    print("[wsl] Atualizando WSL...")

    result = _run(
        ["wsl.exe", "--update"],
        check=False,
        capture_output=True,
        timeout=180,
    )

    if result.returncode != 0:
        _windows_elevated("wsl.exe", ["--update"])

    _run(
        ["wsl.exe", "--set-default-version", "2"],
        check=False,
        capture_output=True,
        timeout=30,
    )

    version = _windows_wsl_version()

    if version is None or version < MINIMUM_WSL_VERSION:
        detail = (
            " O Windows também reportou a virtualização de firmware como "
            "desabilitada; se o erro persistir após reiniciar, confirme "
            "Intel VT-x/AMD-V/SVM no BIOS/UEFI."
            if virtualization is False
            else ""
        )
        raise RuntimeError(
            "WSL/Virtual Machine Platform foram preparados, mas a versão "
            "mínima do WSL ainda não está disponível. Reinicie a máquina e "
            f"execute o mesmo comando novamente.{detail}"
        )

    _print_wsl_diagnostics(version, virtualization)


def _install_windows() -> None:
    if shutil.which("winget") is None:
        raise RuntimeError(
            "WinGet não foi encontrado. Instale Docker Desktop manualmente "
            "ou disponibilize WinGet/App Installer."
        )

    print("[docker] Instalando Docker Desktop via WinGet...")
    result = _run(
        [
            "winget",
            "install",
            "--exact",
            "--id",
            "Docker.DockerDesktop",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--force",
            "--override",
            "install --quiet --accept-license --backend=wsl-2",
        ],
        check=False,
        capture_output=True,
        timeout=600,
    )

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()

        if detail:
            detail = " Detalhes: " + detail[-1500:]

        raise RuntimeError(
            "A instalação do Docker Desktop via WinGet falhou "
            f"com código {result.returncode}.{detail}"
        )

    _refresh_docker_path()
    print("[docker] Docker Desktop instalado com backend WSL 2.")


def _wait_for_windows_docker_cli(
    timeout_seconds: float = WINDOWS_DOCKER_CLI_TIMEOUT_SECONDS,
) -> bool:
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        _refresh_docker_path()

        if shutil.which("docker") is not None:
            return True

        time.sleep(1)

    return False


def _mac_admin_prefix() -> list[str]:
    if os.geteuid() == 0:
        return []

    if shutil.which("sudo"):
        return ["sudo"]

    raise RuntimeError("A instalação no macOS exige privilégios administrativos.")


def _install_macos() -> None:
    if shutil.which("brew"):
        print("[docker] Instalando Docker Desktop via Homebrew...")
        _run(["brew", "install", "--cask", "docker"])
        _refresh_docker_path()
        return

    if shutil.which("curl") is None:
        raise RuntimeError("curl não foi encontrado no macOS.")

    architecture = (
        "arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "amd64"
    )
    url = f"https://desktop.docker.com/mac/main/{architecture}/Docker.dmg"
    prefix = _mac_admin_prefix()

    with tempfile.TemporaryDirectory(prefix="parabank-docker-mac-") as directory:
        dmg = Path(directory) / "Docker.dmg"

        print("[docker] Baixando Docker Desktop oficial...")
        _run(["curl", "-fL", url, "-o", dmg])
        _run([*prefix, "hdiutil", "attach", dmg, "-nobrowse"])

        try:
            _run(
                [
                    *prefix,
                    ("/Volumes/Docker/Docker.app/Contents/MacOS/install"),
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


def _linux_admin_prefix() -> list[str]:
    if os.geteuid() == 0:
        return []

    if shutil.which("sudo"):
        return ["sudo"]

    raise RuntimeError("A operação exige root/sudo e sudo não foi encontrado.")


def _ensure_linux_curl() -> None:
    if shutil.which("curl"):
        return

    prefix = _linux_admin_prefix()
    print("[docker] Instalando curl...")

    if shutil.which("apt-get"):
        _run([*prefix, "apt-get", "update"])
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
            "Nenhum gerenciador suportado foi encontrado para instalar curl."
        )


def _install_linux() -> None:
    _ensure_linux_curl()
    prefix = _linux_admin_prefix()

    print("[docker] Instalando Docker Engine pelo bootstrap oficial get.docker.com...")

    with tempfile.TemporaryDirectory(prefix="parabank-docker-") as directory:
        installer = Path(directory) / "get-docker.sh"
        _run(
            [
                "curl",
                "-fsSL",
                "https://get.docker.com",
                "-o",
                installer,
            ]
        )
        _run([*prefix, "sh", installer])


def _install_docker(system: str) -> None:
    installers = {
        "Windows": _install_windows,
        "Darwin": _install_macos,
        "Linux": _install_linux,
    }
    installers[system]()


def _start_windows() -> None:
    print("[docker] Iniciando Docker Desktop...")

    if _succeeds(
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

    for executable in WINDOWS_DOCKER_APPS:
        if executable.exists():
            subprocess.Popen(
                [str(executable)],
                cwd=PROJECT_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

    raise RuntimeError("Docker Desktop foi instalado, mas não pôde ser iniciado.")


def _start_macos() -> None:
    print("[docker] Iniciando Docker Desktop...")

    if _succeeds(
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

    _run(["open", "-a", "Docker"])


def _start_linux() -> None:
    print("[docker] Iniciando Docker Engine...")
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
    elif shutil.which("service"):
        _run(
            [
                *prefix,
                "service",
                "docker",
                "start",
            ],
            check=False,
        )


def _start_runtime(system: str) -> None:
    starters = {
        "Windows": _start_windows,
        "Darwin": _start_macos,
        "Linux": _start_linux,
    }
    starters[system]()


def _resolve_linux() -> list[str] | None:
    if _succeeds(["docker", "info"]):
        return ["docker"]

    if (
        os.geteuid() != 0
        and shutil.which("sudo")
        and _succeeds(
            ["sudo", "docker", "info"],
            timeout=30,
        )
    ):
        print("[docker] Usando sudo para acessar o daemon.")
        return ["sudo", "docker"]

    return None


def _resolve_running(system: str) -> list[str] | None:
    if shutil.which("docker") is None:
        return None

    if system == "Linux":
        return _resolve_linux()

    if _succeeds(["docker", "info"]):
        return ["docker"]

    return None


def _wait_for_docker(
    command: Sequence[str],
    timeout_seconds: float,
) -> bool:
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        if _succeeds([*command, "info"]):
            return True

        time.sleep(POLL_INTERVAL_SECONDS)

    return False


def _ensure_compose(
    docker_command: Sequence[str],
    system: str,
) -> None:
    if _succeeds([*docker_command, "compose", "version"]):
        return

    if system != "Linux":
        raise RuntimeError("Docker Compose não está disponível no Docker Desktop.")

    prefix = _linux_admin_prefix()
    print("[docker] Instalando Docker Compose plugin...")

    if shutil.which("apt-get"):
        _run([*prefix, "apt-get", "update"])
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
            "Compose está ausente e o gerenciador Linux não é suportado."
        )

    if not _succeeds([*docker_command, "compose", "version"]):
        raise RuntimeError("Docker Compose plugin continua indisponível.")


def _print_versions(
    docker_command: Sequence[str],
) -> list[str]:
    docker_version = _run(
        [*docker_command, "--version"],
        capture_output=True,
    ).stdout.strip()
    compose_version = _run(
        [*docker_command, "compose", "version"],
        capture_output=True,
    ).stdout.strip()

    print(f"[docker] {docker_version}")
    print(f"[docker] {compose_version}")
    print("[docker] Runtime pronto para a suíte.")

    return list(docker_command)


def ensure_docker(
    *,
    install_policy: DockerInstallPolicy = "ask",
) -> list[str]:
    system = platform.system()
    labels = {
        "Windows": "Windows",
        "Darwin": "macOS",
        "Linux": "Linux",
    }

    if system not in labels:
        raise RuntimeError(f"Sistema operacional não suportado: {system}.")

    _refresh_docker_path()
    docker_command = _resolve_running(system)

    if docker_command is not None:
        _ensure_compose(docker_command, system)
        return _print_versions(docker_command)

    if system == "Windows":
        _ensure_windows_wsl(install_policy)

    if shutil.which("docker") is None:
        component = (
            "Docker Desktop com WSL 2 (inclui aceite dos termos do Docker Desktop)"
            if system == "Windows"
            else "Docker"
        )

        if not _allowed(
            install_policy,
            component,
            labels[system],
        ):
            raise RuntimeError(
                "Docker não está instalado e o bootstrap não foi autorizado."
            )

        _install_docker(system)
        _refresh_docker_path()

        cli_ready = (
            _wait_for_windows_docker_cli()
            if system == "Windows"
            else shutil.which("docker") is not None
        )

        if not cli_ready:
            raise RuntimeError(
                "Docker foi instalado, mas o CLI não ficou disponível na "
                "sessão atual. Feche e abra o terminal e execute novamente."
            )

    _start_runtime(system)

    if system == "Linux":
        if _wait_for_docker(["docker"], 30):
            docker_command = ["docker"]
        else:
            docker_command = _resolve_linux()
    elif _wait_for_docker(
        ["docker"],
        DOCKER_START_TIMEOUT_SECONDS,
    ):
        docker_command = ["docker"]

    if docker_command is None:
        detail = {
            "Windows": (
                "Verifique se o WSL 2 concluiu a ativação e se o Docker Desktop "
                "consegue iniciar. Se o próprio WSL/Docker reportar erro de "
                "virtualização, confirme Intel VT-x/AMD-V/SVM no BIOS/UEFI."
            ),
            "Darwin": (
                "Conclua qualquer configuração, permissão ou aceite "
                "de licença solicitado pelo Docker Desktop."
            ),
            "Linux": ("Verifique o serviço docker e as permissões do usuário."),
        }[system]

        raise RuntimeError("Docker não ficou disponível. " + detail)

    _ensure_compose(docker_command, system)
    return _print_versions(docker_command)
