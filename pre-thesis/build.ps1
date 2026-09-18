param(
    [ValidateSet("thesis", "monograph")]
    [string]$Target = "thesis",
    [switch]$Verify,
    [switch]$AuditSources,
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

$Root = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$BuildEpochPath = Join-Path $Root "config/build-epoch.txt"
if (-not (Test-Path -LiteralPath $BuildEpochPath -PathType Leaf)) {
    throw "Falta el epoch reproducible: $BuildEpochPath"
}
$BuildEpoch = (Get-Content -LiteralPath $BuildEpochPath -Raw).Trim()
if ($BuildEpoch -notmatch '^\d+$') {
    throw "El epoch reproducible debe contener solo segundos Unix: $BuildEpochPath"
}

if ($AuditSources -and -not $Verify) {
    throw "-AuditSources requiere -Verify."
}

$PreviousSourceDateEpoch = [Environment]::GetEnvironmentVariable("SOURCE_DATE_EPOCH", "Process")
$PreviousForceSourceDate = [Environment]::GetEnvironmentVariable("FORCE_SOURCE_DATE", "Process")
[Environment]::SetEnvironmentVariable("SOURCE_DATE_EPOCH", $BuildEpoch, "Process")
[Environment]::SetEnvironmentVariable("FORCE_SOURCE_DATE", "1", "Process")

if ($Target -eq "thesis") {
    $Source = "main.tex"
    $OutputDirectory = Join-Path $Root "build"
    $JobName = "main"
    $TrailerId = "AB8EBD52B6AAD3602B7A8E20B2C3C779"
}
else {
    $Source = "monograph/main.tex"
    $OutputDirectory = Join-Path $Root "monograph/build"
    $JobName = "monograph"
    $TrailerId = "C83E758D23036868C30CD7E3ED216BC3"
}

Push-Location $Root
try {
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
    $EntrySource = Join-Path $OutputDirectory "$JobName-entry.tex"
    $EntryText = (
        "\pdfvariable trailerid {[<$TrailerId> <$TrailerId>]}`n" +
        "\input{$Source}`n"
    )
    [System.IO.File]::WriteAllText(
        $EntrySource,
        $EntryText,
        [System.Text.UTF8Encoding]::new($false)
    )

    if ($Verify) {
        Invoke-Checked -Command "python" -Arguments @(
            "scripts/verify_snapshot_provenance.py"
        )
        Invoke-Checked -Command "python" -Arguments @(
            "scripts/verify_release_manifest.py",
            "--check"
        )
        if ($AuditSources) {
            Invoke-Checked -Command "python" -Arguments @(
                "evidence/tools/build_inventory.py",
                "--check"
            )
            Invoke-Checked -Command "python" -Arguments @(
                "evidence/tools/build_source_claim_review.py",
                "--check"
            )
            Invoke-Checked -Command "python" -Arguments @(
                "evidence/tools/merge_formal_semantic_audits.py",
                "--check"
            )
            Invoke-Checked -Command "python" -Arguments @(
                "evidence/tools/build_idea_ledger.py",
                "--check-index"
            )
            Invoke-Checked -Command "python" -Arguments @(
                "evidence/tools/verify_book_identities.py",
                "--check"
            )
        }
    }

    if ($Target -eq "thesis") {
        Invoke-Checked -Command "python" -Arguments @("scripts/check_protected_tikz_figures.py")
    }

    $latexArguments = @(
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-jobname=$JobName",
        "-output-directory=$OutputDirectory",
        $EntrySource
    )

    Invoke-Checked -Command "lualatex" -Arguments $latexArguments
    if (-not $SkipBiber) {
        Invoke-Checked -Command "biber" -Arguments @((Join-Path $OutputDirectory $JobName))
    }
    Invoke-Checked -Command "lualatex" -Arguments $latexArguments
    Invoke-Checked -Command "lualatex" -Arguments $latexArguments

    $AuxPath = Join-Path $OutputDirectory "$JobName.aux"
    $LogPath = Join-Path $OutputDirectory "$JobName.log"
    $PdfPath = Join-Path $OutputDirectory "$JobName.pdf"
    if ($Target -eq "thesis") {
        Invoke-Checked -Command "python" -Arguments @(
            "scripts/check_protected_tikz_figures.py",
            "--aux", $AuxPath
        )
    }

    if ($Verify) {
        Invoke-Checked -Command "python" -Arguments @(
            "scripts/verify_build.py",
            "--target", $Target,
            "--pdf", $PdfPath,
            "--aux", $AuxPath,
            "--log", $LogPath,
            "--report", (Join-Path $OutputDirectory "verification.json")
        )
        Invoke-Checked -Command "python" -Arguments @(
            "scripts/verify_release_manifest.py",
            "--check",
            "--pdf-target", $Target
        )
    }

    Write-Host "PDF generado en: $PdfPath"
}
finally {
    Pop-Location
    [Environment]::SetEnvironmentVariable("SOURCE_DATE_EPOCH", $PreviousSourceDateEpoch, "Process")
    [Environment]::SetEnvironmentVariable("FORCE_SOURCE_DATE", $PreviousForceSourceDate, "Process")
}
