param(
    [switch]$SkipBiber
)

# Compila el material suplementario (supplementary/main.tex) en
# pre-thesis/supplementary/build. Documento independiente, sin límite de
# páginas, no depositado como TFM: no ejecuta las verificaciones ni el
# sello de build.ps1 (esos describen la v1 congelada y monograph/).
#
# NOTA PowerShell 5.1: no redirigir stderr de lualatex/biber con 2>&1.

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

$OutputDirectory = Join-Path $Root "supplementary/build"
$JobName = "supplementary"

Push-Location $Root
try {
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

    # Un .aux obsoleto se lee antes de que biblatex defina \abx@aux@...; como \a
    # SI existe en LaTeX (acento de tabbing), no hay error y la linea se compone
    # como texto: la portada llego a imprimir
    # "bx@aux@defaultrefcontext0zlotStentz2006ComplexTasksnyt/global//global/...".
    # Se retiran los auxiliares antes de la primera pasada; las tres pasadas
    # posteriores los reconstruyen.
    foreach ($ext in @("aux", "bcf", "run.xml", "toc", "out")) {
        $stale = Join-Path $OutputDirectory "$JobName.$ext"
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }

    $latexArguments = @(
        "-interaction=nonstopmode",
        "-file-line-error",
        "-jobname=$JobName",
        "-output-directory=$OutputDirectory",
        "supplementary/main.tex"
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
