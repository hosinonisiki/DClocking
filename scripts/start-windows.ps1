param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VirtualEnvironment = Join-Path $ProjectRoot ".venv"
$Python = Join-Path $VirtualEnvironment "Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$RequirementsStamp = Join-Path $VirtualEnvironment ".requirements.sha256"

Set-Location $ProjectRoot

if (-not (Test-Path $Python)) {
    $EnvironmentCreated = $false
    $Launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($Launcher) {
        & py -3.12 -m venv $VirtualEnvironment
        $EnvironmentCreated = ($LASTEXITCODE -eq 0) -and (Test-Path $Python)
        if (-not $EnvironmentCreated) {
            # A machine may have the Python launcher without Python 3.12.
            # Fall back to its newest installed Python 3 interpreter.
            & py -3 -m venv $VirtualEnvironment
            $EnvironmentCreated = ($LASTEXITCODE -eq 0) -and (Test-Path $Python)
        }
    }
    if (-not $EnvironmentCreated -and (Get-Command python -ErrorAction SilentlyContinue)) {
        & python -m venv $VirtualEnvironment
        $EnvironmentCreated = ($LASTEXITCODE -eq 0) -and (Test-Path $Python)
    }
    if (-not $EnvironmentCreated) {
        throw "Python 3 was not found or the virtual environment could not be created."
    }
}

if (-not $SkipInstall) {
    $RequirementsHash = (Get-FileHash -Algorithm SHA256 $Requirements).Hash
    $InstalledHash = if (Test-Path $RequirementsStamp) {
        (Get-Content $RequirementsStamp -Raw).Trim()
    } else {
        ""
    }
    if ($RequirementsHash -ne $InstalledHash) {
        & $Python -m pip install --disable-pip-version-check -r $Requirements
        if ($LASTEXITCODE -ne 0) {
            throw "Python dependencies failed to install."
        }
        Set-Content -Path $RequirementsStamp -Value $RequirementsHash -Encoding ascii
    }
}

& $Python "python control\qt_UI1.py"
if ($LASTEXITCODE -ne 0) {
    throw "DClocking exited with code $LASTEXITCODE."
}
