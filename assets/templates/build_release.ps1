[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$AddonStage,
    [Parameter(Mandatory = $true)]
    [string]$OutputGma,
    [string]$GmadPath,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Get-Manifest {
    param([string]$Root, [switch]$ExcludeAddonJson)
    $manifest = @{}
    Get-ChildItem -LiteralPath $Root -File -Recurse | ForEach-Object {
        $relative = $_.FullName.Substring($Root.Length).TrimStart('\','/').Replace('\','/')
        if ($ExcludeAddonJson -and $relative -ieq 'addon.json') { return }
        $manifest[$relative.ToLowerInvariant()] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
    return $manifest
}

function Compare-Manifest {
    param([hashtable]$Expected, [hashtable]$Actual)
    $differences = @()
    foreach ($key in @($Expected.Keys + $Actual.Keys | Sort-Object -Unique)) {
        if (-not $Expected.ContainsKey($key)) {
            $differences += [pscustomobject]@{ path = $key; issue = 'unexpected' }
        } elseif (-not $Actual.ContainsKey($key)) {
            $differences += [pscustomobject]@{ path = $key; issue = 'missing' }
        } elseif ($Expected[$key] -ne $Actual[$key]) {
            $differences += [pscustomobject]@{ path = $key; issue = 'hash_mismatch' }
        }
    }
    return $differences
}

$stage = (Resolve-Path -LiteralPath $AddonStage).Path.TrimEnd('\','/')
if (-not (Test-Path -LiteralPath $stage -PathType Container)) { throw "Addon stage is not a directory: $stage" }
if (-not (Test-Path -LiteralPath (Join-Path $stage 'addon.json') -PathType Leaf)) { throw 'addon.json is missing from addon stage' }

$output = [IO.Path]::GetFullPath($OutputGma)
if ([IO.Path]::GetExtension($output) -ine '.gma') { throw 'OutputGma must end in .gma' }
$stagePrefix = $stage + [IO.Path]::DirectorySeparatorChar
if ($output.StartsWith($stagePrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Output GMA cannot be inside addon stage' }
$outputParent = Split-Path -Parent $output
New-Item -ItemType Directory -Path $outputParent -Force | Out-Null

if (-not $GmadPath) {
    $command = Get-Command gmad.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) { $GmadPath = $command.Source }
}
if (-not $GmadPath) {
    foreach ($drive in 'C','D','E','F','G','H') {
        foreach ($candidate in @(
            "${drive}:\SteamLibrary\steamapps\common\GarrysMod\bin\gmad.exe",
            "${drive}:\Steam\steamapps\common\GarrysMod\bin\gmad.exe"
        )) {
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { $GmadPath = $candidate; break }
        }
        if ($GmadPath) { break }
    }
}
if (-not $GmadPath -or -not (Test-Path -LiteralPath $GmadPath -PathType Leaf)) { throw 'gmad.exe was not found; pass -GmadPath' }

$forbidden = @('.blend','.fbx','.qc','.qci','.smd','.dmx','.vta','.psd','.kra','.bak','.log','.tmp')
$developmentFiles = @(Get-ChildItem -LiteralPath $stage -File -Recurse | Where-Object { $forbidden -contains $_.Extension.ToLowerInvariant() })
if ($developmentFiles.Count -gt 0) {
    throw "Addon stage contains development files: $($developmentFiles.FullName -join ', ')"
}

if (Test-Path -LiteralPath $output -PathType Leaf) {
    if (-not $Force) { throw "Output already exists; use -Force to preserve a timestamped backup and replace it: $output" }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    Copy-Item -LiteralPath $output -Destination "$output.$stamp.bak" -Force
}

$verify = Join-Path $outputParent ('.gma_verify_' + [Guid]::NewGuid().ToString('N'))
$verifyFull = [IO.Path]::GetFullPath($verify)
$safePrefix = ([IO.Path]::GetFullPath($outputParent)).TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
if (-not $verifyFull.StartsWith($safePrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe verification directory' }
New-Item -ItemType Directory -Path $verifyFull | Out-Null

try {
    & $GmadPath create -folder $stage -out $output
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $output -PathType Leaf)) { throw "GMad create failed with exit code $LASTEXITCODE" }
    & $GmadPath extract -file $output -out $verifyFull
    if ($LASTEXITCODE -ne 0) { throw "GMad extract failed with exit code $LASTEXITCODE" }

    $expected = Get-Manifest -Root $stage -ExcludeAddonJson
    $actual = Get-Manifest -Root $verifyFull
    $differences = @(Compare-Manifest -Expected $expected -Actual $actual)
    if ($differences.Count -gt 0) { throw "GMA verification found $($differences.Count) file differences" }

    $receipt = [ordered]@{
        generated_at = [DateTimeOffset]::Now.ToString('o')
        addon_stage = $stage
        output_gma = $output
        output_bytes = (Get-Item -LiteralPath $output).Length
        output_sha256 = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash
        verified_files = $expected.Count
        differences = 0
    }
    $receiptPath = "$output.receipt.json"
    $tempReceipt = "$receiptPath.tmp"
    $receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $tempReceipt -Encoding UTF8
    Move-Item -LiteralPath $tempReceipt -Destination $receiptPath -Force
    $receipt | Format-List
} finally {
    if (Test-Path -LiteralPath $verifyFull -PathType Container) {
        Remove-Item -LiteralPath $verifyFull -Recurse -Force
    }
}
