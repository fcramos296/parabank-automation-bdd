from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Sequence
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


def _compose_command(
    docker_command: Sequence[str],
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            *docker_command,
            "compose",
            "-f",
            str(COMPOSE_FILE),
            *args,
        ],
        cwd=PROJECT_ROOT,
        check=check,
    )


def _show_container_logs(
    docker_command: Sequence[str],
) -> None:
    print()
    print("[environment] Últimos logs do ParaBank:")
    print()

    _compose_command(
        docker_command,
        "logs",
        "--no-color",
        "--tail",
        "100",
        "parabank",
        check=False,
    )


def recreate_local_parabank(
    *,
    docker_command: Sequence[str],
    base_url: str,
    startup_timeout_seconds: float,
) -> None:
    if not COMPOSE_FILE.exists():
        raise FileNotFoundError(
            "compose.yaml não foi encontrado."
        )

    print(
        "[environment] Recriando ParaBank local "
        "com banco limpo..."
    )

    _compose_command(
        docker_command,
        "down",
        "--volumes",
        "--remove-orphans",
        check=False,
    )

    try:
        _compose_command(
            docker_command,
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

    _show_container_logs(
        docker_command
    )

    raise RuntimeError(
        "O container ParaBank foi iniciado, mas a "
        "aplicação não ficou disponível dentro do "
        "limite configurado."
    )


def stop_local_parabank(
    docker_command: Sequence[str],
) -> None:
    print(
        "[environment] Encerrando ParaBank local..."
    )

    _compose_command(
        docker_command,
        "down",
        "--volumes",
        "--remove-orphans",
        check=False,
    )
