Set-StrictMode -Version Latest

# NOTA: no se usa $ErrorActionPreference = 'Stop'.
# MiKTeX escribe avisos en stderr (p. ej. "major issue: So far, you have not
# checked for updates as a MiKTeX user"). Si el llamador captura stderr
# (tarea de VS Code, redireccion 2>&1, CI), PowerShell 5.1 convierte cada
# linea en un ErrorRecord y aborta la compilacion aunque LuaLaTeX haya
# terminado con codigo 0. El control de errores se hace con $LASTEXITCODE.

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [switch]$AllowFailure
    )

    $exe = Get-Command $Command -ErrorAction SilentlyContinue
    if ($null -eq $exe) {
        throw "No se encontro '$Command' en PATH. Instale MiKTeX/TeX Live y reabra la consola."
    }

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        if ($AllowFailure) {
            Write-Warning "'$Command' termino con codigo $LASTEXITCODE (no bloqueante)."
            return
        }
        throw "El comando '$Command' termino con codigo $LASTEXITCODE."
    }
}

Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path 'build' | Out-Null
    $latexArguments = @(
        '-interaction=nonstopmode',
        '-halt-on-error',
        '-output-directory=build',
        'sp1.tex'
    )

    # El documento carga fontspec y exige LuaTeX: pdflatex aborta con
    # "Este documento requiere LuaLaTeX" seguido de un error fatal de fontspec.
    Invoke-Checked -Command 'lualatex' -Arguments $latexArguments

    # Actualmente sp1.tex no emite ninguna cita, por lo que biber no tiene
    # trabajo real; se mantiene por si se anaden referencias y no bloquea.
    Invoke-Checked -Command 'biber' -Arguments @('build/sp1') -AllowFailure

    Invoke-Checked -Command 'lualatex' -Arguments $latexArguments
    Invoke-Checked -Command 'lualatex' -Arguments $latexArguments

    Copy-Item -LiteralPath 'build/sp1.pdf' -Destination 'sp1.pdf' -Force
    Write-Host "PDF generado en: $PSScriptRoot\sp1.pdf"
}
finally {
    Pop-Location
}
