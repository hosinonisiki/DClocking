$ErrorActionPreference = "Stop"
$McpArguments = @($args)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VirtualEnvironment = Join-Path $ProjectRoot ".venv"
$Python = Join-Path $VirtualEnvironment "Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements-mcp.txt"
$RequirementsStamp = Join-Path $VirtualEnvironment ".mcp-requirements.sha256"

Set-Location $ProjectRoot

if (-not (Test-Path $Python)) {
    $EnvironmentCreated = $false
    $PythonCandidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $PythonCandidates += [PSCustomObject]@{
            Command = "py"
            PrefixArguments = @("-3")
        }
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        $PythonCandidates += [PSCustomObject]@{
            Command = "python3"
            PrefixArguments = @()
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonCandidates += [PSCustomObject]@{
            Command = "python"
            PrefixArguments = @()
        }
    }
    foreach ($Candidate in $PythonCandidates) {
        $Command = $Candidate.Command
        $PrefixArguments = $Candidate.PrefixArguments
        & $Command @PrefixArguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -ne 0) {
            continue
        }
        & $Command @PrefixArguments -m venv $VirtualEnvironment 1>&2
        $EnvironmentCreated = ($LASTEXITCODE -eq 0) -and (Test-Path $Python)
        if ($EnvironmentCreated) {
            break
        }
    }
    if (-not $EnvironmentCreated) {
        throw "Python 3 was not found or the virtual environment could not be created. Python 3.10 or newer is required."
    }
}

& $Python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "The project virtual environment must use Python 3.10 or newer."
}

$RequirementsHash = (Get-FileHash -Algorithm SHA256 $Requirements).Hash
$InstalledHash = if (Test-Path $RequirementsStamp) {
    (Get-Content $RequirementsStamp -Raw).Trim()
} else {
    ""
}
if ($RequirementsHash -ne $InstalledHash) {
    & $Python -m pip install --disable-pip-version-check -r $Requirements 1>&2
    if ($LASTEXITCODE -ne 0) {
        throw "Python dependencies failed to install."
    }
    Set-Content -Path $RequirementsStamp -Value $RequirementsHash -Encoding ascii
}

& $Python -m FPGA_Agent.mcp_server @McpArguments
if ($LASTEXITCODE -ne 0) {
    throw "DClocking MCP Server exited with code $LASTEXITCODE."
}
