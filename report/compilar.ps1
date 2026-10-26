param(
    [string]$TexBin = '',
    [switch]$InstalarDependencias
)

$ErrorActionPreference = 'Stop'
$reportDir = $PSScriptRoot
$logDir = Join-Path (Split-Path -Parent $reportDir) 'tmp\latex'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

function Resolve-TexTool([string]$Name) {
    if ($TexBin) {
        $candidate = Join-Path $TexBin ($Name + '.exe')
        if (Test-Path -LiteralPath $candidate) { return $candidate }
        throw "No se encuentra $Name en $TexBin."
    }
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $candidate = Join-Path $env:LOCALAPPDATA "Programs\MiKTeX\miktex\bin\x64\$Name.exe"
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    throw "No se encuentra $Name. Instala una distribucion TeX o indica -TexBin."
}

$pdfLatex = Resolve-TexTool 'pdflatex'
$biber = Resolve-TexTool 'biber'
$texArgs = @('--interaction=nonstopmode', '--halt-on-error', '--file-line-error', '--no-shell-escape')
if ($pdfLatex -match 'MiKTeX') {
    if ($InstalarDependencias) { $texArgs += '--enable-installer' }
    else { $texArgs += '--disable-installer' }
}
$texArgs += 'main.tex'

function Invoke-BuildStep([string]$Exe, [string[]]$ToolArgs, [string]$Step) {
    Write-Host $Step
    $stepLog = Join-Path $logDir ($Step + '.txt')
    & $Exe @ToolArgs *> $stepLog
    if ($LASTEXITCODE -ne 0) {
        Get-Content -LiteralPath $stepLog -Tail 40
        throw "Fallo en $Step. Diagnostico: $stepLog"
    }
}

Push-Location $reportDir
try {
    Invoke-BuildStep $pdfLatex $texArgs 'pdflatex-1'
    Invoke-BuildStep $biber @('main') 'biber'
    Invoke-BuildStep $pdfLatex $texArgs 'pdflatex-2'
    Invoke-BuildStep $pdfLatex $texArgs 'pdflatex-3'
    $finalLog = Get-Content -LiteralPath 'main.log' -Raw
    if ($finalLog -match 'Rerun to get cross-references right|Please rerun LaTeX|Rerun to get them right') {
        Invoke-BuildStep $pdfLatex $texArgs 'pdflatex-4'
        $finalLog = Get-Content -LiteralPath 'main.log' -Raw
    }
    if ($finalLog -match 'There were undefined references|Citation .+ undefined|Reference .+ undefined|Please \(re\)run Biber') {
        throw 'La compilacion deja citas o referencias sin resolver. Revisa main.log.'
    }
    if (-not (Test-Path -LiteralPath 'main.pdf')) { throw 'No se ha generado main.pdf.' }
    Write-Host ('PDF generado: ' + (Join-Path $reportDir 'main.pdf'))
}
finally {
    Pop-Location
}
