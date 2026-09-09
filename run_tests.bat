@echo off
setlocal EnableExtensions EnableDelayedExpansion

chcp 65001 >nul
cd /d "%~dp0"

title ParaBank Automation - Interactive Runner

set "ALLURE_RESULTS=reports\allure-results"
set "ALLURE_REPORT=reports\allure-report"

set "TEST_EXIT_CODE=0"

set "SCOPE_ARG="
set "TAGS_ARG="
set "HEADED_ARG="

set "BROWSER=chromium"

set "GENERATE_REPORT=1"

set "ALLURE_AVAILABLE=0"
set "ALLURE_MODE="


REM ============================================================
REM INICIO
REM ============================================================

cls

call :HEADER

echo Este assistente ira preparar e executar os testes automatizados
echo do ParaBank.
echo.
echo Durante a execucao voce podera escolher:
echo.
echo   - quais testes deseja executar;
echo   - qual navegador utilizar;
echo   - se deseja visualizar o navegador;
echo   - se deseja gerar o relatorio Allure.
echo.
echo Na primeira execucao o assistente tambem podera solicitar
echo seu token do Scrape.do.
echo.
echo O token sera armazenado somente no arquivo local .env
echo e nunca sera exibido na tela.
echo.
echo O setup tecnico do framework e realizado pelo scripts\run.py.
echo.

pause


REM ============================================================
REM VALIDACOES INICIAIS
REM ============================================================

call :CHECK_PROJECT

if errorlevel 1 (
    goto FATAL_ERROR
)


call :CHECK_PYTHON

if errorlevel 1 (
    goto FATAL_ERROR
)


call :CONFIGURE_ENV

if errorlevel 1 (
    goto FATAL_ERROR
)


REM ============================================================
REM MENU PRINCIPAL
REM ============================================================

:MAIN_MENU

cls

call :HEADER

echo CONFIGURACAO DA EXECUCAO
echo.

call :SELECT_SCOPE
call :SELECT_BROWSER
call :SELECT_MODE
call :SELECT_REPORT


REM ============================================================
REM RESUMO
REM ============================================================

cls

call :HEADER

echo RESUMO DA EXECUCAO
echo.

echo   Escopo......: !SCOPE_DESCRIPTION!
echo   Navegador...: !BROWSER!
echo   Modo........: !MODE_DESCRIPTION!
echo   Relatorio...: !REPORT_DESCRIPTION!

echo.
echo O runner ira:
echo.
echo   1. verificar/criar o ambiente virtual;
echo   2. instalar dependencias Python quando necessario;
echo   3. garantir a instalacao do navegador Playwright;
echo   4. limpar resultados Allure anteriores;
echo   5. executar os cenarios Behave selecionados;
echo   6. gerar evidencias Allure;
echo   7. gerar o relatorio HTML, se solicitado;
echo   8. perguntar se deseja abrir o relatorio.
echo.

choice /C SN /N /M "Deseja iniciar a execucao? [S/N]: "

if errorlevel 2 (
    goto END_USER
)


REM ============================================================
REM PREPARA ALLURE
REM ============================================================

if "!GENERATE_REPORT!"=="1" (
    call :ENSURE_ALLURE
)


REM ============================================================
REM EXECUTA
REM ============================================================

goto EXECUTE_TESTS



:EXECUTE_TESTS

cls

call :HEADER

echo INICIANDO TESTES
echo.

set "RUN_COMMAND=python scripts\run.py"

if defined SCOPE_ARG (
    set "RUN_COMMAND=!RUN_COMMAND! !SCOPE_ARG!"
)

set "RUN_COMMAND=!RUN_COMMAND! --browser !BROWSER!"

if defined HEADED_ARG (
    set "RUN_COMMAND=!RUN_COMMAND! !HEADED_ARG!"
)

if defined TAGS_ARG (
    set "RUN_COMMAND=!RUN_COMMAND! !TAGS_ARG!"
)


echo Configuracao:
echo.

echo   Escopo....: !SCOPE_DESCRIPTION!
echo   Browser...: !BROWSER!
echo   Modo......: !MODE_DESCRIPTION!

echo.
echo Comando:
echo.
echo   !RUN_COMMAND!
echo.
echo ------------------------------------------------------------
echo.

call !RUN_COMMAND!

set "TEST_EXIT_CODE=!ERRORLEVEL!"

echo.
echo ------------------------------------------------------------
echo.

if "!TEST_EXIT_CODE!"=="0" (

    echo [OK] Execucao concluida com sucesso.

) else (

    echo [ATENCAO] A execucao terminou com falhas ou erros.
    echo.
    echo Codigo de saida: !TEST_EXIT_CODE!
    echo.
    echo As evidencias continuarao sendo processadas para
    echo permitir a analise das falhas.

)


REM ============================================================
REM ALLURE
REM ============================================================

