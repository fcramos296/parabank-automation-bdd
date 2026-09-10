from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = PROJECT_ROOT / "compose.yaml"


def _health_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/index.htm"


def parabank_is_ready(base_url: str) -> bool:
    request = Request(
        _health_url(base_url),
        headers={
            "User-Agent": "parabank-automation-bdd/1.0",
        },
    )

    opener = build_opener(
        ProxyHandler({})
    )

    try:
        with opener.open(
            request,
            timeout=3,
        ) as response:
            if response.status >= 400:
                return False

            body = response.read(
                128 * 1024
            ).decode(
                "utf-8",
                errors="ignore",
            )

            return "ParaBank" in body

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
    ):
        return False


def _validate_docker() -> None:
    if shutil.which("docker") is None:
        raise RuntimeError(
            "Docker não foi encontrado no PATH. "
            "Instale Docker Desktop ou Docker Engine "
            "antes de executar a suíte local."
        )

    try:
        subprocess.run(
            ["docker", "info"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Docker foi encontrado, mas o daemon "
            "não está disponível. Verifique se o "
            "Docker está iniciado."
        ) from exc

    try:
        subprocess.run(
            ["docker", "compose", "version"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "O plugin Docker Compose não está disponível."
        ) from exc


def _compose_command(
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_FILE),
            *args,
        ],
        cwd=PROJECT_ROOT,
        check=check,
    )


def _show_container_logs() -> None:
    print()
    print("[environment] Últimos logs do ParaBank:")
    print()

    _compose_command(
        "logs",
        "--no-color",
        "--tail",
        "100",
        "parabank",
        check=False,
    )


def recreate_local_parabank(
    *,
    base_url: str,
    startup_timeout_seconds: float,
) -> None:
    if not COMPOSE_FILE.exists():
        raise FileNotFoundError(
            "compose.yaml não foi encontrado."
        )

    _validate_docker()

    print(
        "[environment] Recriando ParaBank local "
        "com banco limpo..."
    )

    _compose_command(
        "down",
        "--volumes",
        "--remove-orphans",
        check=False,
    )

    try:
        _compose_command(
            "up",
            "-d",
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Não foi possível iniciar o ParaBank "
            "via Docker Compose."
        ) from exc

    deadline = (
        time.monotonic()
        + startup_timeout_seconds
    )

    while time.monotonic() < deadline:
        if parabank_is_ready(base_url):
            print(
                "[environment] ParaBank local está pronto."
            )
            return

        time.sleep(2)

    _show_container_logs()

    raise RuntimeError(
        "O container ParaBank foi iniciado, mas a "
        "aplicação não ficou disponível dentro do "
        "limite configurado."
    )


def stop_local_parabank() -> None:
    if shutil.which("docker") is None:
        return

    print(
        "[environment] Encerrando ParaBank local..."
    )

    _compose_command(
        "down",
        "--volumes",
        "--remove-orphans",
        check=False,
    )
