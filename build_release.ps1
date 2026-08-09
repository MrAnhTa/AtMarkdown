# AtMarkdown Release Build Script
$ErrorActionPreference = "Stop"

Write-Host "🚀 Building AtMarkdown..." -ForegroundColor Green

# Add exact WinLibs GCC bin path to PATH
$WinLibsBin = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin"
if (Test-Path $WinLibsBin) {
    $env:PATH = "$WinLibsBin;$env:PATH"
}

$CargoPath = "$env:USERPROFILE\.cargo\bin\cargo.exe"
if (-not (Test-Path $CargoPath)) {
    $CargoPath = "cargo"
}

# Run Cargo Release Build with 2 parallel jobs
& $CargoPath build --release -j 2

$ExeSource = "target\x86_64-pc-windows-gnu\release\atmarkdown.exe"
if (-not (Test-Path $ExeSource)) {
    $ExeSource = "target\release\atmarkdown.exe"
}

$DllSource = "target\x86_64-pc-windows-gnu\release\WebView2Loader.dll"
if (-not (Test-Path $DllSource)) {
    $DllSource = "target\release\WebView2Loader.dll"
}

$OutputDir = "output"

if (Test-Path $ExeSource) {
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir | Out-Null
    }
    
    $DestExe = "$OutputDir\AtMarkdown.exe"
    Copy-Item $ExeSource $DestExe -Force

    if (Test-Path $DllSource) {
        Copy-Item $DllSource "$OutputDir\WebView2Loader.dll" -Force
    }
    
    $SizeMB = [math]::Round(((Get-Item $DestExe).Length + (Get-Item "$OutputDir\WebView2Loader.dll" -ErrorAction SilentlyContinue).Length) / 1MB, 2)
    Write-Host "BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "Output Directory: $OutputDir (Total Size: $SizeMB MB)" -ForegroundColor Cyan
} else {
    Write-Host "Build failed! Could not find compiled executable." -ForegroundColor Red
}
