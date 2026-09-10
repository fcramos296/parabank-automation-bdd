from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from bootstrap_docker import ensure_docker
from config.settings import settings
from configure_env import ensure_environment
from parabank_env import (
    recreate_local_parabank,
    stop_local_parabank,
)


VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
REQUIREMENTS_HASH_FILE = VENV_DIR / ".requirements.sha256"
REPORTS_DIR = PROJECT_ROOT / "reports"
ALLURE_RESULTS_DIR = REPORTS_DIR / "allure-results"

SUPPORTED_BROWSERS = (
    "chromium",
    "firefox",
    "webkit",
)

FEATURE_SCOPES = {
    "login": PROJECT_ROOT / "features" / "login.feature",
    "registration": (PROJECT_ROOT / "features" / "registration.feature"),
    "transfer": (PROJECT_ROOT / "features" / "transfer.feature"),
}

MINIMUM_PYTHON = (
    3,
    10,
)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("ParaBank local Docker automation runner."),
        formatter_class=(argparse.ArgumentDefaultsHelpFormatter),
    )

    parser.add_argument(
        "--scope",
        choices=tuple(FEATURE_SCOPES),
        help=("Executa apenas uma feature específica."),
    )

    parser.add_argument(
        "--tags",
        help=("Filtro de tags do Behave. Exemplo: --tags '@smoke'"),
    )

    parser.add_argument(
        "--browser",
        choices=SUPPORTED_BROWSERS,
        default="chromium",
        help=("Browser utilizado pelo Playwright."),
    )

    parser.add_argument(
        "--headed",
        action="store_true",
        help=("Executa com o navegador visível."),
    )

    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help=(
            "Não cria venv, não instala dependências "
            "e não instala browser. O ambiente Docker "
            "continua sendo preparado normalmente."
        ),
    )

    parser.add_argument(
        "--keep-environment",
        action="store_true",
        help=(
            "Mantém o container ParaBank ativo após a execução para inspeção manual."
        ),
    )

    docker_group = parser.add_mutually_exclusive_group()

    docker_group.add_argument(
        "--install-docker",
        action="store_true",
        help=(
            "Autoriza a instalação automática do Docker "
            "quando ele não estiver disponível, sem "
            "perguntar antes. Pode solicitar privilégios "
            "administrativos do sistema operacional."
        ),
    )

    docker_group.add_argument(
        "--no-docker-install",
        action="store_true",
        help=(
            "Nunca instala Docker automaticamente. Falha "
            "com instruções quando Docker não estiver "
            "disponível."
        ),
    )

    return parser.parse_args(argv)


def validate_python_version() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        expected = ".".join(str(part) for part in MINIMUM_PYTHON)

        current = (
            f"{sys.version_info.major}."
            f"{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        )

        raise RuntimeError(
            "Versão do Python não suportada. "
            f"Encontrado: {current}. "
            f"Requerido: Python {expected}+."
        )


def docker_install_policy(
    args: argparse.Namespace,
) -> str:
    if args.install_docker:
        return "always"

    if args.no_docker_install:
        return "never"

    return "ask"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"


def create_virtualenv() -> None:
    python_path = venv_python()

    if VENV_DIR.exists() and python_path.exists():
        print("[setup] Ambiente virtual .venv já existe.")
        return

    if VENV_DIR.exists():
        print("[setup] .venv incompleta encontrada; recriando...")
        shutil.rmtree(VENV_DIR)

    print("[setup] Criando ambiente virtual .venv...")

    builder = venv.EnvBuilder(
        with_pip=True,
        clear=False,
        symlinks=(os.name != "nt"),
    )

    builder.create(VENV_DIR)

    if not python_path.exists():
        raise RuntimeError(
            "O ambiente virtual foi criado, mas o executável Python não foi encontrado."
        )

    print("[setup] Ambiente virtual criado.")


def file_sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def requirements_changed() -> bool:
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError("requirements.txt não foi encontrado.")

    if not REQUIREMENTS_HASH_FILE.exists():
        return True

    current_hash = file_sha256(REQUIREMENTS_FILE)

    stored_hash = REQUIREMENTS_HASH_FILE.read_text(encoding="utf-8").strip()

    return current_hash != stored_hash


def save_requirements_hash() -> None:
    REQUIREMENTS_HASH_FILE.write_text(
        file_sha256(REQUIREMENTS_FILE),
        encoding="utf-8",
    )


def run_command(
    command: Sequence[str | Path],
    *,
    cwd: Path = PROJECT_ROOT,
    check: bool = True,
) -> subprocess.CompletedProcess:
    normalized = [str(item) for item in command]

    return subprocess.run(
        normalized,
        cwd=cwd,
        check=check,
    )


def install_dependencies() -> None:
    python_path = venv_python()

    if not requirements_changed():
        print("[setup] Dependências já estão atualizadas.")
        return

    print("[setup] Instalando/atualizando dependências...")

    run_command(
        [
            python_path,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
        ]
    )

    run_command(
        [
            python_path,
            "-m",
            "pip",
            "install",
            "-r",
            REQUIREMENTS_FILE,
        ]
    )

    save_requirements_hash()

    print("[setup] Dependências instaladas.")


def ensure_playwright_browser(
    browser: str,
) -> None:
    print(f"[setup] Ensuring Playwright browser is installed: {browser}")

    run_command(
        [
            venv_python(),
            "-m",
            "playwright",
            "install",
            browser,
        ]
    )


def setup_project(
    browser: str,
) -> None:
    create_virtualenv()
    install_dependencies()
    ensure_playwright_browser(browser)


def prepare_allure_results() -> None:
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if ALLURE_RESULTS_DIR.exists():
        print("[report] Limpando resultados Allure anteriores...")
        shutil.rmtree(ALLURE_RESULTS_DIR)

    ALLURE_RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def resolve_runner_python(
    skip_setup: bool,
) -> Path:
    if skip_setup:
        return Path(sys.executable)

    python_path = venv_python()

    if not python_path.exists():
        raise RuntimeError(".venv Python não foi encontrado.")

    return python_path


def build_behave_command(
    *,
    python_path: Path,
    scope: str | None,
    tags: str | None,
    browser: str,
    headed: bool,
) -> list[str]:
    command = [
        str(python_path),
        "-m",
        "behave",
    ]

    if scope:
        feature_path = FEATURE_SCOPES[scope]

        if not feature_path.exists():
            raise FileNotFoundError(
                f"Feature não encontrada para o escopo '{scope}': {feature_path}"
            )

        command.append(str(feature_path.relative_to(PROJECT_ROOT)))

    if tags:
        command.extend(
            [
                "--tags",
                tags,
            ]
        )

    command.extend(
        [
            "-D",
            ("headless=false" if headed else "headless=true"),
            "-D",
            f"browser={browser}",
        ]
    )

    return command


def format_command(
    command: Sequence[str],
) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(list(command))

    import shlex

    return shlex.join(command)


def run_behave(
    *,
    python_path: Path,
    scope: str | None,
    tags: str | None,
    browser: str,
    headed: bool,
) -> int:
    command = build_behave_command(
        python_path=python_path,
        scope=scope,
        tags=tags,
        browser=browser,
        headed=headed,
    )

    print("[run] " + format_command(command))

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
    )

    return int(completed.returncode)


