param(
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$certificatePath = Join-Path $PSScriptRoot "ToolsBuilt-Personal-Publisher.cer"
$exePath = Join-Path $PSScriptRoot "AtMarkdown.exe"

if (-not (Test-Path -LiteralPath $certificatePath)) {
    throw "Publisher certificate not found next to this script: $certificatePath"
}

$certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($certificatePath)
$thumbprint = $certificate.Thumbprint
$storeNames = @("Root", "TrustedPublisher")

if ($Remove) {
    foreach ($storeName in $storeNames) {
        $store = [System.Security.Cryptography.X509Certificates.X509Store]::new(
            $storeName,
            [System.Security.Cryptography.X509Certificates.StoreLocation]::CurrentUser
        )
        try {
            $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
            $certificatesToRemove = $store.Certificates.Find(
                [System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint,
                $thumbprint,
                $false
            )
            foreach ($certificateToRemove in $certificatesToRemove) {
                $store.Remove($certificateToRemove)
            }
        } finally {
            $store.Close()
        }
    }
    Write-Host "Removed personal publisher trust for certificate $thumbprint" -ForegroundColor Green
    exit 0
}

Write-Host "You are about to trust this private publisher for the CURRENT USER only:" -ForegroundColor Yellow
Write-Host "Subject: $($certificate.Subject)"
Write-Host "Thumbprint: $thumbprint"
Write-Host "Expires: $($certificate.NotAfter)"
Write-Host "Only continue on a computer you control and after comparing the thumbprint with PERSONAL-RELEASE-README.txt."

$confirmation = Read-Host "Type TRUST to continue"
if ($confirmation -cne "TRUST") {
    throw "Publisher trust installation was cancelled."
}

foreach ($storeName in $storeNames) {
    $store = [System.Security.Cryptography.X509Certificates.X509Store]::new(
        $storeName,
        [System.Security.Cryptography.X509Certificates.StoreLocation]::CurrentUser
    )
    try {
        $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
        $existing = $store.Certificates.Find(
            [System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint,
            $thumbprint,
            $false
        )
        if ($existing.Count -eq 0) {
            $store.Add($certificate)
        }
    } finally {
        $store.Close()
    }
}

Write-Host "Personal publisher installed for the current user." -ForegroundColor Green
if (Test-Path -LiteralPath $exePath) {
    $signature = Get-AuthenticodeSignature -LiteralPath $exePath
    Write-Host "AtMarkdown signature status: $($signature.Status)"
    Write-Host "Publisher: $($signature.SignerCertificate.Subject)"
    if ($signature.Status -ne "Valid") {
        throw "The AtMarkdown signature is not valid after installing publisher trust: $($signature.StatusMessage)"
    }
}
