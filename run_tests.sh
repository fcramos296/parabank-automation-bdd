#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")" &&
    pwd
)"

cd "$PROJECT_DIR" || exit 1

ALLURE_RESULTS="reports/allure-results"
ALLURE_REPORT="reports/allure-report"
ALLURE_LOG="reports/allure-server.log"

TEST_EXIT_CODE=0
GENERATE_REPORT=true
ALLURE_AVAILABLE=false
ALLURE_MODE=""
SCOPE_ARGS=()
HEADED_ARGS=()
BROWSER="chromium"
PYTHON_CMD=""

header() {
    clear 2>/dev/null || true

    echo "============================================================"
    echo
    echo "             PARABANK AUTOMATION BDD"
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

python_supported() {
    local candidate="$1"

    "$candidate" -c \
        'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
        >/dev/null 2>&1
}

find_python() {
    local candidate

    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1 \
            && python_supported "$candidate"; then
            PYTHON_CMD="$candidate"
            return 0
        fi
    done

    return 1
}

run_admin() {
    if [[ "$(id -u)" -eq 0 ]]; then
        "$@"
        return $?
    fi

    if command -v sudo >/dev/null 2>&1; then
        sudo "$@"
        return $?
    fi

    echo
    echo "[ERRO] Esta operacao exige privilegios administrativos"
    echo "e sudo nao foi encontrado."
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
    if command -v brew >/dev/null 2>&1; then
        return 0
    fi

    if ! command -v curl >/dev/null 2>&1; then
        echo "[ERRO] curl nao foi encontrado no macOS."
        return 1
    fi

    echo
    echo "[python] Homebrew nao foi encontrado."
    echo "[python] Instalando Homebrew para preparar Python..."

    /bin/bash -c \
        "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
        || return 1

    refresh_homebrew
}

install_python_macos() {
    install_homebrew || return 1

    echo
    echo "[python] Instalando Python via Homebrew..."

    brew install python@3.12 || return 1

    hash -r 2>/dev/null || true
    find_python
}

install_python_linux() {
    echo
    echo "[python] Instalando Python 3, pip e suporte a venv..."

    if command -v apt-get >/dev/null 2>&1; then
        run_admin apt-get update || return 1
        run_admin apt-get install -y \
            python3 \
            python3-venv \
            python3-pip \
            curl \
            ca-certificates \
            || return 1

    elif command -v dnf >/dev/null 2>&1; then
        run_admin dnf install -y \
            python3 \
            python3-pip \
            curl \
            ca-certificates \
            || return 1

    elif command -v yum >/dev/null 2>&1; then
        run_admin yum install -y \
            python3 \
            python3-pip \
            curl \
            ca-certificates \
            || return 1

    elif command -v pacman >/dev/null 2>&1; then
        run_admin pacman -S --noconfirm \
            python \
            python-pip \
            curl \
            ca-certificates \
            || return 1

    elif command -v zypper >/dev/null 2>&1; then
        run_admin zypper \
            --non-interactive \
            install \
            python3 \
            python3-pip \
            curl \
            ca-certificates \
            || return 1
    else
        echo
        echo "[ERRO] Nenhum gerenciador de pacotes Linux suportado"
        echo "foi encontrado para instalar Python automaticamente."
        return 1
    fi

    hash -r 2>/dev/null || true

    if ! find_python; then
        echo
        echo "[ERRO] O gerenciador instalou Python, mas a versao"
        echo "disponivel nao atende ao requisito Python 3.10+."
        return 1
    fi

    return 0
}

install_python() {
    local system

    system="$(uname -s)"

    case "$system" in
        Darwin)
            install_python_macos
            ;;
        Linux)
            install_python_linux
            ;;
        *)
            echo
            echo "[ERRO] Bootstrap automatico de Python nao suporta: $system"
            return 1
            ;;
    esac
}

check_project() {
    echo "[CHECK] Validando estrutura do projeto..."

    for path in \
        "scripts/run.py" \
        "scripts/configure_env.py" \
        "requirements.txt" \
        "features"; do

        if [[ ! -e "$path" ]]; then
            echo
            echo "[ERRO] $path nao foi encontrado."
            return 1
        fi
    done

    echo "[OK] Estrutura principal encontrada."
    return 0
}

