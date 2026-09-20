Set-StrictMode -Version Latest

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    if ($null -eq (Get-Command $Command -ErrorAction SilentlyContinue)) {
        throw "No se encontro '$Command' en PATH."
    }
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "El comando '$Command' termino con codigo $LASTEXITCODE."
    }
}

Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path 'build' | Out-Null
    New-Item -ItemType Directory -Force -Path 'generated' | Out-Null
    New-Item -ItemType Directory -Force -Path 'figures/generated' | Out-Null

    $repositoryRoot = (Resolve-Path -LiteralPath '../..').Path
    $sp2Results = Join-Path $repositoryRoot 'results/sp2_canonical/SP2_HONORS_v3'
    $cargoResults = Join-Path $repositoryRoot 'results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1'
    Copy-Item -LiteralPath (Join-Path $sp2Results 'generated/metrics.tex') `
        -Destination 'generated/sp2_ready_metrics.tex' -Force
    Get-ChildItem -LiteralPath (Join-Path $sp2Results 'figures') -Filter '*.pdf' | `
        Copy-Item -Destination 'figures/generated' -Force
    foreach ($name in @('cargo_e2e_numbers.tex', 'cargo_e2e_results.tex', 'cargo_e2e_hypotheses.tex')) {
        Copy-Item -LiteralPath (Join-Path $cargoResults "tables/$name") `
            -Destination (Join-Path 'generated' $name) -Force
    }
    Get-ChildItem -LiteralPath (Join-Path $cargoResults 'figures') -Filter '*.pdf' | `
        Copy-Item -Destination 'figures/generated' -Force

    # Las tres composiciones maestras y la tabla de evidencia se reconstruyen
    # exclusivamente desde los CSV/NPZ archivados. No se editan PDFs generados.
    Invoke-Checked -Command 'python' -Arguments @(
        (Join-Path $repositoryRoot 'scripts/generate_sp2_master_figures.py'),
        '--repo-root', $repositoryRoot,
        '--output-dir', (Join-Path $PSScriptRoot 'figures/generated'),
        '--generated-dir', (Join-Path $PSScriptRoot 'generated')
    )

    $latexArguments = @(
        '-interaction=nonstopmode',
        '-halt-on-error',
        '-output-directory=build',
        'sp2.tex'
    )

    Invoke-Checked -Command 'lualatex' -Arguments $latexArguments
    Invoke-Checked -Command 'biber' -Arguments @('build/sp2')
    Invoke-Checked -Command 'lualatex' -Arguments $latexArguments
    Invoke-Checked -Command 'lualatex' -Arguments $latexArguments

    $log = Get-Content -LiteralPath 'build/sp2.log' -Raw
    if ($log -match '(?i)undefined (references|citations)') {
        throw 'La compilacion contiene referencias o citas sin resolver.'
    }
    if ($log -match 'Overfull \\[hv]box') {
        throw 'La compilacion contiene cajas desbordadas; revise build/sp2.log.'
    }

    $pdfPath = (Resolve-Path -LiteralPath 'build/sp2.pdf').Path
    $pdfInfo = & pdfinfo.exe $pdfPath
    if ($LASTEXITCODE -ne 0) {
        throw "pdfinfo termino con codigo $LASTEXITCODE."
    }
    $pagesLine = $pdfInfo | Where-Object { $_ -match '^Pages:\s+(\d+)' } | Select-Object -First 1
    if ($null -eq $pagesLine -or [int]$matches[1] -gt 20) {
        throw "El informe no puede superar 20 paginas; pdfinfo devolvio: $pagesLine"
    }

    $source = (@('sp2.tex', 'n4_controller_benchmark.tex', 'cargo_e2e_integration.tex') | ForEach-Object {
        Get-Content -LiteralPath $_ -Raw
    }) -join [Environment]::NewLine
    $aux = Get-Content -LiteralPath 'build/sp2.aux' -Raw
    $labelMatches = [regex]::Matches($aux, '\\newlabel\{((?:fig|tab):[^}]+)\}')
    foreach ($match in $labelMatches) {
        $label = $match.Groups[1].Value
        $occurrences = [regex]::Matches($source, [regex]::Escape($label)).Count
        if ($occurrences -lt 2) {
            throw "La figura o tabla '$label' no esta citada en el texto."
        }
    }

    Copy-Item -LiteralPath 'build/sp2.pdf' -Destination 'sp2.pdf' -Force
    $outputDirectory = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) 'output/pdf'
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
    $finalPdf = Join-Path $outputDirectory 'SP2_HONORS_VIU.pdf'
    Copy-Item -LiteralPath 'build/sp2.pdf' -Destination $finalPdf -Force
    Write-Host "PDF generado y verificado (maximo 20 paginas): $finalPdf"
}
finally {
    Pop-Location
}
