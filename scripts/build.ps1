$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
python scripts/build.py
if ($LASTEXITCODE -ne 0) { throw "Build failed" }
