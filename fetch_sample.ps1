$ErrorActionPreference = 'Stop'
$url = 'https://raw.githubusercontent.com/VLSIDA/OpenRAM/stable/compiler/tests/golden/sram_2_16_1_freepdk45.sp'
$out = 'd:\workspace\project\logic_effort\samples\reference_sram_2_16_1_freepdk45.sp'
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
try {
    Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -TimeoutSec 30
    Get-Item $out | Select-Object FullName,Length
} catch {
    Write-Host ('ERR: ' + $_.Exception.Message)
    exit 2
}
