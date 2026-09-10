$ErrorActionPreference = "Stop"

function Test-PythonCommand {
    param(
        [string]$Command,
        [string[]]$Arguments = @()
    )

    try {
        & $Command @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Find-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (Test-PythonCommand -Command "python") {
            return "python"
        }
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($version in @("-3.14", "-3.13", "-3.12", "-3.11", "-3.10")) {
            if (Test-PythonCommand -Command "py" -Arguments @($version)) {
                return "py $version"
            }
        }
    }

    $roots = @(
        "$env:LOCALAPPDATA\Programs\Python",
        "$env:ProgramFiles\Python314",
        "$env:ProgramFiles\Python313",
        "$env:ProgramFiles\Python312",
        "$env:ProgramFiles\Python311",
        "$env:ProgramFiles\Python310"
    )

    foreach ($root in $roots) {
        if (-not (Test-Path $root)) {
            continue
        }

        $candidates = Get-ChildItem -Path $root -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending

        foreach ($candidate in $candidates) {
            if (Test-PythonCommand -Command $candidate.FullName) {
                return $candidate.FullName
            }
        }
    }

    return $null
}

$existing = Find-Python

if ($existing) {
    Write-Output $existing
    exit 0
}

Write-Host "[python] Python 3.10+ não foi encontrado."
Write-Host ""

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "[python] Instalando Python 3.12 via WinGet..."

    winget install `
        --exact `
        --id Python.Python.3.12 `
        --accept-package-agreements `
        --accept-source-agreements

    if ($LASTEXITCODE -ne 0) {
        throw "A instalação do Python via WinGet falhou."
    }
}
else {
    Write-Host "[python] WinGet não está disponível; usando instalador oficial do Python."

    $version = "3.12.10"
    $architecture = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") {
        "arm64"
    }
    else {
        "amd64"
    }

    $installerName = "python-$version-$architecture.exe"
    $downloadUrl = "https://www.python.org/ftp/python/$version/$installerName"
    $installerPath = Join-Path $env:TEMP $installerName

    Invoke-WebRequest `
        -Uri $downloadUrl `
        -OutFile $installerPath `
        -UseBasicParsing

    try {
        $process = Start-Process `
            -FilePath $installerPath `
            -ArgumentList @(
                "/quiet",
                "InstallAllUsers=0",
                "PrependPath=1",
                "Include_launcher=1",
                "Include_pip=1",
                "Include_test=0"
            ) `
            -Wait `
            -PassThru

        if ($process.ExitCode -ne 0) {
            throw "O instalador oficial do Python retornou código $($process.ExitCode)."
        }
    }
    finally {
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
    }
}

$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = "$machinePath;$userPath"

$python = Find-Python

if (-not $python) {
    throw "Python foi instalado, mas ainda não pôde ser localizado. Feche e abra o terminal e execute novamente."
}

Write-Host "[python] Python pronto."
Write-Output $python