check_python() {
    echo
    echo "[CHECK] Verificando Python..."

    if find_python; then
        echo "[OK] $("$PYTHON_CMD" --version 2>&1)"
        return 0
    fi

    echo
    echo "[INFO] Python 3.10+ nao foi encontrado."
    echo
    echo "O requirements.txt instala bibliotecas Python, mas nao"
    echo "instala o proprio interpretador Python."
    echo

    read -r -p \
        "Deseja instalar Python automaticamente? [S/n]: " \
        answer

    answer="${answer:-S}"

    if [[ ! "$answer" =~ ^[Ss]$ ]]; then
        echo
        echo "[ERRO] Python e obrigatorio para executar o framework."
        return 1
    fi

    install_python || return 1

    if ! find_python; then
        echo
        echo "[ERRO] Python foi instalado, mas nao foi localizado."
        return 1
    fi

    echo "[OK] $("$PYTHON_CMD" --version 2>&1)"
    return 0
}

configure_env() {
    echo
    echo "[CHECK] Verificando configuracao do ambiente..."
    echo

    "$PYTHON_CMD" scripts/configure_env.py

    local exit_code=$?

    if [[ "$exit_code" -ne 0 ]]; then
        echo
        echo "[ERRO] A configuracao do ambiente nao foi concluida."
        return "$exit_code"
    fi

    echo
    echo "[OK] Ambiente configurado."
    return 0
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

        read -r -p \
            "Escolha [1-5] (padrao: 1): " \
            choice

        choice="${choice:-1}"
        SCOPE_ARGS=()

        case "$choice" in
            1)
                SCOPE_DESCRIPTION="Suite completa"
                return
                ;;
            2)
                SCOPE_DESCRIPTION="Smoke Tests (@smoke)"
                SCOPE_ARGS=(--tags "@smoke")
                return
                ;;
            3)
                SCOPE_DESCRIPTION="Login"
                SCOPE_ARGS=(--scope login)
                return
                ;;
            4)
                SCOPE_DESCRIPTION="Registro"
                SCOPE_ARGS=(--scope registration)
                return
                ;;
            5)
                SCOPE_DESCRIPTION="Transferencia"
                SCOPE_ARGS=(--scope transfer)
                return
                ;;
            *)
                echo
                echo "[AVISO] Opcao invalida."
                echo
                ;;
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

        read -r -p \
            "Escolha [1-3] (padrao: 1): " \
            choice

        choice="${choice:-1}"

        case "$choice" in
            1)
                BROWSER="chromium"
                return
                ;;
            2)
                BROWSER="firefox"
                return
                ;;
            3)
                BROWSER="webkit"
                return
                ;;
            *)
                echo
                echo "[AVISO] Opcao invalida."
                ;;
        esac
    done
}

select_execution_mode() {
    echo
    echo "============================================================"
    echo "MODO DE EXECUCAO"
    echo "============================================================"
    echo

    read -r -p \
        "Executar exibindo o navegador? [s/N]: " \
        answer

    if [[ "$answer" =~ ^[Ss]$ ]]; then
        HEADED_ARGS=(--headed)
        MODE_DESCRIPTION="Headed - navegador visivel"
    else
        HEADED_ARGS=()
        MODE_DESCRIPTION="Headless"
    fi
}

select_report_mode() {
    echo
    echo "============================================================"
    echo "RELATORIO ALLURE"
    echo "============================================================"
    echo

    read -r -p \
        "Deseja gerar o relatorio Allure ao final? [S/n]: " \
        answer

    answer="${answer:-S}"

    if [[ "$answer" =~ ^[Ss]$ ]]; then
        GENERATE_REPORT=true
        REPORT_DESCRIPTION="Gerar relatorio Allure"
    else
        GENERATE_REPORT=false
        REPORT_DESCRIPTION="Apenas allure-results"
    fi
}

