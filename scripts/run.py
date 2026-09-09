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

from configure_env import ensure_environment


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

VENV_DIR = PROJECT_ROOT / ".venv"

REQUIREMENTS_FILE = (
    PROJECT_ROOT
    / "requirements.txt"
)

REQUIREMENTS_HASH_FILE = (
    VENV_DIR
    / ".requirements.sha256"
)

REPORTS_DIR = (
    PROJECT_ROOT
    / "reports"
)

ALLURE_RESULTS_DIR = (
    REPORTS_DIR
    / "allure-results"
)


# ============================================================
# SUPPORTED CONFIGURATION
# ============================================================

SUPPORTED_BROWSERS = (
    "chromium",
    "firefox",
    "webkit",
)

FEATURE_SCOPES = {
    "login": (
        PROJECT_ROOT
        / "features"
        / "login.feature"
    ),
    "registration": (
        PROJECT_ROOT
        / "features"
        / "registration.feature"
    ),
    "transfer": (
        PROJECT_ROOT
        / "features"
        / "transfer.feature"
    ),
}

MINIMUM_PYTHON = (
    3,
    10,
)


# ============================================================
# CLI
# ============================================================

def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "ParaBank automation runner."
        ),
        formatter_class=(
            argparse.ArgumentDefaultsHelpFormatter
        ),
    )

    parser.add_argument(
        "--scope",
        choices=tuple(
            FEATURE_SCOPES
        ),
        help=(
            "Executa apenas uma feature específica."
        ),
    )

    parser.add_argument(
        "--tags",
        help=(
            "Filtro de tags do Behave. "
            "Exemplo: --tags '@smoke'"
        ),
    )

    parser.add_argument(
        "--browser",
        choices=SUPPORTED_BROWSERS,
        default="chromium",
        help=(
            "Browser utilizado pelo Playwright."
        ),
    )

    parser.add_argument(
        "--headed",
        action="store_true",
        help=(
            "Executa com o navegador visível."
        ),
    )

    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help=(
            "Não cria venv, não instala dependências "
            "e não instala browser. "
            "Útil para CI após o setup já ter sido feito."
        ),
    )

    return parser.parse_args(
        argv
    )


# ============================================================
# PYTHON VALIDATION
# ============================================================

def validate_python_version() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        expected = ".".join(
            str(part)
            for part in MINIMUM_PYTHON
        )

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


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

def configure_environment() -> None:
    """
    Ensures SCRAPE_DO_TOKEN is available.

    Local execution:
        - creates .env if needed;
        - interactively requests the token if missing.

    CI/non-interactive execution:
        - uses SCRAPE_DO_TOKEN from environment;
        - never opens an interactive prompt.
    """

    print(
        "[env] Verificando configuração "
        "do ambiente..."
    )

    ensure_environment()

    print(
        "[env] Configuração concluída."
    )


# ============================================================
# VIRTUAL ENVIRONMENT
# ============================================================

def venv_python() -> Path:
    if os.name == "nt":
        return (
            VENV_DIR
            / "Scripts"
            / "python.exe"
        )

    return (
        VENV_DIR
        / "bin"
        / "python"
    )


def create_virtualenv() -> None:
    python_path = (
        venv_python()
    )

    if (
        VENV_DIR.exists()
        and python_path.exists()
    ):
        print(
            "[setup] Ambiente virtual "
            ".venv já existe."
        )
        return

    if VENV_DIR.exists():
        print(
            "[setup] .venv incompleta encontrada; "
            "recriando..."
        )

        shutil.rmtree(
            VENV_DIR
        )

    print(
        "[setup] Criando ambiente virtual .venv..."
    )

    builder = venv.EnvBuilder(
        with_pip=True,
        clear=False,
        symlinks=(
            os.name != "nt"
        ),
    )

    builder.create(
        VENV_DIR
    )

    if not python_path.exists():
        raise RuntimeError(
            "O ambiente virtual foi criado, "
            "mas o executável Python não "
            "foi encontrado."
        )

    print(
        "[setup] Ambiente virtual criado."
    )


# ============================================================
# REQUIREMENTS
# ============================================================

def file_sha256(
    path: Path,
) -> str:
    digest = (
        hashlib.sha256()
    )

    with path.open(
        "rb"
    ) as file:
        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def requirements_changed() -> bool:
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(
            "requirements.txt não foi encontrado."
        )

    if not REQUIREMENTS_HASH_FILE.exists():
        return True

    current_hash = file_sha256(
        REQUIREMENTS_FILE
    )

    stored_hash = (
        REQUIREMENTS_HASH_FILE
        .read_text(
            encoding="utf-8"
        )
        .strip()
    )

    return (
        current_hash
        != stored_hash
    )


def save_requirements_hash() -> None:
    REQUIREMENTS_HASH_FILE.write_text(
        file_sha256(
            REQUIREMENTS_FILE
        ),
        encoding="utf-8",
    )


def run_command(
    command: Sequence[str | Path],
    *,
    cwd: Path = PROJECT_ROOT,
    check: bool = True,
) -> subprocess.CompletedProcess:
    normalized = [
        str(item)
        for item in command
    ]

    return subprocess.run(
        normalized,
        cwd=cwd,
        check=check,
    )


