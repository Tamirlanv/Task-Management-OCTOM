param([switch]$UnitOnly)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
$previousIntegrationSetting = $env:RUN_INTEGRATION

function Invoke-ProjectCheck {
    param([string]$Executable, [string[]]$CommandArguments)
    & $Executable @CommandArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Check failed: $Executable $CommandArguments"
    }
}

try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        throw 'Create .venv and install dependencies before running checks.'
    }
    if (-not $UnitOnly) {
        $dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
        $dockerExecutable = if ($dockerCommand) {
            $dockerCommand.Source
        } else {
            Join-Path $env:LOCALAPPDATA 'Programs/DockerDesktop/resources/bin/docker.exe'
        }
        if (-not (Test-Path -LiteralPath $dockerExecutable)) {
            throw 'Docker CLI was not found. Start Docker and add its CLI to PATH.'
        }
        Invoke-ProjectCheck $dockerExecutable @('compose', '-f', 'compose.test.yaml', 'up', '-d', '--wait', 'postgres', 'redis')
        $env:RUN_INTEGRATION = '1'
    } else {
        $env:RUN_INTEGRATION = '0'
    }
    Invoke-ProjectCheck '.venv/Scripts/ruff.exe' @('check', '.')
    Invoke-ProjectCheck '.venv/Scripts/black.exe' @('--check', '.')
    Invoke-ProjectCheck '.venv/Scripts/mypy.exe' @('app', 'tests', 'scripts')
    # Keep caches separate for the Windows user and the Codex sandbox account.
    $pytestArguments = @('-m', 'pytest', '-o', "cache_dir=.cache/pytest-$env:USERNAME", '--cov=app', '--cov-report=term-missing', '--cov-report=xml')
    if ($UnitOnly) {
        # A unit-only run is useful feedback, but is not the full coverage gate.
        $pytestArguments += @('tests/unit', '--cov-fail-under=0')
    }
    Invoke-ProjectCheck '.venv/Scripts/python.exe' $pytestArguments
} finally {
    $env:RUN_INTEGRATION = $previousIntegrationSetting
    Pop-Location
}