install_node() {
    echo
    echo "Node.js/npm nao foram encontrados."
    echo

    read -r -p \
        "Deseja instalar Node.js automaticamente? [S/n]: " \
        answer

    answer="${answer:-S}"

    if [[ ! "$answer" =~ ^[Ss]$ ]]; then
        return 1
    fi

    if command -v brew >/dev/null 2>&1; then
        brew install node
        return $?
    fi

    if command -v apt-get >/dev/null 2>&1; then
        run_admin apt-get update &&
            run_admin apt-get install -y nodejs npm
        return $?
    fi

    if command -v dnf >/dev/null 2>&1; then
        run_admin dnf install -y nodejs npm
        return $?
    fi

    if command -v pacman >/dev/null 2>&1; then
        run_admin pacman -S --noconfirm nodejs npm
        return $?
    fi

    if command -v zypper >/dev/null 2>&1; then
        run_admin zypper \
            --non-interactive \
            install \
            nodejs \
            npm
        return $?
    fi

    echo
    echo "[ERRO] Nenhum gerenciador suportado foi encontrado."
    return 1
}

ensure_node() {
    if command -v node >/dev/null 2>&1 \
        && command -v npm >/dev/null 2>&1; then
        echo "[OK] Node.js $(node --version) encontrado."
        return 0
    fi

    install_node
}

ensure_allure() {
    echo
    echo "============================================================"
    echo "VERIFICANDO ALLURE REPORT"
    echo "============================================================"
    echo

    ALLURE_AVAILABLE=false
    ALLURE_MODE=""

    if command -v allure >/dev/null 2>&1 \
        && allure --version >/dev/null 2>&1; then
        echo "[OK] Allure $(allure --version | head -n 1) encontrado."
        ALLURE_AVAILABLE=true
        ALLURE_MODE="direct"
        return
    fi

    echo "[INFO] Allure CLI nao esta instalado."
    echo

    read -r -p \
        "Deseja instalar o Allure agora? [S/n]: " \
        answer

    answer="${answer:-S}"

    if [[ ! "$answer" =~ ^[Ss]$ ]]; then
        GENERATE_REPORT=false
        return
    fi

    if ! ensure_node; then
        GENERATE_REPORT=false
        return
    fi

    echo
    echo "[ALLURE] Instalando Allure Report..."
    echo

    if npm install -g allure; then
        hash -r 2>/dev/null || true

        if command -v allure >/dev/null 2>&1; then
            ALLURE_AVAILABLE=true
            ALLURE_MODE="direct"
            return
        fi
    fi

    if npx --yes allure --version >/dev/null 2>&1; then
        ALLURE_AVAILABLE=true
        ALLURE_MODE="npx"
        return
    fi

    echo
    echo "[AVISO] Nao foi possivel preparar o Allure."
    GENERATE_REPORT=false
}

run_allure() {
    if [[ "$ALLURE_MODE" == "npx" ]]; then
        npx --yes allure "$@"
    else
        allure "$@"
    fi
}

open_allure_report() {
    echo
    echo "[ALLURE] Abrindo relatorio..."
    echo

    mkdir -p "$(dirname "$ALLURE_LOG")"

    if [[ "$ALLURE_MODE" == "npx" ]]; then
        nohup \
            npx \
            --yes \
            allure \
            open \
            "$ALLURE_REPORT" \
            >"$ALLURE_LOG" \
            2>&1 &
    else
        nohup \
            allure \
            open \
            "$ALLURE_REPORT" \
            >"$ALLURE_LOG" \
            2>&1 &
    fi

    echo "[OK] Servidor Allure iniciado."
}

generate_allure_report() {
    echo
    echo "============================================================"
    echo "RELATORIO ALLURE"
    echo "============================================================"
    echo

    if [[ ! -d "$ALLURE_RESULTS" ]]; then
        echo "[AVISO] Resultados Allure nao encontrados."
        return
    fi

    if [[ "$GENERATE_REPORT" != true ]]; then
        echo "[INFO] Geracao do HTML nao foi solicitada."
        return
    fi

    if [[ "$ALLURE_AVAILABLE" != true ]]; then
        echo "[AVISO] Allure CLI nao esta disponivel."
        return
    fi

    rm -rf "$ALLURE_REPORT"

    echo "[ALLURE] Gerando relatorio HTML..."

    if ! run_allure \
        generate \
        "$ALLURE_RESULTS" \
        -o "$ALLURE_REPORT"; then
        echo
        echo "[ERRO] Nao foi possivel gerar o relatorio."
        return
    fi

    echo
    echo "[OK] Relatorio Allure gerado: $ALLURE_REPORT"
    echo

    read -r -p \
        "Deseja abrir o relatorio Allure agora? [S/n]: " \
        answer

    answer="${answer:-S}"

    if [[ "$answer" =~ ^[Ss]$ ]]; then
        open_allure_report
    fi
}

