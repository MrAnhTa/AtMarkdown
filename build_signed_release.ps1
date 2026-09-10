param(
    [Parameter(Mandatory = $true)]
    [string]$Endpoint,

    [Parameter(Mandatory = $true)]
    [string]$AccountName,

    [Parameter(Mandatory = $true)]
    [string]$CertificateProfileName,

    [string]$SignToolPath,
    [string]$DlibPath,

    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Find-LatestTool {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Roots,

        [Parameter(Mandatory = $true)]
        [string]$FileName,

        [switch]$PreferX64
    )

    $foundTools = foreach ($root in $Roots) {
        if ($root -and (Test-Path -LiteralPath $root)) {
            Get-ChildItem -LiteralPath $root -Recurse -File -Filter $FileName -ErrorAction SilentlyContinue
        }
    }

    if ($PreferX64) {
        $x64Tools = $foundTools | Where-Object { $_.FullName -match '[\\/]x64[\\/]' }
        if ($x64Tools) {
            $foundTools = $x64Tools
        }
    }

    return $foundTools | Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}

if ($Endpoint -notmatch '^https://[a-z0-9-]+\.codesigning\.azure\.net/?$') {
    throw "Endpoint must be the region-specific Artifact Signing URI, for example https://eus.codesigning.azure.net/."
}

$toolRoots = @(
    "${env:ProgramFiles(x86)}\Microsoft\ArtifactSigningClientTools",
    "$env:LOCALAPPDATA\Microsoft\MicrosoftArtifactSigningClientTools",
    "$env:LOCALAPPDATA\Microsoft\ArtifactSigningBuildTools",
    "$env:LOCALAPPDATA\Microsoft\ArtifactSigningClientTools",
    "$env:LOCALAPPDATA\TrustedSigning"
)

if (-not $SignToolPath) {
    $SignToolPath = Find-LatestTool -Roots $toolRoots -FileName "signtool.exe" -PreferX64
}
if (-not $DlibPath) {
    $DlibPath = Find-LatestTool -Roots $toolRoots -FileName "Azure.CodeSigning.Dlib.dll"
}

if (-not $SignToolPath -or -not (Test-Path -LiteralPath $SignToolPath)) {
    throw "SignTool was not found. Install Microsoft Artifact Signing Client Tools first."
}
if (-not $DlibPath -or -not (Test-Path -LiteralPath $DlibPath)) {
    throw "Azure.CodeSigning.Dlib.dll was not found. Install Microsoft Artifact Signing Client Tools first."
}

if ($ValidateOnly) {
    Write-Host "SIGNING TOOLCHAIN READY" -ForegroundColor Green
    Write-Host "SignTool: $SignToolPath" -ForegroundColor Cyan
    Write-Host "Artifact Signing Dlib: $DlibPath" -ForegroundColor Cyan
    exit 0
}

# Always rebuild before signing. Any change after signing invalidates Authenticode.
& "$PSScriptRoot\build_release.ps1"
if ($LASTEXITCODE -ne 0) {
    throw "Release build failed with exit code $LASTEXITCODE."
}

$exePath = Join-Path $PSScriptRoot "dist\AtMarkdown.exe"
$dllPath = Join-Path $PSScriptRoot "dist\WebView2Loader.dll"
$zipPath = Join-Path $PSScriptRoot "dist\AtMarkdown.zip"

if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Release executable was not created: $exePath"
}

$metadataPath = [System.IO.Path]::GetTempFileName()
try {
    $metadata = [ordered]@{
        Endpoint = $Endpoint.TrimEnd('/') + '/'
        CodeSigningAccountName = $AccountName
        CertificateProfileName = $CertificateProfileName
        CorrelationId = "AtMarkdown-$([DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss'))"
    }
    $metadata | ConvertTo-Json | Set-Content -LiteralPath $metadataPath -Encoding UTF8

    $signArguments = @(
        "sign",
        "/v",
        "/fd", "SHA256",
        "/tr", "http://timestamp.acs.microsoft.com/",
        "/td", "SHA256",
        "/dlib", $DlibPath,
        "/dmdf", $metadataPath,
        $exePath
    )

    & $SignToolPath @signArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Artifact Signing failed with exit code $LASTEXITCODE."
    }
} finally {
    if (Test-Path -LiteralPath $metadataPath) {
        Remove-Item -LiteralPath $metadataPath -Force
    }
}

$signature = Get-AuthenticodeSignature -LiteralPath $exePath
if ($signature.Status -ne "Valid" -or -not $signature.SignerCertificate) {
    throw "Release signature verification failed: $($signature.Status) - $($signature.StatusMessage)"
}
if (-not $signature.TimeStamperCertificate) {
    throw "The executable is signed but has no trusted timestamp. Release packaging was stopped."
}

if (Test-Path -LiteralPath $dllPath) {
    $dllSignature = Get-AuthenticodeSignature -LiteralPath $dllPath
    if ($dllSignature.Status -ne "Valid") {
        throw "Microsoft WebView2Loader.dll signature is not valid: $($dllSignature.Status)"
    }
    Compress-Archive -LiteralPath $exePath, $dllPath -DestinationPath $zipPath -CompressionLevel Optimal -Force
} else {
    Compress-Archive -LiteralPath $exePath -DestinationPath $zipPath -CompressionLevel Optimal -Force
}

$zipHash = Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath
Write-Host "SIGNED RELEASE SUCCESSFUL" -ForegroundColor Green
Write-Host "Publisher: $($signature.SignerCertificate.Subject)" -ForegroundColor Cyan
Write-Host "Timestamp authority: $($signature.TimeStamperCertificate.Subject)" -ForegroundColor Cyan
Write-Host "Output: $zipPath" -ForegroundColor Cyan
Write-Host "SHA256: $($zipHash.Hash)" -ForegroundColor Cyan