def print_execution_summary(
    args: argparse.Namespace,
) -> None:
    scope = args.scope if args.scope else "suite completa"

    execution_mode = "headed" if args.headed else "headless"

    policy = docker_install_policy(args)

    docker_setup = {
        "ask": "automático com confirmação se ausente",
        "always": "instalação autorizada",
        "never": "instalação desabilitada",
    }[policy]

    print()
    print("=" * 60)
    print("PARABANK AUTOMATION - LOCAL DOCKER")
    print("=" * 60)
    print(f"Escopo........: {scope}")

    if args.tags:
        print(f"Tags..........: {args.tags}")

    print(f"Base URL......: {settings.BASE_URL}")
    print("Backend.......: direct")
    print("Browser net...: direct")
    print(f"Browser.......: {args.browser}")
    print(f"Modo..........: {execution_mode}")
    print(f"Docker........: {docker_setup}")
    print(
        "Setup Python..: "
        + ("ignorado (--skip-setup)" if args.skip_setup else "automático")
    )
    print("=" * 60)
    print()


def main(
    argv: Sequence[str] | None = None,
) -> int:
    environment_started = False
    docker_command: list[str] | None = None
    args: argparse.Namespace | None = None

    try:
        validate_python_version()
        args = parse_args(argv)

        print("[env] Verificando configuração do ambiente...")
        ensure_environment()
        print("[env] Configuração concluída.")

        print_execution_summary(args)

        docker_command = ensure_docker(install_policy=docker_install_policy(args))

        recreate_local_parabank(
            docker_command=docker_command,
            base_url=settings.BASE_URL,
            startup_timeout_seconds=(settings.LOCAL_STARTUP_TIMEOUT_SECONDS),
        )
        environment_started = True

        if not args.skip_setup:
            setup_project(args.browser)
        else:
            print(
                "[setup] --skip-setup informado; "
                "pulando venv, dependências e "
                "instalação do Playwright."
            )

        prepare_allure_results()

        runner_python = resolve_runner_python(args.skip_setup)

        exit_code = run_behave(
            python_path=runner_python,
            scope=args.scope,
            tags=args.tags,
            browser=args.browser,
            headed=args.headed,
        )

        print()

        if exit_code == 0:
            print("[run] Suite concluída com sucesso.")
        else:
            print("[run] Suite concluída com falhas ou erros.")

        print(f"[report] Resultados Allure: {ALLURE_RESULTS_DIR}")

        return exit_code

    except KeyboardInterrupt:
        print()
        print("[run] Execução cancelada pelo usuário.")
        return 130

    except subprocess.CalledProcessError as exc:
        print()
        print("[run][ERRO] Um comando de setup falhou.")
        print("[run][ERRO] Comando: " + format_command([str(item) for item in exc.cmd]))
        print(f"[run][ERRO] Código de saída: {exc.returncode}")
        return int(exc.returncode or 1)

    except Exception as exc:
        print()
        print(f"[run][ERRO] {exc}")
        return 1

    finally:
        keep_environment = bool(args and args.keep_environment)

        if environment_started and docker_command is not None and not keep_environment:
            stop_local_parabank(docker_command)
        elif environment_started:
            print("[environment] ParaBank local mantido ativo (--keep-environment).")


if __name__ == "__main__":
    raise SystemExit(main())
