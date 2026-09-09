@echo off
chcp 65001 >nul
title Parabank Automation Runner

echo ============================================================
echo   🚀 SETUP E EXECUCAO DE TESTES - PARABANK (WINDOWS)
echo ============================================================
echo.

:: 1. Verificacao do Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python nao encontrado no PATH do sistema.
    echo Instale o Python 3.10+ e marque a opcao Add Python to PATH.
    pause
    exit /b 1
)

:: 2. Criacao do Ambiente Virtual (.venv)
if not exist ".venv" (
    echo [1/5] Criando ambiente virtual .venv...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado com sucesso!
) else (
    echo [1/5] Ambiente virtual .venv ja existente.
)

:: 3. Ativacao do Ambiente Virtual
echo [2/5] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

:: 4. Instalacao de Dependencias
echo [3/5] Instalando dependencias do requirements.txt...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

:: 5. Instalacao dos Binarios do Playwright
echo [4/5] Instalando navegador Chromium via Playwright...
python -m playwright install chromium

:: 6. Configuracao do .env
if not exist ".env" (
    if exist ".env.example" (
        echo [5/5] Gerando arquivo .env a partir do .env.example...
        copy .env.example .env >nul
    )
)

:: 7. Menu Interativo - Escopo dos Testes
echo.
echo ================== ESCOLHA O ESCOPO DOS TESTES ==================
echo  [1] Suite Completa - Todas as features
echo  [2] Registro de Usuario - features\registration.feature
echo  [3] Autenticacao / Login - features\login.feature
echo  [4] Transferencia de Fundos - features\transfer.feature
echo ================================================================
set /p SCOPE="Escolha uma opcao [1-4] (Padrao: 1): "

if "%SCOPE%"=="" set SCOPE=1
set FEATURE_PATH=

if "%SCOPE%"=="1" (
    set FEATURE_PATH=
    echo [*] Escopo: Suite Completa
) else if "%SCOPE%"=="2" (
    set FEATURE_PATH=features\registration.feature
    echo [*] Escopo: Registro de Usuario
) else if "%SCOPE%"=="3" (
    set FEATURE_PATH=features\login.feature
    echo [*] Escopo: Login
) else if "%SCOPE%"=="4" (
    set FEATURE_PATH=features\transfer.feature
    echo [*] Escopo: Transferencia de Fundos
) else (
    echo [AVISO] Opcao invalida. Executando suite completa por padrao.
    set FEATURE_PATH=
)

:: 8. Menu Interativo - Modo Visual (Headed)
echo.
set /p HEADED="Deseja ver o navegador em tela durante os testes? (Headed) [s/N]: "
set HEADLESS_FLAG=-D headless=true
if /i "%HEADED%"=="s" set HEADLESS_FLAG=-D headless=false
if /i "%HEADED%"=="sim" set HEADLESS_FLAG=-D headless=false

:: 9. Limpeza de Relatorios Anteriores
if not exist "reports\allure-results" mkdir "reports\allure-results"
del /q /f "reports\allure-results\*" 2>nul

:: 10. Execucao dos Testes
echo.
echo ============================================================
echo   🚀 Executando testes com Behave...
echo ============================================================
echo.

if "%FEATURE_PATH%"=="" (
    python -m behave %HEADLESS_FLAG%
) else (
    python -m behave %FEATURE_PATH% %HEADLESS_FLAG%
)

:: 11. Geracao e Abertura do Relatorio Allure
echo.
echo ============================================================
echo   📊 Abrindo relatorio Allure Report...
echo ============================================================
echo.

where allure >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    allure serve reports\allure-results
) else (
    echo [AVISO] O utilitario 'allure' nao foi encontrado no PATH do Windows.
    echo Para abrir relatorios graficos, instale via Scoop ou Chocolatey:
    echo   scoop install allure  OU  choco install allure-commandline
    echo Os resultados brutos estao salvos em: reports\allure-results
    pause
)