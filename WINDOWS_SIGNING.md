# Windows release signing

AtMarkdown public releases must be Authenticode-signed. Product metadata such as
`CompanyName` does not create a verified Windows publisher, and self-signed
certificates do not establish public trust.

## One-time Microsoft Artifact Signing setup

1. In the Azure portal, register the `Microsoft.CodeSigning` resource provider.
2. Create an Artifact Signing account using the Basic SKU.
3. Complete a **Public** individual or organization identity validation. The
   legal name and address in Azure Billing must match the identity being
   validated.
4. Create a **Public Trust** certificate profile. Do not use `Public Trust Test`
   for files distributed to users.
5. Assign the person or service principal that performs releases the
   `Artifact Signing Certificate Profile Signer` role.
6. Install Microsoft Artifact Signing Client Tools on the build machine and
   authenticate to Azure.

Official setup documentation:

- https://learn.microsoft.com/azure/artifact-signing/quickstart
- https://learn.microsoft.com/azure/artifact-signing/how-to-signing-integrations

## Build a signed release

Run PowerShell from this directory after authenticating with an identity that
has the signer role:

```powershell
.\build_signed_release.ps1 `
    -Endpoint "https://eus.codesigning.azure.net/" `
    -AccountName "your-account-name" `
    -CertificateProfileName "your-profile-name"
```

Validate the local signing toolchain without building or contacting Azure:

```powershell
.\build_signed_release.ps1 `
    -Endpoint "https://eus.codesigning.azure.net/" `
    -AccountName "your-account-name" `
    -CertificateProfileName "your-profile-name" `
    -ValidateOnly
```

Use the endpoint shown on the Artifact Signing account Overview page. The
script deliberately stops instead of producing a release if signing,
timestamping, EXE verification, or Microsoft WebView2 DLL verification fails.
It generates `dist\AtMarkdown.exe` and `dist\AtMarkdown.zip` only after the
signature is verified.

Never modify the EXE after signing. Sign every public version with the same
publisher identity so Microsoft SmartScreen reputation can accumulate.

## Free personal-use release

For computers controlled by the same owner, a self-signed publisher can be
used without Azure or a paid certificate:

```powershell
.\build_personal_release.ps1
```

The private key remains in `Cert:\CurrentUser\My` on the build computer. The
generated `dist\AtMarkdown-Personal.zip` contains only the signed application,
the public certificate, a trust installation/removal script, and fingerprint
instructions. Each destination computer must explicitly install that public
certificate into its current-user Trusted Root and Trusted Publishers stores.

This is suitable only for personal/internal computers. It does not establish
public Microsoft SmartScreen reputation and must not be used for general
distribution.
