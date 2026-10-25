param(
    [Parameter(Mandatory)][string]$RuntimeRoot,
    [Parameter(Mandatory)][string]$Output
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $IsWindows) { throw 'Authenticode verification requires Windows.' }
$root = (Resolve-Path -LiteralPath $RuntimeRoot).Path
$records = @(
    Get-ChildItem -LiteralPath $root -File -Recurse |
        Where-Object { $_.Extension -in '.exe', '.dll' } |
        Sort-Object FullName |
        ForEach-Object {
            $signature = Get-AuthenticodeSignature -LiteralPath $_.FullName
            $status = $signature.Status.ToString()
            if ($status -notin 'Valid', 'NotSigned') {
                throw "Invalid vendor signature: $($_.FullName): $status ($($signature.StatusMessage))"
            }
            [ordered]@{
                path = [IO.Path]::GetRelativePath($root, $_.FullName).Replace('\', '/')
                status = $status
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                signer_thumbprint = if ($null -ne $signature.SignerCertificate) {
                    $signature.SignerCertificate.Thumbprint
                } else { $null }
            }
        }
)
if ($records.Count -eq 0) { throw 'No Windows executables or DLLs were found.' }
ConvertTo-Json -InputObject $records -Depth 5 | Set-Content -LiteralPath $Output -Encoding utf8NoBOM
