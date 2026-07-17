param(
    [switch]$SkipBiber
)

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

Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path "build" | Out-Null

    Invoke-Checked -Command "python" -Arguments @(
        "..\scripts\export_aws_industrial2_latex.py"
    )

    Invoke-Checked -Command "python" -Arguments @(
        "..\src\viu_mrob_tfm\literature_coverage.py",
        "--ledger", "..\references\LITERATURE_LEDGER.md",
        "--output", "generated\literature-coverage.tex"
    )

    $latexArguments = @(
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory=build",
        "main.tex"
    )

    Invoke-Checked -Command "lualatex" -Arguments $latexArguments
    if (-not $SkipBiber) {
        Invoke-Checked -Command "biber" -Arguments @("build/main")
    }
    Invoke-Checked -Command "lualatex" -Arguments $latexArguments
    Invoke-Checked -Command "lualatex" -Arguments $latexArguments

    Write-Host "PDF generado en: $PSScriptRoot\build\main.pdf"
}
finally {
    Pop-Location
}