call :PROCESS_REPORT


REM ============================================================
REM RESULTADO
REM ============================================================

echo.
echo ============================================================
echo RESULTADO FINAL
echo ============================================================
echo.

if "!TEST_EXIT_CODE!"=="0" (

    echo Status dos testes: SUCESSO

) else (

    echo Status dos testes: FALHA / ERRO

)

echo.

if exist "%ALLURE_RESULTS%" (
    echo Resultados Allure: %ALLURE_RESULTS%
)

if exist "%ALLURE_REPORT%\index.html" (
    echo Relatorio HTML...: %ALLURE_REPORT%
)

echo.
echo ============================================================
echo.

choice /C SN /N /M "Deseja realizar uma nova execucao? [S/N]: "

if errorlevel 2 (
    goto END
)

goto MAIN_MENU



REM ============================================================
REM PROJETO
REM ============================================================

:CHECK_PROJECT

echo.
echo [CHECK] Validando estrutura do projeto...

if not exist "scripts\run.py" (

    echo.
    echo [ERRO] scripts\run.py nao foi encontrado.

    exit /b 1
)

if not exist "scripts\configure_env.py" (

    echo.
    echo [ERRO] scripts\configure_env.py nao foi encontrado.

    exit /b 1
)

if not exist "requirements.txt" (

    echo.
    echo [ERRO] requirements.txt nao foi encontrado.

    exit /b 1
)

if not exist "features" (

    echo.
    echo [ERRO] A pasta features nao foi encontrada.

    exit /b 1
)

echo [OK] Estrutura principal encontrada.

exit /b 0



REM ============================================================
REM PYTHON
REM ============================================================

:CHECK_PYTHON

echo.
echo [CHECK] Verificando Python...

where python >nul 2>&1

if errorlevel 1 (

    echo.
    echo [ERRO] Python nao foi encontrado no PATH.
    echo.
    echo Instale Python 3.10 ou superior.
    echo.
    echo Durante a instalacao habilite:
    echo.
    echo   Add Python to PATH
    echo.

    exit /b 1
)

for /f "tokens=*" %%V in ('python --version 2^>^&1') do (
    echo [OK] %%V encontrado.
)

exit /b 0



REM ============================================================
REM CONFIGURA .ENV
REM ============================================================

:CONFIGURE_ENV

echo.
echo [CHECK] Verificando configuracao do ambiente...
echo.

python scripts\configure_env.py

set "CONFIG_EXIT_CODE=!ERRORLEVEL!"

if not "!CONFIG_EXIT_CODE!"=="0" (

    echo.
    echo [ERRO] A configuracao do ambiente nao foi concluida.
    echo.

    exit /b !CONFIG_EXIT_CODE!
)

echo.
echo [OK] Ambiente configurado.

exit /b 0



REM ============================================================
REM ESCOPO
REM ============================================================

:SELECT_SCOPE

echo ============================================================
echo ESCOLHA O ESCOPO
echo ============================================================
echo.

echo   [1] Suite completa
echo       Executa todos os cenarios.
echo.

echo   [2] Smoke Tests
echo       Executa apenas os cenarios marcados com @smoke.
echo.

echo   [3] Login
echo       Executa os cenarios de autenticacao.
echo.

echo   [4] Registro
echo       Executa os cenarios de cadastro.
echo.

echo   [5] Transferencia
echo       Executa os cenarios de transferencia de fundos.
echo.

set /p "SCOPE_CHOICE=Escolha [1-5] (padrao: 1): "

if "!SCOPE_CHOICE!"=="" (
    set "SCOPE_CHOICE=1"
)

set "SCOPE_ARG="
set "TAGS_ARG="

if "!SCOPE_CHOICE!"=="1" (

    set "SCOPE_DESCRIPTION=Suite completa"

    goto :eof
)

if "!SCOPE_CHOICE!"=="2" (

    set "SCOPE_DESCRIPTION=Smoke Tests (@smoke)"
    set "TAGS_ARG=--tags @smoke"

    goto :eof
)

if "!SCOPE_CHOICE!"=="3" (

    set "SCOPE_DESCRIPTION=Login"
    set "SCOPE_ARG=--scope login"

    goto :eof
)

if "!SCOPE_CHOICE!"=="4" (

    set "SCOPE_DESCRIPTION=Registro"
    set "SCOPE_ARG=--scope registration"

    goto :eof
)

if "!SCOPE_CHOICE!"=="5" (

    set "SCOPE_DESCRIPTION=Transferencia"
    set "SCOPE_ARG=--scope transfer"

    goto :eof
)

echo.
echo [AVISO] Opcao invalida.
echo.

goto SELECT_SCOPE



REM ============================================================
REM BROWSER
REM ============================================================

:SELECT_BROWSER

