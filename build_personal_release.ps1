param(
    [string]$PublisherName = "ToolsBuilt Personal Publisher",
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$subject = "CN=$PublisherName, O=ToolsBuilt"
$friendlyName = "AtMarkdown Personal Code Signing"
$codeSigningOid = "1.3.6.1.5.5.7.3.3"

$certificate = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
    Where-Object {
        $_.FriendlyName -eq $friendlyName -and
        $_.Subject -eq $subject -and
        $_.HasPrivateKey -and
        $_.NotAfter -gt [DateTime]::Now.AddDays(30)
    } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if (-not $certificate) {
    Write-Host "Creating a personal code-signing certificate..." -ForegroundColor Yellow
    $certificate = New-SelfSignedCertificate `
        -Type Custom `
        -Subject $subject `
        -FriendlyName $friendlyName `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -KeyAlgorithm RSA `
        -KeyLength 3072 `
        -HashAlgorithm SHA256 `
        -KeyExportPolicy Exportable `
        -KeyUsage DigitalSignature `
        -TextExtension @(
            "2.5.29.37={text}$codeSigningOid",
            "2.5.29.19={text}CA=false"
        ) `
        -NotAfter ([DateTime]::Now.AddYears(5))
}

& "$PSScriptRoot\build_release.ps1"
if ($LASTEXITCODE -ne 0) {
    throw "Release build failed with exit code $LASTEXITCODE."
}

$distPath = Join-Path $PSScriptRoot "dist"
$exePath = Join-Path $distPath "AtMarkdown.exe"
$dllPath = Join-Path $distPath "WebView2Loader.dll"
$certificatePath = Join-Path $distPath "ToolsBuilt-Personal-Publisher.cer"
$trustScriptSource = Join-Path $PSScriptRoot "install_personal_publisher.ps1"
$trustScriptPath = Join-Path $distPath "Install-Personal-Publisher.ps1"
$readmePath = Join-Path $distPath "README.md"
$legacyReadmePath = Join-Path $distPath "PERSONAL-RELEASE-README.txt"
$zipPath = Join-Path $distPath "AtMarkdown-Personal.zip"

if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Release executable was not created: $exePath"
}

$signTool = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\ArtifactSigningBuildTools" `
    -Recurse -File -Filter "signtool.exe" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '[\\/]x64[\\/]' } |
    Sort-Object FullName -Descending |
    Select-Object -First 1 -ExpandProperty FullName

if (-not $signTool -or -not (Test-Path -LiteralPath $signTool)) {
    throw "x64 SignTool was not found. Install Microsoft.Windows.SDK.BuildTools first."
}

Export-Certificate -Cert $certificate -FilePath $certificatePath -Type CERT -Force | Out-Null

$timestampedArguments = @(
    "sign", "/v",
    "/sha1", $certificate.Thumbprint,
    "/s", "My",
    "/fd", "SHA256",
    "/tr", $TimestampUrl,
    "/td", "SHA256",
    $exePath
)
& $signTool @timestampedArguments

if ($LASTEXITCODE -ne 0) {
    Write-Warning "The timestamp service was unavailable. Signing without a timestamp for personal use."
    & $signTool "sign" "/v" "/sha1" $certificate.Thumbprint "/s" "My" "/fd" "SHA256" $exePath
    if ($LASTEXITCODE -ne 0) {
        throw "Personal Authenticode signing failed with exit code $LASTEXITCODE."
    }
}

$signature = Get-AuthenticodeSignature -LiteralPath $exePath
if (-not $signature.SignerCertificate -or
    $signature.SignerCertificate.Thumbprint -ne $certificate.Thumbprint -or
    $signature.Status -in @("NotSigned", "HashMismatch")) {
    throw "The EXE signature could not be verified against the personal publisher certificate."
}

Copy-Item -LiteralPath $trustScriptSource -Destination $trustScriptPath -Force

$exeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $exePath).Hash
$certificateHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $certificatePath).Hash
$readme = @"
# AtMarkdown Personal Release

Đây là bản dành cho **các máy tính cá nhân do cùng một chủ sở hữu kiểm soát**.
Ứng dụng đã được ký bằng self-signed certificate ``ToolsBuilt Personal Publisher``,
nhưng certificate này không được Microsoft tin cậy công khai.

## Cài và chạy trên máy khác

1. Giải nén toàn bộ ZIP vào cùng một thư mục. Không chạy trực tiếp từ bên trong ZIP.
2. Kiểm tra certificate thumbprint hiển thị bên dưới.
3. Mở PowerShell tại thư mục vừa giải nén.
4. Chạy lệnh:

       powershell -ExecutionPolicy Bypass -File .\Install-Personal-Publisher.ps1

5. Script sẽ hiển thị publisher và thumbprint. Chỉ nhập ``TRUST`` nếu thumbprint
   khớp chính xác với README này.
6. Kiểm tra chữ ký sau khi cài trust:

       Get-AuthenticodeSignature .\AtMarkdown.exe | Format-List Status,StatusMessage

   Giá trị ``Status`` phải là ``Valid``.
7. Chạy ứng dụng:

       .\AtMarkdown.exe

## Gỡ publisher khỏi máy

Khi không còn sử dụng AtMarkdown, chạy:

    powershell -ExecutionPolicy Bypass -File .\Install-Personal-Publisher.ps1 -Remove

Lệnh này chỉ xóa đúng certificate có trong gói khỏi ``Current User\Trusted Root``
và ``Current User\Trusted Publishers``.

## Thông tin xác minh

- Publisher: ``$($certificate.Subject)``
- Certificate thumbprint: ``$($certificate.Thumbprint)``
- Certificate expires: ``$($certificate.NotAfter.ToString("yyyy-MM-dd HH:mm:ss"))``
- AtMarkdown.exe SHA-256: ``$exeHash``
- Certificate SHA-256: ``$certificateHash``

## Lưu ý bảo mật

- Chỉ cài certificate này trên máy bạn sở hữu và kiểm soát.
- Không dùng gói Personal Release để phát hành công khai.
- Không chia sẻ private key trong certificate store của máy build.
- ``WebView2Loader.dll`` đi kèm được Microsoft ký số.
"@
$readme | Set-Content -LiteralPath $readmePath -Encoding UTF8
if (Test-Path -LiteralPath $legacyReadmePath) {
    Remove-Item -LiteralPath $legacyReadmePath -Force
}

$packageFiles = @($exePath, $certificatePath, $trustScriptPath, $readmePath)
if (Test-Path -LiteralPath $dllPath) {
    $dllSignature = Get-AuthenticodeSignature -LiteralPath $dllPath
    if ($dllSignature.Status -ne "Valid") {
        throw "Microsoft WebView2Loader.dll signature is not valid: $($dllSignature.Status)"
    }
    $packageFiles += $dllPath
}

Compress-Archive -LiteralPath $packageFiles -DestinationPath $zipPath -CompressionLevel Optimal -Force
$zipHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath).Hash

Write-Host "PERSONAL RELEASE SUCCESSFUL" -ForegroundColor Green
Write-Host "Publisher: $($certificate.Subject)" -ForegroundColor Cyan
Write-Host "Certificate thumbprint: $($certificate.Thumbprint)" -ForegroundColor Cyan
Write-Host "Output: $zipPath" -ForegroundColor Cyan
Write-Host "SHA256: $zipHash" -ForegroundColor Cyan
Write-Warning "This certificate is trusted only after the public .cer is installed on each personal computer."
