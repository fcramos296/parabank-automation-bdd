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


header() {
    clear 2>/dev/null || true

    echo "============================================================"
    echo
    echo "             PARABANK AUTOMATION BDD"
    echo
    echo "        Playwright + Python + Behave + Allure"
    echo
    echo "============================================================"
    echo
}


pause_execution() {
    echo
    read -r -p "Pressione ENTER para continuar..."
}


find_python() {
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
        return 0
    fi

    if command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
        return 0
    fi

    return 1
}


check_project() {
    echo "[CHECK] Validando estrutura do projeto..."

    if [[ ! -f "scripts/run.py" ]]; then
        echo
        echo "[ERRO] scripts/run.py nao foi encontrado."
        return 1
    fi

    if [[ ! -f "scripts/configure_env.py" ]]; then
        echo
        echo "[ERRO] scripts/configure_env.py nao foi encontrado."
        return 1
    fi

    if [[ ! -f "requirements.txt" ]]; then
        echo
        echo "[ERRO] requirements.txt nao foi encontrado."
        return 1
    fi

    if [[ ! -d "features" ]]; then
        echo
        echo "[ERRO] A pasta features nao foi encontrada."
        return 1
    fi

    echo "[OK] Estrutura principal encontrada."

    return 0
}


check_python() {
    echo
    echo "[CHECK] Verificando Python..."

    if ! find_python; then
        echo
        echo "[ERRO] Python nao foi encontrado."
        echo
        echo "Instale Python 3.10 ou superior."
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
        echo "      Todos os cenarios."
        echo
        echo "  [2] Smoke Tests"
        echo "      Apenas cenarios @smoke."
        echo
        echo "  [3] Login"
        echo "      Cenarios de autenticacao."
        echo
        echo "  [4] Registro"
        echo "      Cenarios de cadastro."
        echo
        echo "  [5] Transferencia"
        echo "      Cenarios de transferencia de fundos."
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
                SCOPE_ARGS=(
                    --tags
                    "@smoke"
                )
                return
                ;;

            3)
                SCOPE_DESCRIPTION="Login"
                SCOPE_ARGS=(
                    --scope
                    login
                )
                return
                ;;

            4)
                SCOPE_DESCRIPTION="Registro"
                SCOPE_ARGS=(
                    --scope
                    registration
                )
                return
                ;;

            5)
                SCOPE_DESCRIPTION="Transferencia"
                SCOPE_ARGS=(
                    --scope
                    transfer
                )
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
    echo "Deseja visualizar o navegador durante os testes?"
    echo
    echo "  S = Headed"
    echo "  N = Headless"
    echo

    read -r -p \
        "Executar exibindo o navegador? [s/N]: " \
        answer

    if [[ "$answer" =~ ^[Ss]$ ]]; then

        HEADED_ARGS=(
            --headed
        )

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

    echo "O Allure permite visualizar:"
    echo
    echo "  - features;"
    echo "  - cenarios;"
    echo "  - steps;"
    echo "  - duracao;"
    echo "  - falhas;"
    echo "  - screenshots;"
    echo "  - evidencias."
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
        sudo apt-get update
        sudo apt-get install -y nodejs npm
        return $?
    fi

    if command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y nodejs npm
        return $?
    fi

    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm nodejs npm
        return $?
    fi

    if command -v zypper >/dev/null 2>&1; then
        sudo zypper \
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

    if command -v allure >/dev/null 2>&1; then

        if allure --version >/dev/null 2>&1; then

            echo "[OK] Allure $(allure --version | head -n 1) encontrado."

            ALLURE_AVAILABLE=true
            ALLURE_MODE="direct"

            return
        fi
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

            echo "[OK] Allure instalado."

            return
        fi
    fi

    if npx --yes allure --version >/dev/null 2>&1; then

        ALLURE_AVAILABLE=true
        ALLURE_MODE="npx"

        echo "[OK] Allure disponivel via npx."

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

    echo "[OK] Resultados encontrados:"
    echo
    echo "  $ALLURE_RESULTS"
    echo

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
    echo

    if ! run_allure \
        generate \
        "$ALLURE_RESULTS" \
        -o "$ALLURE_REPORT"; then

        echo
        echo "[ERRO] Nao foi possivel gerar o relatorio."

        return
    fi

    echo
    echo "[OK] Relatorio Allure gerado com sucesso."
    echo
    echo "Local:"
    echo
    echo "  $ALLURE_REPORT"
    echo

    read -r -p \
        "Deseja abrir o relatorio Allure agora? [S/n]: " \
        answer

    answer="${answer:-S}"

    if [[ "$answer" =~ ^[Ss]$ ]]; then
        open_allure_report
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
    echo
    echo "O navegador devera abrir automaticamente."
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

    RUN_ARGS=(
        scripts/run.py
        --browser
        "$BROWSER"
    )

    if [[ ${#SCOPE_ARGS[@]} -gt 0 ]]; then
        RUN_ARGS+=(
            "${SCOPE_ARGS[@]}"
        )
    fi

    if [[ ${#HEADED_ARGS[@]} -gt 0 ]]; then
        RUN_ARGS+=(
            "${HEADED_ARGS[@]}"
        )
    fi

    echo "Configuracao:"
    echo
    echo "  Escopo....: $SCOPE_DESCRIPTION"
    echo "  Browser...: $BROWSER"
    echo "  Modo......: $MODE_DESCRIPTION"
    echo

    "$PYTHON_CMD" "${RUN_ARGS[@]}"

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
    echo "do ParaBank."
    echo
    echo "Na primeira execucao ele tambem podera solicitar"
    echo "seu token do Scrape.do."
    echo
    echo "O token sera armazenado somente no arquivo local .env"
    echo "e nao sera exibido na tela."

    pause_execution

    header

    check_project || exit 1
    check_python || exit 1
    configure_env || exit 1

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