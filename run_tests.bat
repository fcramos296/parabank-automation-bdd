@echo off
setlocal EnableExtensions EnableDelayedExpansion

chcp 65001 >nul
cd /d "%~dp0"

title ParaBank Automation BDD - Topaz

set "ALLURE_VERSION=3.17.0"
set "ALLURE_CONFIG=allurerc.yml"
set "ALLURE_RESULTS=reports\allure-results"
set "ALLURE_REPORT=reports\allure-report"

set "TEST_EXIT_CODE=0"
set "PYTHON_CMD="
set "SCOPE_ARG="
set "TAGS_ARG="
set "HEADED_ARG="
set "BROWSER=chromium"
set "GENERATE_REPORT=1"
set "ALLURE_READY=0"
set "ALLURE_SCOPE=full"

cls
call :HEADER

echo Este assistente prepara e executa os testes automatizados
echo do ParaBank em um ambiente local Docker.
echo.
echo Em uma maquina nova ele pode preparar automaticamente:
echo.
echo   - Python 3.10+;
echo   - WSL 2 e Virtual Machine Platform no Windows;
echo   - Docker Desktop e Docker Compose;
echo   - ambiente virtual e dependencias Python;
echo   - browsers do Playwright;
echo   - ParaBank e banco de dados local.
echo.
echo O relatorio utiliza Allure 3 Awesome com identidade visual Topaz.
echo.
echo Alteracoes de sistema podem solicitar confirmacao,
echo UAC ou privilegios administrativos.
echo.

pause

call :CHECK_PROJECT
if errorlevel 1 goto FATAL_ERROR

call :CHECK_PYTHON
if errorlevel 1 goto FATAL_ERROR

call :CONFIGURE_ENV
if errorlevel 1 goto FATAL_ERROR

if not "%~1"=="" (
    echo.
    echo [INFO] Argumentos detectados. Executando scripts\run.py diretamente.
    echo.
    call !PYTHON_CMD! scripts\run.py %*
    exit /b !ERRORLEVEL!
)

:MAIN_MENU
cls
call :HEADER

echo CONFIGURACAO DA EXECUCAO
echo.

call :SELECT_SCOPE
call :SELECT_BROWSER
call :SELECT_MODE
call :SELECT_REPORT

cls
call :HEADER

echo RESUMO DA EXECUCAO
echo.
echo   Escopo......: !SCOPE_DESCRIPTION!
echo   Navegador...: !BROWSER!
echo   Modo........: !MODE_DESCRIPTION!
echo   Relatorio...: !REPORT_DESCRIPTION!
echo.

echo O runner ira preparar Docker/ParaBank, Python/Playwright
echo e executar os cenarios Behave selecionados.
echo.

choice /C SN /N /M "Deseja iniciar a execucao? [S/N]: "
if errorlevel 2 goto END_USER

if "!GENERATE_REPORT!"=="1" (
    call :ENSURE_ALLURE3
    if errorlevel 1 (
        echo.
        echo [AVISO] O relatorio HTML nao sera gerado nesta execucao.
        set "GENERATE_REPORT=0"
    )
)

goto EXECUTE_TESTS


:EXECUTE_TESTS
cls
call :HEADER

echo INICIANDO TESTES
echo.

set "RUN_COMMAND=!PYTHON_CMD! scripts\run.py"

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
    echo Codigo de saida: !TEST_EXIT_CODE!
)

call :PROCESS_REPORT

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
if errorlevel 2 goto END

goto MAIN_MENU


:CHECK_PROJECT
echo.
echo [CHECK] Validando estrutura do projeto...

for %%F in (
    "scripts\run.py"
    "scripts\configure_env.py"
    "scripts\bootstrap_python_windows.ps1"
    "requirements.txt"
    "%ALLURE_CONFIG%"
    "assets\topaz-logo.png"
) do (
    if not exist %%F (
        echo [ERRO] %%~F nao foi encontrado.
        exit /b 1
    )
)

if not exist "features" (
    echo [ERRO] A pasta features nao foi encontrada.
    exit /b 1
)

echo [OK] Estrutura principal encontrada.
exit /b 0


:CHECK_PYTHON
echo.
echo [CHECK] Verificando Python...

call :RESOLVE_PYTHON
if not errorlevel 1 goto PYTHON_FOUND

echo.
echo [INFO] Python 3.10 ou superior nao foi encontrado.
echo.
echo O requirements.txt instala bibliotecas Python, mas nao
echo instala o proprio interpretador Python.
echo.

choice /C SN /N /M "Deseja instalar Python 3.12 automaticamente? [S/N]: "
if errorlevel 2 (
    echo.
    echo [ERRO] Python e obrigatorio para executar o framework.
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\bootstrap_python_windows.ps1"
if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel instalar Python automaticamente.
    exit /b 1
)

