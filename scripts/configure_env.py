from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE = PROJECT_ROOT / ".env.example"


def ensure_environment() -> None:
    """
    Prepara apenas a configuração local do projeto.

    Nenhum token ou serviço externo é necessário nesta
    branch. Se .env não existir, ele é criado a partir de
    .env.example. Variáveis antigas do ambiente público são
    ignoradas pela configuração local.
    """

    if ENV_FILE.exists():
        print(
            "[env] Arquivo .env já existe. "
            "A execução utilizará o ParaBank local em Docker."
        )
        return

    if not ENV_EXAMPLE_FILE.exists():
        raise FileNotFoundError(".env.example não foi encontrado.")

    ENV_FILE.write_text(
        ENV_EXAMPLE_FILE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    print("[env] Arquivo .env criado a partir de .env.example.")


def main() -> int:
    try:
        ensure_environment()
        return 0
    except Exception as exc:
        print(f"[ERRO] Configuração do ambiente: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
