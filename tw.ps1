$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$src = Join-Path $root "src"
$env:PYTHONPATH = $src

if (-not $env:TRIPWIRE_PROVIDER) {
  $env:TRIPWIRE_PROVIDER = "ollama"
}

if (-not $env:TRIPWIRE_MODEL) {
  $env:TRIPWIRE_MODEL = "qwen3:8b"
}

$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (Test-Path $bundledPython) {
  $python = $bundledPython
} else {
  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if (-not $pythonCommand) {
    Write-Error "Python was not found. Install Python or run this from Codex where bundled Python is available."
    exit 1
  }
  $python = $pythonCommand.Source
}

& $python -m tripwire @args
exit $LASTEXITCODE
