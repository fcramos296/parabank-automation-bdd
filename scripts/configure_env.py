from __future__ import annotations

import os
import re
import sys
from pathlib import Path


# ============================================================
# PATHS / CONSTANTS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE = PROJECT_ROOT / ".env.example"

TOKEN_KEY = "SCRAPE_DO_TOKEN"

TOKEN_PLACEHOLDERS = {
    "your_token",
    "your_token_here",
    "seu_token",
    "seu_token_aqui",
    "<token>",
    "<your_token>",
    "token",
}


# ============================================================
# .ENV
# ============================================================

def create_env_if_needed() -> None:
    """
    Cria .env a partir de .env.example quando necessário.

    Se SCRAPE_DO_TOKEN já existir como variável de ambiente,
    como ocorre normalmente no CI, não é necessário criar .env.
    """

    if ENV_FILE.exists():
        return

    if get_token_from_environment():
        return

    if not ENV_EXAMPLE_FILE.exists():
        raise FileNotFoundError(
            ".env.example não foi encontrado."
        )

    ENV_FILE.write_text(
        ENV_EXAMPLE_FILE.read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    print(
        "[env] Arquivo .env criado a partir de .env.example."
    )


def read_env() -> str:
    if not ENV_FILE.exists():
        return ""

    return ENV_FILE.read_text(
        encoding="utf-8"
    )


# ============================================================
# TOKEN VALIDATION
# ============================================================

def normalize_token(
    raw_value: str,
) -> str | None:
    """
    Normaliza e valida um possível valor de token.
    """

    value = (
        raw_value
        .strip()
        .strip('"')
        .strip("'")
        .strip()
    )

    if not value:
        return None

    if value.startswith("#"):
        return None

    if value.lower() in TOKEN_PLACEHOLDERS:
        return None

    return value


def get_token_from_environment() -> str | None:
    """
    Procura SCRAPE_DO_TOKEN nas variáveis de ambiente.

    Isso é utilizado principalmente pelo CI/CD.
    """

    return normalize_token(
        os.getenv(
            TOKEN_KEY,
            "",
        )
    )


def get_token_from_env_file(
    content: str,
) -> str | None:
    """
    Procura SCRAPE_DO_TOKEN dentro do .env.

    [ \\t] é utilizado em vez de \\s para impedir
    que o regex atravesse quebras de linha.
    """

    pattern = re.compile(
        rf"^[ \t]*"
        rf"{re.escape(TOKEN_KEY)}"
        rf"[ \t]*=[ \t]*(.*)$",
        re.MULTILINE,
    )

    matches = pattern.findall(
        content
    )

    for raw_value in reversed(matches):
        token = normalize_token(
            raw_value
        )

        if token:
            return token

    return None


# ============================================================
# TOKEN WRITING
# ============================================================

def write_token(
    content: str,
    token: str,
) -> None:
    """
    Salva SCRAPE_DO_TOKEN no .env.

    Todas as ocorrências anteriores da variável são removidas
    para impedir configurações duplicadas.
    """

    pattern = re.compile(
        rf"^[ \t]*"
        rf"{re.escape(TOKEN_KEY)}"
        rf"[ \t]*=.*$",
        re.MULTILINE,
    )

    cleaned = pattern.sub(
        "",
        content,
    )

    cleaned = re.sub(
        r"\n{3,}",
        "\n\n",
        cleaned,
    ).rstrip()

    if cleaned:
        updated = (
            cleaned
            + "\n\n"
            + f"{TOKEN_KEY}={token}"
            + "\n"
        )
    else:
        updated = (
            f"{TOKEN_KEY}={token}\n"
        )

    ENV_FILE.write_text(
        updated,
        encoding="utf-8",
    )


# ============================================================
# INTERACTIVE MODE
# ============================================================

def is_interactive_terminal() -> bool:
    """
    Retorna True quando existe um terminal humano disponível.

    GitHub Actions e outros processos não interativos
    normalmente retornam False.
    """

    return (
        sys.stdin.isatty()
        and sys.stdout.isatty()
    )


def request_token() -> str:
    """
    Solicita o token mostrando o valor digitado no terminal.
    """

    print()
    print("=" * 60)
    print("CONFIGURAÇÃO DO SCRAPE.DO")
    print("=" * 60)
    print()
    print(
        "Este projeto utiliza Scrape.do nas chamadas de backend."
    )
    print()
    print(
        "A instância pública do ParaBank possui limitações "
        "de rate limiting."
    )
    print(
        "O Scrape.do é utilizado como adapter de infraestrutura"
    )
    print(
        "para preservar a estratégia API-first do framework."
    )
    print()
    print(
        "Para continuar, informe seu token do Scrape.do."
    )
    print()
    print(
        "O token será salvo SOMENTE no arquivo local .env."
    )
    print(
        "O arquivo .env não deve ser versionado no Git."
    )
    print()
    print(
        "O valor digitado ficará visível no terminal."
    )
    print()

    while True:
        token = input(
            "SCRAPE_DO_TOKEN: "
        ).strip()

        token = normalize_token(
            token
        )

        if not token:
            print()
            print(
                "[AVISO] Informe um token válido."
            )
            print()
            continue

        confirmation = input(
            "Confirme o token: "
        ).strip()

        if token != confirmation:
            print()
            print(
                "[AVISO] Os valores informados não coincidem."
            )
            print(
                "Tente novamente."
            )
            print()
            continue

        return token


# ============================================================
# ENVIRONMENT SETUP
# ============================================================

def ensure_environment() -> None:
    """
    Garante que SCRAPE_DO_TOKEN esteja configurado.

    Prioridade:

    1. Variável de ambiente
    2. Arquivo .env local
    3. Prompt interativo

    Em execução não interativa, nenhum prompt é aberto.
    """

    environment_token = (
        get_token_from_environment()
    )

    if environment_token:
        print(
            "[env] SCRAPE_DO_TOKEN encontrado "
            "nas variáveis de ambiente."
        )
        return

    create_env_if_needed()

    content = read_env()

    file_token = get_token_from_env_file(
        content
    )

    if file_token:
        print(
            "[env] SCRAPE_DO_TOKEN já está configurado no .env."
        )
        return

    if not is_interactive_terminal():
        raise RuntimeError(
            "SCRAPE_DO_TOKEN não está configurado. "
            "Em execução não interativa/CI, defina "
            "SCRAPE_DO_TOKEN como variável de ambiente "
            "ou GitHub Actions Secret."
        )

    token = request_token()

    content = read_env()

    write_token(
        content,
        token,
    )

    print()
    print(
        "[OK] SCRAPE_DO_TOKEN configurado com sucesso."
    )
    print(
        "[OK] Token salvo somente no arquivo local .env."
    )


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    try:
        ensure_environment()

        return 0

    except KeyboardInterrupt:
        print()
        print()
        print(
            "[INFO] Configuração cancelada pelo usuário."
        )

        return 130

    except Exception as exc:
        print()
        print(
            f"[ERRO] Configuração do ambiente: {exc}"
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )