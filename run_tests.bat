@echo off
chcp 65001 >nul
:: Força o diretório de execução a ser a pasta onde este arquivo .bat está salvo
cd /d "%~dp0"
title Parabank Automation Runner

echo ============================================================
echo   🚀 SETUP E EXECUÇÃO DE TESTES - PARABANK (WINDOWS)
echo ============================================================
echo Diretório do projeto: %CD%
echo.

:: 1. Checagem do Python
where python >nul 2>nul
if errorlevel 1 goto NO_PYTHON

:: 2. Criar ou pular criação da VENV
if exist ".venv" goto VENV_EXISTS
echo [1/5] Criando ambiente virtual na pasta .venv...
python -m venv .venv
if errorlevel 1 goto VENV_FAIL
echo [OK] Ambiente virtual criado com sucesso!
goto ACTIVATE_VENV

:VENV_EXISTS
echo [1/5] Ambiente virtual .venv já detectado.

:ACTIVATE_VENV
echo [2/5] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

:: 3. Instalação de Dependências
echo [3/5] Instalando dependencias do requirements.txt...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

:: 4. Instalação do Chromium
echo [4/5] Instalando navegador Chromium via Playwright...
python -m playwright install chromium

:: 5. Geração do .env
if exist ".env" goto MENU
if exist ".env.example" (
    echo [5/5] Criando .env a partir do .env.example...
    copy .env.example .env >nul
)

:MENU
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

if "%SCOPE%"=="1" set FEATURE_PATH=
if "%SCOPE%"=="2" set FEATURE_PATH=features\registration.feature
if "%SCOPE%"=="3" set FEATURE_PATH=features\login.feature
if "%SCOPE%"=="4" set FEATURE_PATH=features\transfer.feature

echo.
set /p HEADED="Deseja ver o navegador em tela durante os testes? (Headed) [s/N]: "
set HEADLESS_FLAG=-D headless=true
if /i "%HEADED%"=="s" set HEADLESS_FLAG=-D headless=false
if /i "%HEADED%"=="sim" set HEADLESS_FLAG=-D headless=false

:: Limpar relatórios antigos
if not exist "reports\allure-results" mkdir "reports\allure-results"
del /q /f "reports\allure-results\*" 2>nul

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

echo.
echo ============================================================
echo   📊 Abrindo relatorio Allure Report...
echo ============================================================
echo.

where allure >nul 2>nul
if errorlevel 1 goto NO_ALLURE

allure serve reports\allure-results
goto END

:NO_PYTHON
echo [ERRO] Python nao encontrado no PATH do sistema.
echo Instale o Python 3.10+ e marque a opcao Add Python to PATH.
pause
exit /b 1

:VENV_FAIL
echo [ERRO] Falha ao criar o ambiente virtual .venv.
pause
exit /b 1

:NO_ALLURE
echo [AVISO] O utilitario 'allure' nao foi encontrado no PATH do Windows.
echo Instale via Scoop: scoop install allure
echo Resultados brutos salvos em: reports\allure-results
pause

:END