call :REFRESH_PYTHON_PATH
call :RESOLVE_PYTHON
if errorlevel 1 (
    echo.
    echo [ERRO] Python foi instalado, mas nao foi localizado nesta sessao.
    echo Feche e abra o terminal e execute run_tests.bat novamente.
    exit /b 1
)

:PYTHON_FOUND
for /f "tokens=*" %%V in ('call !PYTHON_CMD! --version 2^>^&1') do (
    echo [OK] %%V encontrado.
)
exit /b 0


:RESOLVE_PYTHON
set "PYTHON_CMD="

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

where py >nul 2>&1
if not errorlevel 1 (
    for %%V in (3.14 3.13 3.12 3.11 3.10) do (
        py -%%V -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=py -%%V"
            exit /b 0
        )
    )
)

for /f "usebackq delims=" %%P in (`powershell.exe -NoProfile -Command "$roots=@($env:LOCALAPPDATA+'\Programs\Python',$env:ProgramFiles); Get-ChildItem $roots -Filter python.exe -Recurse -ErrorAction SilentlyContinue ^| Where-Object { $_.FullName -notmatch '\\.venv\\' } ^| Sort-Object FullName -Descending ^| Select-Object -First 1 -ExpandProperty FullName"`) do (
    "%%P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD="%%P"
        exit /b 0
    )
)

exit /b 1


:REFRESH_PYTHON_PATH
for /f "usebackq delims=" %%P in (`powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','User')"`) do (
    set "PATH=!PATH!;%%P"
)
for /f "usebackq delims=" %%P in (`powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','Machine')"`) do (
    set "PATH=!PATH!;%%P"
)
exit /b 0


:CONFIGURE_ENV
echo.
echo [CHECK] Verificando configuracao do ambiente...
echo.

call !PYTHON_CMD! scripts\configure_env.py
set "CONFIG_EXIT_CODE=!ERRORLEVEL!"

if not "!CONFIG_EXIT_CODE!"=="0" (
    echo.
    echo [ERRO] A configuracao do ambiente nao foi concluida.
    exit /b !CONFIG_EXIT_CODE!
)

echo.
echo [OK] Ambiente configurado.
exit /b 0


:SELECT_SCOPE
echo ============================================================
echo ESCOLHA O ESCOPO
echo ============================================================
echo.
echo   [1] Suite completa
echo   [2] Smoke Tests
echo   [3] Login
echo   [4] Registro
echo   [5] Transferencia
echo.

set /p "SCOPE_CHOICE=Escolha [1-5] (padrao: 1): "
if "!SCOPE_CHOICE!"=="" set "SCOPE_CHOICE=1"

set "SCOPE_ARG="
set "TAGS_ARG="
set "ALLURE_SCOPE=full"

if "!SCOPE_CHOICE!"=="1" (
    set "SCOPE_DESCRIPTION=Suite completa"
    exit /b 0
)
if "!SCOPE_CHOICE!"=="2" (
    set "SCOPE_DESCRIPTION=Smoke Tests (@smoke)"
    set "TAGS_ARG=--tags @smoke"
    set "ALLURE_SCOPE=smoke"
    exit /b 0
)
if "!SCOPE_CHOICE!"=="3" (
    set "SCOPE_DESCRIPTION=Login"
    set "SCOPE_ARG=--scope login"
    set "ALLURE_SCOPE=login"
    exit /b 0
)
if "!SCOPE_CHOICE!"=="4" (
    set "SCOPE_DESCRIPTION=Registro"
    set "SCOPE_ARG=--scope registration"
    set "ALLURE_SCOPE=registration"
    exit /b 0
)
if "!SCOPE_CHOICE!"=="5" (
    set "SCOPE_DESCRIPTION=Transferencia"
    set "SCOPE_ARG=--scope transfer"
    set "ALLURE_SCOPE=transfer"
    exit /b 0
)

echo.
echo [AVISO] Opcao invalida.
echo.
goto SELECT_SCOPE


:SELECT_BROWSER
echo.
echo ============================================================
echo ESCOLHA O NAVEGADOR
echo ============================================================
echo.
echo   [1] Chromium - recomendado
echo   [2] Firefox
echo   [3] WebKit
echo.

set /p "BROWSER_CHOICE=Escolha [1-3] (padrao: 1): "
if "!BROWSER_CHOICE!"=="" set "BROWSER_CHOICE=1"

if "!BROWSER_CHOICE!"=="1" (
    set "BROWSER=chromium"
    exit /b 0
)
if "!BROWSER_CHOICE!"=="2" (
    set "BROWSER=firefox"
    exit /b 0
)
if "!BROWSER_CHOICE!"=="3" (
    set "BROWSER=webkit"
    exit /b 0
)

echo.
echo [AVISO] Opcao invalida.
goto SELECT_BROWSER


:SELECT_MODE
echo.
echo ============================================================
echo MODO DE EXECUCAO
echo ============================================================
echo.