echo.
echo ============================================================
echo ESCOLHA O NAVEGADOR
echo ============================================================
echo.

echo   [1] Chromium
echo       Recomendado.
echo.

echo   [2] Firefox
echo.

echo   [3] WebKit
echo.

set /p "BROWSER_CHOICE=Escolha [1-3] (padrao: 1): "

if "!BROWSER_CHOICE!"=="" (
    set "BROWSER_CHOICE=1"
)

if "!BROWSER_CHOICE!"=="1" (

    set "BROWSER=chromium"

    goto :eof
)

if "!BROWSER_CHOICE!"=="2" (

    set "BROWSER=firefox"

    goto :eof
)

if "!BROWSER_CHOICE!"=="3" (

    set "BROWSER=webkit"

    goto :eof
)

echo.
echo [AVISO] Opcao invalida.
echo.

goto SELECT_BROWSER



REM ============================================================
REM HEADED / HEADLESS
REM ============================================================

:SELECT_MODE

echo.
echo ============================================================
echo MODO DE EXECUCAO
echo ============================================================
echo.

echo Deseja visualizar o navegador enquanto os testes executam?
echo.

echo   S = Headed
echo       O navegador ficara visivel.
echo.

echo   N = Headless
echo       O navegador executara em segundo plano.
echo.

choice /C SN /N /M "Executar exibindo o navegador? [S/N]: "

if errorlevel 2 (

    set "HEADED_ARG="
    set "MODE_DESCRIPTION=Headless"

    goto :eof
)

set "HEADED_ARG=--headed"
set "MODE_DESCRIPTION=Headed - navegador visivel"

goto :eof



REM ============================================================
REM RELATORIO
REM ============================================================

:SELECT_REPORT

echo.
echo ============================================================
echo RELATORIO ALLURE
echo ============================================================
echo.

echo O Allure permite visualizar:
echo.
echo   - features;
echo   - cenarios;
echo   - steps;
echo   - duracao;
echo   - falhas;
echo   - screenshots;
echo   - evidencias da execucao.
echo.

choice /C SN /N /M "Deseja gerar o relatorio Allure ao final? [S/N]: "

if errorlevel 2 (

    set "GENERATE_REPORT=0"
    set "REPORT_DESCRIPTION=Apenas allure-results"

    goto :eof
)

set "GENERATE_REPORT=1"
set "REPORT_DESCRIPTION=Gerar relatorio Allure"

goto :eof



REM ============================================================
REM ALLURE
REM ============================================================

:ENSURE_ALLURE

echo.
echo ============================================================
echo VERIFICANDO ALLURE REPORT
echo ============================================================
echo.

set "ALLURE_AVAILABLE=0"
set "ALLURE_MODE="

where allure >nul 2>&1

if not errorlevel 1 (

    call allure --version >nul 2>&1

    if not errorlevel 1 (

        set "ALLURE_VERSION="

        for /f "tokens=*" %%V in ('call allure --version 2^>^&1') do (
            set "ALLURE_VERSION=%%V"
        )

        echo [OK] Allure !ALLURE_VERSION! encontrado.

        set "ALLURE_AVAILABLE=1"
        set "ALLURE_MODE=direct"

        goto :eof
    )
)


echo [INFO] Allure CLI nao foi encontrado.
echo.
echo O script pode instalar o Allure automaticamente.
echo.

choice /C SN /N /M "Deseja instalar o Allure agora? [S/N]: "

if errorlevel 2 (

    echo.
    echo [INFO] Instalacao ignorada.

    set "GENERATE_REPORT=0"

    goto :eof
)


call :ENSURE_NODE

if errorlevel 1 (

    echo.
    echo [AVISO] Node.js/npm nao puderam ser preparados.

    set "GENERATE_REPORT=0"

    goto :eof
)


echo.
echo [ALLURE] Instalando Allure Report...
echo.

call npm install -g allure


if not errorlevel 1 (

    call :REFRESH_NODE_PATH

    where allure >nul 2>&1

    if not errorlevel 1 (

        call allure --version >nul 2>&1

        if not errorlevel 1 (

            set "ALLURE_VERSION="

            for /f "tokens=*" %%V in ('call allure --version 2^>^&1') do (
                set "ALLURE_VERSION=%%V"
            )

            echo.
            echo [OK] Allure !ALLURE_VERSION! instalado.

            set "ALLURE_AVAILABLE=1"
            set "ALLURE_MODE=direct"

            goto :eof
        )
    )
)


echo.
echo [INFO] Tentando utilizar Allure via npx...
echo.

call npx --yes allure --version >nul 2>&1

if not errorlevel 1 (

    set "ALLURE_AVAILABLE=1"
    set "ALLURE_MODE=npx"

    echo [OK] Allure disponivel via npx.

    goto :eof
)


echo.
echo [ERRO] Nao foi possivel preparar o Allure.
echo.