def install_dependencies() -> None:
    python_path = (
        venv_python()
    )

    if not requirements_changed():
        print(
            "[setup] Dependências já estão "
            "atualizadas."
        )
        return

    print(
        "[setup] requirements.txt mudou "
        "ou é a primeira execução."
    )

    print(
        "[setup] Atualizando pip..."
    )

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

    print(
        "[setup] Instalando dependências..."
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

    print(
        "[setup] Dependências instaladas."
    )


# ============================================================
# PLAYWRIGHT
# ============================================================

def ensure_playwright_browser(
    browser: str,
) -> None:
    python_path = (
        venv_python()
    )

    print(
        "[setup] Ensuring Playwright browser "
        f"is installed: {browser}"
    )

    run_command(
        [
            python_path,
            "-m",
            "playwright",
            "install",
            browser,
        ]
    )


# ============================================================
# REPORTS
# ============================================================

def prepare_allure_results() -> None:
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if ALLURE_RESULTS_DIR.exists():
        print(
            "[report] Limpando resultados "
            "Allure anteriores..."
        )

        shutil.rmtree(
            ALLURE_RESULTS_DIR
        )

    ALLURE_RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# BEHAVE
# ============================================================

def resolve_runner_python(
    skip_setup: bool,
) -> Path:
    """
    Local setup:
        use .venv Python.

    --skip-setup:
        use the current interpreter.

    This makes --skip-setup appropriate for CI, where
    dependencies may already have been installed into
    the runner's Python environment.
    """

    if skip_setup:
        return Path(
            sys.executable
        )

    python_path = (
        venv_python()
    )

    if not python_path.exists():
        raise RuntimeError(
            ".venv Python não foi encontrado."
        )

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
        str(
            python_path
        ),
        "-m",
        "behave",
    ]

    if scope:
        feature_path = (
            FEATURE_SCOPES[
                scope
            ]
        )

        if not feature_path.exists():
            raise FileNotFoundError(
                "Feature não encontrada para "
                f"o escopo '{scope}': "
                f"{feature_path}"
            )

        command.append(
            str(
                feature_path.relative_to(
                    PROJECT_ROOT
                )
            )
        )

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
            (
                "headless=false"
                if headed
                else "headless=true"
            ),
            "-D",
            f"browser={browser}",
        ]
    )

    return command


def format_command(
    command: Sequence[str],
) -> str:
    """
    Human-readable command for logs.

    This command contains no secrets.
    """

    if os.name == "nt":
        return subprocess.list2cmdline(
            list(
                command
            )
        )

    import shlex

    return shlex.join(
        command
    )


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

    print(
        "[run] "
        + format_command(
            command
        )
    )

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
    )

    return int(
        completed.returncode
    )


# ============================================================
# SETUP
# ============================================================

def setup_project(
    browser: str,
) -> None:
    create_virtualenv()

    install_dependencies()

    ensure_playwright_browser(
        browser
    )


# ============================================================
# EXECUTION SUMMARY
# ============================================================

def print_execution_summary(
    args: argparse.Namespace,
) -> None:
    scope = (
        args.scope
        if args.scope
        else "suite completa"
    )

    execution_mode = (
        "headed"
        if args.headed
        else "headless"
    )

    print()
    print(
        "=" * 60
    )
    print(
        "PARABANK AUTOMATION"
    )
    print(
        "=" * 60
    )
    print(
        f"Escopo........: {scope}"
    )

    if args.tags:
        print(
            f"Tags..........: {args.tags}"
        )

    print(
        f"Browser.......: {args.browser}"
    )
    print(
        f"Modo..........: {execution_mode}"
    )
    print(
        "Setup.........: "
        + (
            "ignorado (--skip-setup)"
            if args.skip_setup
            else "automático"
        )
    )
    print(
        "=" * 60
    )
    print()


# ============================================================
# MAIN
# ============================================================

def main(
    argv: Sequence[str] | None = None,
) -> int:
    try:
        validate_python_version()

        args = parse_args(
            argv
        )

        # Environment setup deliberately occurs before
        # venv/dependency setup because configure_env.py
        # uses only Python's standard library.
        #
        # Local:
        #   prompts for token if missing.
        #
        # CI:
        #   reads SCRAPE_DO_TOKEN from environment.
        configure_environment()

        print_execution_summary(
            args
        )

        if not args.skip_setup:
            setup_project(
                args.browser
            )
        else:
            print(
                "[setup] --skip-setup informado; "
                "pulando venv, dependências e "
                "instalação do Playwright."
            )

        prepare_allure_results()

        runner_python = (
            resolve_runner_python(
                args.skip_setup
            )
        )

        exit_code = run_behave(
            python_path=runner_python,
            scope=args.scope,
            tags=args.tags,
            browser=args.browser,
            headed=args.headed,
        )

        print()

        if exit_code == 0:
            print(
                "[run] Suite concluída "
                "com sucesso."
            )
        else:
            print(
                "[run] Suite concluída "
                "com falhas ou erros."
            )

        print(
            "[report] Resultados Allure: "
            f"{ALLURE_RESULTS_DIR}"
        )

        return exit_code

    except KeyboardInterrupt:
        print()
        print(
            "[run] Execução cancelada "
            "pelo usuário."
        )

        return 130

    except subprocess.CalledProcessError as exc:
        print()
        print(
            "[run][ERRO] Um comando de setup "
            "falhou."
        )
        print(
            "[run][ERRO] Comando: "
            + format_command(
                [
                    str(item)
                    for item
                    in exc.cmd
                ]
            )
        )
        print(
            "[run][ERRO] Código de saída: "
            f"{exc.returncode}"
        )

        return int(
            exc.returncode
            or 1
        )

    except Exception as exc:
        print()
        print(
            f"[run][ERRO] {exc}"
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )