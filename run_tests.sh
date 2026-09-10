#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

ALLURE_VERSION="3.17.0"
ALLURE_CONFIG="allurerc.yml"
ALLURE_RESULTS="reports/allure-results"
ALLURE_REPORT="reports/allure-report"
ALLURE_LOG="reports/allure-server.log"

TEST_EXIT_CODE=0
GENERATE_REPORT=true
ALLURE_READY=false
SCOPE_ARGS=()
HEADED_ARGS=()
BROWSER="chromium"
PYTHON_CMD=""
ALLURE_SCOPE="full"

header() {
    clear 2>/dev/null || true
    echo "============================================================"
    echo
    echo "             PARABANK AUTOMATION BDD"
    echo
    echo "              TOPAZ - QA AUTOMATION"
    echo
    echo "        Playwright + Python + Behave + Docker"
    echo
    echo "============================================================"
    echo
}

pause_execution() {
    echo
    read -r -p "Pressione ENTER para continuar..."
}

run_admin() {
    if [[ "$(id -u)" -eq 0 ]]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        echo "[ERRO] A operacao exige root/sudo."
        return 1
    fi
}

python_supported() {
    "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

find_python() {
    local candidate
    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1 && python_supported "$candidate"; then
            PYTHON_CMD="$candidate"
            return 0
        fi
    done
    return 1
}

refresh_homebrew() {
    if [[ -x /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        return 0
    fi
    if [[ -x /usr/local/bin/brew ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
        return 0
    fi
    return 1
}

install_homebrew() {
    command -v brew >/dev/null 2>&1 && return 0
    refresh_homebrew && return 0

    command -v curl >/dev/null 2>&1 || {
        echo "[ERRO] curl nao foi encontrado no macOS."
        return 1
    }

    echo "[setup] Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || return 1
    refresh_homebrew
}

install_python() {
    case "$(uname -s)" in
        Darwin)
            install_homebrew || return 1
            brew install python@3.12 || return 1
            hash -r 2>/dev/null || true
            ;;
        Linux)
            if command -v apt-get >/dev/null 2>&1; then
                run_admin apt-get update || return 1
                run_admin apt-get install -y python3 python3-venv python3-pip curl ca-certificates || return 1
            elif command -v dnf >/dev/null 2>&1; then
                run_admin dnf install -y python3 python3-pip curl ca-certificates || return 1
            elif command -v yum >/dev/null 2>&1; then
                run_admin yum install -y python3 python3-pip curl ca-certificates || return 1
            elif command -v pacman >/dev/null 2>&1; then
                run_admin pacman -S --noconfirm python python-pip curl ca-certificates || return 1
            elif command -v zypper >/dev/null 2>&1; then
                run_admin zypper --non-interactive install python3 python3-pip curl ca-certificates || return 1
            else
                echo "[ERRO] Gerenciador de pacotes Linux nao suportado."
                return 1
            fi
            hash -r 2>/dev/null || true
            ;;
        *)
            echo "[ERRO] Sistema nao suportado pelo bootstrap de Python."
            return 1
            ;;
    esac

    find_python
}

check_project() {
    echo "[CHECK] Validando estrutura do projeto..."

    local path
    for path in \
        scripts/run.py \
        scripts/configure_env.py \
        requirements.txt \
        features \
        "$ALLURE_CONFIG" \
        assets/topaz-logo.png; do
        if [[ ! -e "$path" ]]; then
            echo "[ERRO] $path nao foi encontrado."
            return 1
        fi
    done

    echo "[OK] Estrutura principal encontrada."
}

check_python() {
    echo
    echo "[CHECK] Verificando Python..."

    if find_python; then
        echo "[OK] $("$PYTHON_CMD" --version 2>&1)"
        return 0
    fi

    echo "[INFO] Python 3.10+ nao foi encontrado."
    echo "O requirements.txt instala bibliotecas, mas nao o interpretador."
    echo
    read -r -p "Deseja instalar Python automaticamente? [S/n]: " answer
    answer="${answer:-S}"

    [[ "$answer" =~ ^[Ss]$ ]] || return 1
    install_python || return 1

    echo "[OK] $("$PYTHON_CMD" --version 2>&1)"
}

configure_env() {
    echo
    echo "[CHECK] Verificando configuracao do ambiente..."
    "$PYTHON_CMD" scripts/configure_env.py
}

select_scope() {
    while true; do
        echo "============================================================"
        echo "ESCOLHA O ESCOPO"
        echo "============================================================"
        echo
        echo "  [1] Suite completa"
        echo "  [2] Smoke Tests"
        echo "  [3] Login"
        echo "  [4] Registro"
        echo "  [5] Transferencia"
        echo
        read -r -p "Escolha [1-5] (padrao: 1): " choice
        choice="${choice:-1}"
        SCOPE_ARGS=()
        ALLURE_SCOPE="full"

        case "$choice" in
            1) SCOPE_DESCRIPTION="Suite completa"; return ;;
            2) SCOPE_DESCRIPTION="Smoke Tests (@smoke)"; SCOPE_ARGS=(--tags "@smoke"); ALLURE_SCOPE="smoke"; return ;;
            3) SCOPE_DESCRIPTION="Login"; SCOPE_ARGS=(--scope login); ALLURE_SCOPE="login"; return ;;
            4) SCOPE_DESCRIPTION="Registro"; SCOPE_ARGS=(--scope registration); ALLURE_SCOPE="registration"; return ;;
            5) SCOPE_DESCRIPTION="Transferencia"; SCOPE_ARGS=(--scope transfer); ALLURE_SCOPE="transfer"; return ;;
            *) echo "[AVISO] Opcao invalida." ;;
        esac
    done
}

