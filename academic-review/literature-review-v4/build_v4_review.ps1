$ErrorActionPreference = 'Stop'

$reviewRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $reviewRoot)
$referencePdf = 'C:\Users\walla\Downloads\MROB_literature_review_reworked (2).pdf'
$outputDir = Join-Path $repoRoot 'output\pdf\literature-review'

python (Join-Path $repoRoot 'academic-review\scripts\build_v4_literature_audit.py') --reference-pdf $referencePdf --repository-root $repoRoot
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

Push-Location $reviewRoot
try {
  & lualatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory $outputDir MROB_literature_review_v4_audited.tex
  & lualatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory $outputDir MROB_literature_review_v4_audited.tex
}
finally {
  Pop-Location
}

$pdf = Join-Path $outputDir 'MROB_literature_review_v4_audited.pdf'
if (-not (Test-Path -LiteralPath $pdf)) {
  throw "Expected PDF was not created: $pdf"
}
Write-Output $pdf