show_summary() {
    header

    echo "RESUMO DA EXECUCAO"
    echo
    echo "  Escopo......: $SCOPE_DESCRIPTION"
    echo "  Navegador...: $BROWSER"
    echo "  Modo........: $MODE_DESCRIPTION"
    echo "  Relatorio...: $REPORT_DESCRIPTION"
    echo

    read -r -p \
        "Deseja iniciar a execucao? [S/n]: " \
        answer

    answer="${answer:-S}"

    [[ "$answer" =~ ^[Ss]$ ]]
}

execute_tests() {
    header

    echo "INICIANDO TESTES"
    echo

    local run_args=(
        scripts/run.py
        --browser
        "$BROWSER"
    )

    if [[ ${#SCOPE_ARGS[@]} -gt 0 ]]; then
        run_args+=("${SCOPE_ARGS[@]}")
    fi

    if [[ ${#HEADED_ARGS[@]} -gt 0 ]]; then
        run_args+=("${HEADED_ARGS[@]}")
    fi

    echo "Configuracao:"
    echo
    echo "  Escopo....: $SCOPE_DESCRIPTION"
    echo "  Browser...: $BROWSER"
    echo "  Modo......: $MODE_DESCRIPTION"
    echo

    "$PYTHON_CMD" "${run_args[@]}"
    TEST_EXIT_CODE=$?

    echo

    if [[ "$TEST_EXIT_CODE" -eq 0 ]]; then
        echo "[OK] Execucao concluida com sucesso."
    else
        echo "[ATENCAO] Os testes terminaram com falhas ou erros."
        echo "Codigo de saida: $TEST_EXIT_CODE"
    fi

    generate_allure_report
}

main() {
    header

    echo "Este assistente prepara e executa os testes automatizados"
    echo "do ParaBank em um ambiente local Docker."
    echo
    echo "Em uma maquina nova ele pode preparar Python, Docker,"
    echo "Compose, Playwright e o proprio ParaBank."
    echo
    echo "Alteracoes de sistema podem solicitar sudo ou confirmacao."

    pause_execution

    header

    check_project || exit 1
    check_python || exit 1
    configure_env || exit 1

    if [[ "$#" -gt 0 ]]; then
        echo
        echo "[INFO] Argumentos detectados. Executando scripts/run.py diretamente."
        echo
        "$PYTHON_CMD" scripts/run.py "$@"
        exit $?
    fi

    while true; do
        header

        select_scope
        select_browser
        select_execution_mode
        select_report_mode

        if ! show_summary; then
            echo
            echo "Execucao cancelada."
            exit 0
        fi

        if [[ "$GENERATE_REPORT" == true ]]; then
            ensure_allure
        fi

        execute_tests

        echo
        echo "============================================================"
        echo "RESULTADO FINAL"
        echo "============================================================"
        echo

        if [[ "$TEST_EXIT_CODE" -eq 0 ]]; then
            echo "Status dos testes: SUCESSO"
        else
            echo "Status dos testes: FALHA / ERRO"
        fi

        echo
        echo "Resultados Allure: $ALLURE_RESULTS"

        if [[ -d "$ALLURE_REPORT" ]]; then
            echo "Relatorio HTML...: $ALLURE_REPORT"
        fi

        echo

        read -r -p \
            "Deseja realizar uma nova execucao? [s/N]: " \
            again

        if [[ ! "$again" =~ ^[Ss]$ ]]; then
            break
        fi
    done

    echo
    echo "Execucao finalizada."

    exit "$TEST_EXIT_CODE"
}

main "$@"
