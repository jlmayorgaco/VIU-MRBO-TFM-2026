param(
    [switch]$SkipBiber
)

# Compila la versión 2 de la memoria (main-v2.tex) en pre-thesis/build-v2.
#
# No ejecuta las verificaciones de `build.ps1`: el sello de
# config/release-manifest.json y el presupuesto de config/page-budget.yaml
# describen la v1 congelada, y la v2 añade material por definición.
# `build.ps1 -Target thesis -Verify` sigue siendo la vía de la v1.
#
# NOTA PowerShell 5.1: no redirigir stderr de lualatex/biber con 2>&1.
# MiKTeX escribe avisos en stderr y la redirección los convierte en
# ErrorRecord, abortando la compilación aunque el código de salida sea 0.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "El comando '$Command' terminó con código $LASTEXITCODE."
    }
}

$Root = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$BuildEpochPath = Join-Path $Root "config/build-epoch.txt"
if (-not (Test-Path -LiteralPath $BuildEpochPath -PathType Leaf)) {
    throw "Falta el epoch reproducible: $BuildEpochPath"
}
$BuildEpoch = (Get-Content -LiteralPath $BuildEpochPath -Raw).Trim()

$PreviousSourceDateEpoch = [Environment]::GetEnvironmentVariable("SOURCE_DATE_EPOCH", "Process")
$PreviousForceSourceDate = [Environment]::GetEnvironmentVariable("FORCE_SOURCE_DATE", "Process")
[Environment]::SetEnvironmentVariable("SOURCE_DATE_EPOCH", $BuildEpoch, "Process")
[Environment]::SetEnvironmentVariable("FORCE_SOURCE_DATE", "1", "Process")

$OutputDirectory = Join-Path $Root "build-v2"
$JobName = "main-v2"

Push-Location $Root
try {
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

    $latexArguments = @(
        "-interaction=nonstopmode",
        "-file-line-error",
        "-jobname=$JobName",
        "-output-directory=$OutputDirectory",
        "main-v2.tex"
    )

    Invoke-Checked -Command "lualatex" -Arguments $latexArguments
    if (-not $SkipBiber) {
        Invoke-Checked -Command "biber" -Arguments @((Join-Path $OutputDirectory $JobName))
    }
    Invoke-Checked -Command "lualatex" -Arguments $latexArguments
    Invoke-Checked -Command "lualatex" -Arguments $latexArguments

    $PdfPath = Join-Path $OutputDirectory "$JobName.pdf"
    Write-Host "PDF generado en: $PdfPath"
}
finally {
    Pop-Location
    [Environment]::SetEnvironmentVariable("SOURCE_DATE_EPOCH", $PreviousSourceDateEpoch, "Process")
    [Environment]::SetEnvironmentVariable("FORCE_SOURCE_DATE", $PreviousForceSourceDate, "Process")
}