select_browser() {
    while true; do
        echo
        echo "============================================================"
        echo "ESCOLHA O NAVEGADOR"
        echo "============================================================"
        echo
        echo "  [1] Chromium - recomendado"
        echo "  [2] Firefox"
        echo "  [3] WebKit"
        echo
        read -r -p "Escolha [1-3] (padrao: 1): " choice
        choice="${choice:-1}"

        case "$choice" in
            1) BROWSER="chromium"; return ;;
            2) BROWSER="firefox"; return ;;
            3) BROWSER="webkit"; return ;;
            *) echo "[AVISO] Opcao invalida." ;;
        esac
    done
}

select_mode() {
    echo
    read -r -p "Executar exibindo o navegador? [s/N]: " answer
    if [[ "$answer" =~ ^[Ss]$ ]]; then
        HEADED_ARGS=(--headed)
        MODE_DESCRIPTION="Headed - navegador visivel"
    else
        HEADED_ARGS=()
        MODE_DESCRIPTION="Headless"
    fi
}

select_report() {
    echo
    echo "============================================================"
    echo "RELATORIO ALLURE 3 - TOPAZ"
    echo "============================================================"
    echo
    read -r -p "Deseja gerar o relatorio Allure personalizado ao final? [S/n]: " answer
    answer="${answer:-S}"

    if [[ "$answer" =~ ^[Ss]$ ]]; then
        GENERATE_REPORT=true
        REPORT_DESCRIPTION="Allure 3 Awesome - Topaz"
    else
        GENERATE_REPORT=false
        REPORT_DESCRIPTION="Apenas allure-results"
    fi
}

install_node() {
    echo "[setup] Node.js/npm nao foram encontrados."
    read -r -p "Deseja instalar Node.js automaticamente para gerar o Allure? [S/n]: " answer
    answer="${answer:-S}"
    [[ "$answer" =~ ^[Ss]$ ]] || return 1

    if [[ "$(uname -s)" == "Darwin" ]]; then
        install_homebrew || return 1
        brew install node || return 1
    elif command -v apt-get >/dev/null 2>&1; then
        run_admin apt-get update && run_admin apt-get install -y nodejs npm || return 1
    elif command -v dnf >/dev/null 2>&1; then
        run_admin dnf install -y nodejs npm || return 1
    elif command -v yum >/dev/null 2>&1; then
        run_admin yum install -y nodejs npm || return 1
    elif command -v pacman >/dev/null 2>&1; then
        run_admin pacman -S --noconfirm nodejs npm || return 1
    elif command -v zypper >/dev/null 2>&1; then
        run_admin zypper --non-interactive install nodejs npm || return 1
    else
        echo "[ERRO] Nao foi possivel instalar Node.js automaticamente."
        return 1
    fi

    hash -r 2>/dev/null || true
}

ensure_allure3() {
    echo
    echo "============================================================"
    echo "PREPARANDO ALLURE 3"
    echo "============================================================"
    echo

    if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
        install_node || return 1
    fi

    if ! npx --yes "allure@$ALLURE_VERSION" --version >/dev/null 2>&1; then
        echo "[ERRO] Nao foi possivel preparar Allure $ALLURE_VERSION."
        return 1
    fi

    echo "[OK] Allure $(npx --yes "allure@$ALLURE_VERSION" --version | head -n 1) pronto."
    ALLURE_READY=true
}