choice /C SN /N /M "Executar exibindo o navegador? [S/N]: "
if errorlevel 2 (
    set "HEADED_ARG="
    set "MODE_DESCRIPTION=Headless"
    exit /b 0
)

set "HEADED_ARG=--headed"
set "MODE_DESCRIPTION=Headed - navegador visivel"
exit /b 0


:SELECT_REPORT
echo.
echo ============================================================
echo RELATORIO ALLURE 3 - TOPAZ
echo ============================================================
echo.

choice /C SN /N /M "Deseja gerar o relatorio Allure personalizado ao final? [S/N]: "
if errorlevel 2 (
    set "GENERATE_REPORT=0"
    set "REPORT_DESCRIPTION=Apenas allure-results"
    exit /b 0
)

set "GENERATE_REPORT=1"
set "REPORT_DESCRIPTION=Allure 3 Awesome - Topaz"
exit /b 0


:ENSURE_ALLURE3
echo.
echo ============================================================
echo PREPARANDO ALLURE 3
echo ============================================================
echo.

call :ENSURE_NODE
if errorlevel 1 exit /b 1

call npx --yes allure@%ALLURE_VERSION% --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Nao foi possivel preparar Allure %ALLURE_VERSION% via npx.
    exit /b 1
)

for /f "tokens=*" %%V in ('call npx --yes allure@%ALLURE_VERSION% --version 2^>^&1') do (
    echo [OK] Allure %%V pronto.
)

set "ALLURE_READY=1"
exit /b 0


:ENSURE_NODE
where node >nul 2>&1
if not errorlevel 1 (
    where npm >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Node.js e npm encontrados.
        exit /b 0
    )
)

echo.
echo [INFO] Node.js/npm nao foram encontrados.
choice /C SN /N /M "Deseja instalar Node.js LTS automaticamente para gerar o Allure? [S/N]: "
if errorlevel 2 exit /b 1

where winget >nul 2>&1
if not errorlevel 1 (
    winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
    call :REFRESH_NODE_PATH
    where npm >nul 2>&1
    if not errorlevel 1 exit /b 0
)

where choco >nul 2>&1
if not errorlevel 1 (
    choco install nodejs-lts -y
    call :REFRESH_NODE_PATH
    where npm >nul 2>&1
    if not errorlevel 1 exit /b 0
)

echo [ERRO] Nao foi possivel instalar Node.js automaticamente.
exit /b 1


:REFRESH_NODE_PATH
if exist "%ProgramFiles%\nodejs" set "PATH=%ProgramFiles%\nodejs;%PATH%"
if exist "%APPDATA%\npm" set "PATH=%APPDATA%\npm;%PATH%"
exit /b 0


:PROCESS_REPORT
echo.
echo ============================================================
echo RELATORIO ALLURE 3 - TOPAZ
echo ============================================================
echo.

if not exist "%ALLURE_RESULTS%" (
    echo [AVISO] Resultados Allure nao encontrados.
    exit /b 0
)

if "!GENERATE_REPORT!"=="0" (
    echo [INFO] Geracao do HTML nao foi solicitada.
    exit /b 0
)

if "!ALLURE_READY!"=="0" (
    echo [AVISO] Allure 3 nao esta disponivel.
    exit /b 0
)

if exist "%ALLURE_REPORT%" rmdir /S /Q "%ALLURE_REPORT%" >nul 2>&1

set "ALLURE_BROWSER=!BROWSER!"

echo [ALLURE] Gerando relatorio personalizado...
echo [ALLURE] Config....: %ALLURE_CONFIG%
echo [ALLURE] Tema......: Topaz / Awesome / dark
echo [ALLURE] Escopo....: !ALLURE_SCOPE!
echo [ALLURE] Browser...: !ALLURE_BROWSER!
echo.

call npx --yes allure@%ALLURE_VERSION% generate "%ALLURE_RESULTS%" --config ".\%ALLURE_CONFIG%" --output "%ALLURE_REPORT%"
if errorlevel 1 (
    echo [ERRO] Nao foi possivel gerar o relatorio personalizado.
    exit /b 0
)

if not exist "%ALLURE_REPORT%\index.html" (
    echo [ERRO] index.html do Allure nao foi encontrado.
    exit /b 0
)

echo.
echo [OK] Relatorio Topaz gerado: %ALLURE_REPORT%
echo.

choice /C SN /N /M "Deseja abrir o relatorio Allure agora? [S/N]: "
if errorlevel 2 exit /b 0

start "Topaz - ParaBank Allure" cmd /k "npx --yes allure@%ALLURE_VERSION% open reports\allure-report"
exit /b 0


:HEADER
echo ============================================================
echo.
echo             PARABANK AUTOMATION BDD
echo.
echo              TOPAZ - QA AUTOMATION
echo.
echo        Playwright + Python + Behave + Docker
echo.
echo ============================================================
echo.
exit /b 0


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