set "GENERATE_REPORT=0"

goto :eof



REM ============================================================
REM NODE
REM ============================================================

:ENSURE_NODE

where node >nul 2>&1

if not errorlevel 1 (

    where npm >nul 2>&1

    if not errorlevel 1 (

        for /f "tokens=*" %%V in ('node --version 2^>^&1') do (
            echo [OK] Node.js %%V encontrado.
        )

        exit /b 0
    )
)


echo.
echo Node.js/npm nao foram encontrados.
echo.

choice /C SN /N /M "Deseja instalar Node.js LTS automaticamente? [S/N]: "

if errorlevel 2 (
    exit /b 1
)


where winget >nul 2>&1

if not errorlevel 1 (

    winget install ^
        --id OpenJS.NodeJS.LTS ^
        -e ^
        --accept-package-agreements ^
        --accept-source-agreements

    call :REFRESH_NODE_PATH

    where npm >nul 2>&1

    if not errorlevel 1 (
        exit /b 0
    )
)


where choco >nul 2>&1

if not errorlevel 1 (

    choco install nodejs-lts -y

    call :REFRESH_NODE_PATH

    where npm >nul 2>&1

    if not errorlevel 1 (
        exit /b 0
    )
)


where scoop >nul 2>&1

if not errorlevel 1 (

    scoop install nodejs-lts

    call :REFRESH_NODE_PATH

    where npm >nul 2>&1

    if not errorlevel 1 (
        exit /b 0
    )
)


echo.
echo [ERRO] Nao foi possivel instalar Node.js automaticamente.

exit /b 1



:REFRESH_NODE_PATH

if exist "%ProgramFiles%\nodejs" (
    set "PATH=%ProgramFiles%\nodejs;%PATH%"
)

if exist "%APPDATA%\npm" (
    set "PATH=%APPDATA%\npm;%PATH%"
)

exit /b 0



REM ============================================================
REM GERA REPORT
REM ============================================================

:PROCESS_REPORT

echo.
echo ============================================================
echo RELATORIO ALLURE
echo ============================================================
echo.

if not exist "%ALLURE_RESULTS%" (

    echo [AVISO] Resultados Allure nao encontrados.

    goto :eof
)


echo [OK] Resultados encontrados:
echo.
echo   %ALLURE_RESULTS%
echo.


if "!GENERATE_REPORT!"=="0" (

    echo [INFO] Geracao do HTML nao foi solicitada.

    goto :eof
)


if "!ALLURE_AVAILABLE!"=="0" (

    echo [AVISO] Allure CLI nao esta disponivel.

    goto :eof
)


if exist "%ALLURE_REPORT%" (
    rmdir /S /Q "%ALLURE_REPORT%" >nul 2>&1
)


echo [ALLURE] Gerando relatorio HTML...
echo.


if "!ALLURE_MODE!"=="npx" (

    call npx --yes allure generate ^
        "%ALLURE_RESULTS%" ^
        --clean ^
        -o "%ALLURE_REPORT%"

) else (

    call allure generate ^
        "%ALLURE_RESULTS%" ^
        --clean ^
        -o "%ALLURE_REPORT%"
)


if errorlevel 1 (

    echo.
    echo [ERRO] Nao foi possivel gerar o relatorio.

    goto :eof
)


echo.
echo [OK] Relatorio Allure gerado com sucesso.
echo.
echo Local:
echo.
echo   %ALLURE_REPORT%
echo.


choice /C SN /N /M "Deseja abrir o relatorio Allure agora? [S/N]: "

if errorlevel 2 (
    goto :eof
)


call :OPEN_ALLURE_REPORT

goto :eof



REM ============================================================
REM ABRE REPORT
REM ============================================================

:OPEN_ALLURE_REPORT

echo.
echo [ALLURE] Abrindo relatorio no navegador...
echo.


if "!ALLURE_MODE!"=="npx" (

    start "ParaBank - Allure Report" cmd /k ^
        "npx --yes allure open reports\allure-report"

) else (

    start "ParaBank - Allure Report" cmd /k ^
        "call allure open reports\allure-report"
)

goto :eof



REM ============================================================
REM HEADER
REM ============================================================

:HEADER

echo ============================================================
echo.
echo             PARABANK AUTOMATION BDD
echo.
echo        Playwright + Python + Behave + Allure
echo.
echo ============================================================
echo.

goto :eof



:FATAL_ERROR

echo.
echo ============================================================
echo NAO FOI POSSIVEL INICIAR A EXECUCAO
echo ============================================================
echo.

pause

exit /b 1



:END_USER

echo.
echo Execucao cancelada pelo usuario.
echo.

pause

exit /b 0



:END

echo.
echo Pressione qualquer tecla para fechar esta janela.

pause >nul

exit /b !TEST_EXIT_CODE!