generate_allure_report() {
    echo
    echo "============================================================"
    echo "RELATORIO ALLURE 3 - TOPAZ"
    echo "============================================================"
    echo

    [[ -d "$ALLURE_RESULTS" ]] || { echo "[AVISO] Resultados Allure nao encontrados."; return; }
    [[ "$GENERATE_REPORT" == true ]] || { echo "[INFO] Geracao do HTML nao foi solicitada."; return; }
    [[ "$ALLURE_READY" == true ]] || { echo "[AVISO] Allure 3 nao esta disponivel."; return; }

    rm -rf "$ALLURE_REPORT"
    export ALLURE_SCOPE
    export ALLURE_BROWSER="$BROWSER"

    echo "[ALLURE] Gerando relatorio personalizado..."
    echo "[ALLURE] Config....: $ALLURE_CONFIG"
    echo "[ALLURE] Tema......: Topaz / Awesome / dark"
    echo "[ALLURE] Escopo....: $ALLURE_SCOPE"
    echo "[ALLURE] Browser...: $ALLURE_BROWSER"
    echo

    if ! npx --yes "allure@$ALLURE_VERSION" generate "$ALLURE_RESULTS" --config "./$ALLURE_CONFIG" --output "$ALLURE_REPORT"; then
        echo "[ERRO] Nao foi possivel gerar o relatorio personalizado."
        return
    fi

    [[ -f "$ALLURE_REPORT/index.html" ]] || { echo "[ERRO] index.html do Allure nao foi encontrado."; return; }

    echo "[OK] Relatorio Topaz gerado: $ALLURE_REPORT"
    echo
    read -r -p "Deseja abrir o relatorio Allure agora? [S/n]: " answer
    answer="${answer:-S}"

    if [[ "$answer" =~ ^[Ss]$ ]]; then
        mkdir -p "$(dirname "$ALLURE_LOG")"
        nohup npx --yes "allure@$ALLURE_VERSION" open "$ALLURE_REPORT" >"$ALLURE_LOG" 2>&1 &
        echo "[OK] Servidor Allure iniciado."
    fi
}

execute_tests() {
    local run_args=(scripts/run.py --browser "$BROWSER")
    run_args+=("${SCOPE_ARGS[@]}")
    run_args+=("${HEADED_ARGS[@]}")

    "$PYTHON_CMD" "${run_args[@]}"
    TEST_EXIT_CODE=$?

    if [[ "$TEST_EXIT_CODE" -eq 0 ]]; then
        echo "[OK] Execucao concluida com sucesso."
    else
        echo "[ATENCAO] Execucao terminou com falhas ou erros: $TEST_EXIT_CODE"
    fi

    generate_allure_report
}

main() {
    header
    echo "Este assistente prepara e executa o ParaBank local em Docker."
    echo "O relatorio utiliza Allure 3 Awesome com identidade visual Topaz."
    pause_execution

    header
    check_project || exit 1
    check_python || exit 1
    configure_env || exit 1

    if [[ "$#" -gt 0 ]]; then
        "$PYTHON_CMD" scripts/run.py "$@"
        exit $?
    fi

    while true; do
        header
        select_scope
        select_browser
        select_mode
        select_report

        echo
        echo "Resumo: $SCOPE_DESCRIPTION | $BROWSER | $MODE_DESCRIPTION | $REPORT_DESCRIPTION"
        echo
        read -r -p "Deseja iniciar a execucao? [S/n]: " answer
        answer="${answer:-S}"
        [[ "$answer" =~ ^[Ss]$ ]] || exit 0

        if [[ "$GENERATE_REPORT" == true ]]; then
            ensure_allure3 || GENERATE_REPORT=false
        fi

        execute_tests

        echo
        echo "============================================================"
        if [[ "$TEST_EXIT_CODE" -eq 0 ]]; then
            echo "Status dos testes: SUCESSO"
        else
            echo "Status dos testes: FALHA / ERRO"
        fi
        [[ -f "$ALLURE_REPORT/index.html" ]] && echo "Relatorio HTML: $ALLURE_REPORT"
        echo "============================================================"
        echo

        read -r -p "Deseja realizar uma nova execucao? [s/N]: " again
        [[ "$again" =~ ^[Ss]$ ]] || exit "$TEST_EXIT_CODE"
    done
}

main "$@"
