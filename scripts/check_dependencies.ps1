[CmdletBinding()]
param(
    [string]$JsonPath,
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Get-FirstExistingPath {
    param([string[]]$Candidates)
    foreach ($candidate in @($Candidates)) {
        if ([string]::IsNullOrWhiteSpace([string]$candidate)) { continue }
        try {
            $resolved = (Resolve-Path -LiteralPath ([string]$candidate) -ErrorAction Stop).Path
            if (Test-Path -LiteralPath $resolved -PathType Leaf) { return $resolved }
        } catch { }
    }
    return $null
}

function Get-CommandPath {
    param([string[]]$Names)
    foreach ($name in $Names) {
        $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($command) { return $command.Source }
    }
    return $null
}

function Get-FileVersionText {
    param([string]$Path)
    if (-not $Path) { return $null }
    try {
        $version = (Get-Item -LiteralPath $Path).VersionInfo.ProductVersion
        if ($version) { return $version.Trim() }
    } catch { }
    return $null
}

function New-ToolResult {
    param(
        [string]$Name,
        [bool]$Required,
        [string]$Path,
        [string]$Version,
        [string]$Source,
        [string]$InstallUrl
    )
    [pscustomobject]@{
        Category = $(if ($Required) { 'required' } else { 'recommended' })
        Name = $Name
        Status = $(if ($Path) { 'FOUND' } else { 'MISSING' })
        Version = $(if ($Version) { $Version } else { '' })
        Path = $(if ($Path) { $Path } else { '' })
        FoundBy = $(if ($Path) { $Source } else { '' })
        InstallUrl = $InstallUrl
    }
}

function Get-SteamRoots {
    $roots = New-Object System.Collections.Generic.List[string]
    $defaults = @(
        'C:\Program Files (x86)\Steam',
        'C:\Program Files\Steam'
    )
    foreach ($drive in 'C','D','E','F','G','H') {
        $defaults += "${drive}:\SteamLibrary"
        $defaults += "${drive}:\Steam"
    }
    foreach ($path in $defaults) {
        if ((Test-Path -LiteralPath $path -PathType Container) -and -not $roots.Contains($path)) {
            $roots.Add((Resolve-Path -LiteralPath $path).Path)
        }
    }

    foreach ($root in @($roots)) {
        $vdf = Join-Path $root 'steamapps\libraryfolders.vdf'
        if (-not (Test-Path -LiteralPath $vdf -PathType Leaf)) { continue }
        foreach ($match in [regex]::Matches((Get-Content -Raw -LiteralPath $vdf), '"path"\s+"([^"]+)"')) {
            $library = $match.Groups[1].Value.Replace('\\', '\')
            if ((Test-Path -LiteralPath $library -PathType Container) -and -not $roots.Contains($library)) {
                $roots.Add((Resolve-Path -LiteralPath $library).Path)
            }
        }
    }
    return @($roots)
}

$steamRoots = Get-SteamRoots
$gmodRoots = @()
$blenderCandidates = @()
foreach ($root in $steamRoots) {
    $gmodRoots += (Join-Path $root 'steamapps\common\GarrysMod')
    $blenderCandidates += (Join-Path $root 'steamapps\common\Blender\blender.exe')
}
$blenderCandidates += @(
    'C:\Program Files\Blender Foundation\Blender\blender.exe',
    'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe',
    'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe'
)

$blender = Get-CommandPath @('blender.exe','blender')
if (-not $blender) { $blender = Get-FirstExistingPath $blenderCandidates }

$python = Get-CommandPath @('python.exe','python','py.exe','py')
$git = Get-CommandPath @('git.exe','git')

$gmod = $null
foreach ($candidate in $gmodRoots) {
    if (Test-Path -LiteralPath $candidate -PathType Container) {
        $gmod = (Resolve-Path -LiteralPath $candidate).Path
        break
    }
}

$toolCandidates = @{}
foreach ($name in @('studiomdl.exe','hlmv.exe','gmad.exe')) {
    $toolCandidates[$name] = @()
    if ($gmod) {
        $toolCandidates[$name] += (Join-Path $gmod "bin\$name")
        $toolCandidates[$name] += (Join-Path $gmod "garrysmod\bin\$name")
    }
}

$studiomdl = Get-CommandPath @('studiomdl.exe')
if (-not $studiomdl) { $studiomdl = Get-FirstExistingPath $toolCandidates['studiomdl.exe'] }
$hlmv = Get-CommandPath @('hlmv.exe')
if (-not $hlmv) { $hlmv = Get-FirstExistingPath $toolCandidates['hlmv.exe'] }
$gmad = Get-CommandPath @('gmad.exe')
if (-not $gmad) { $gmad = Get-FirstExistingPath $toolCandidates['gmad.exe'] }

$sourceTools = $null
$blenderConfig = Join-Path $env:APPDATA 'Blender Foundation\Blender'
if (Test-Path -LiteralPath $blenderConfig -PathType Container) {
    $sourceTools = Get-ChildItem -LiteralPath $blenderConfig -Directory -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq 'io_scene_valvesource' } |
        Select-Object -ExpandProperty FullName -First 1
}

$portsRoot = Join-Path $env:USERPROFILE 'Documents\GMod_Model_Ports'
$crowbarCandidates = @((Join-Path $env:USERPROFILE 'Downloads\Crowbar.exe'))
$toolFolders = @()
if (Test-Path -LiteralPath $portsRoot -PathType Container) {
    $toolFolders += @(Get-ChildItem -Path (Join-Path $portsRoot '05_*') -Directory -ErrorAction SilentlyContinue)
    $toolFolders += @(Get-ChildItem -Path (Join-Path $portsRoot '*\05_*') -Directory -ErrorAction SilentlyContinue)
    foreach ($folder in @($toolFolders | Sort-Object FullName -Unique)) {
        $crowbarCandidates += @(Get-ChildItem -LiteralPath $folder.FullName -Filter 'Crowbar.exe' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
    }
}
$crowbar = Get-CommandPath @('Crowbar.exe')
if (-not $crowbar) {
    foreach ($candidatePath in $crowbarCandidates) {
        if (Test-Path -LiteralPath $candidatePath -PathType Leaf) {
            $crowbar = (Resolve-Path -LiteralPath $candidatePath).Path
            break
        }
    }
}

$vtfCandidates = @()
foreach ($folder in @($toolFolders | Sort-Object FullName -Unique)) {
    $vtfCandidates += @(Get-ChildItem -LiteralPath $folder.FullName -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -in @('VTFCmd.exe','VTFEdit Reloaded.exe','VTFEdit.exe') } |
        Select-Object -ExpandProperty FullName)
}
$vtf = Get-CommandPath @('VTFCmd.exe','VTFEdit Reloaded.exe','VTFEdit.exe')
if (-not $vtf) {
    foreach ($candidatePath in $vtfCandidates) {
        if (Test-Path -LiteralPath $candidatePath -PathType Leaf) {
            $vtf = (Resolve-Path -LiteralPath $candidatePath).Path
            break
        }
    }
}

$glualint = Get-CommandPath @('glualint.exe','glualint')
$sevenZip = Get-CommandPath @('7z.exe','7z')
if (-not $sevenZip) { $sevenZip = Get-FirstExistingPath @('C:\Program Files\7-Zip\7z.exe') }
$assetRipper = Get-CommandPath @('AssetRipper.GUI.Free.exe','AssetRipper.exe')

$blenderVersion = $null
if ($blender) {
    try { $blenderVersion = (& $blender --version 2>$null | Select-Object -First 1) -replace '^Blender\s+', '' } catch { }
}
$pythonVersion = $null
if ($python) {
    try { $pythonVersion = (& $python --version 2>&1 | Select-Object -First 1) -replace '^Python\s+', '' } catch { }
}
$gitVersion = $null
if ($git) {
    try { $gitVersion = (& $git --version 2>&1 | Select-Object -First 1) -replace '^git version\s+', '' } catch { }
}

$results = @(
    (New-ToolResult 'Garrys Mod' $true $gmod '' 'Steam library' 'https://store.steampowered.com/app/4000/Garrys_Mod/'),
    (New-ToolResult 'Blender' $true $blender $blenderVersion 'PATH or Steam library' 'https://www.blender.org/download/'),
    (New-ToolResult 'Blender Source Tools' $true $sourceTools '' 'Blender user addons' 'http://steamreview.org/BlenderSourceTools/'),
    (New-ToolResult 'Python' $true $python $pythonVersion 'PATH' 'https://www.python.org/downloads/windows/'),
    (New-ToolResult 'StudioMDL' $true $studiomdl (Get-FileVersionText $studiomdl) 'GMod bin or PATH' 'Installed with Garrys Mod'),
    (New-ToolResult 'HLMV' $true $hlmv (Get-FileVersionText $hlmv) 'GMod bin or PATH' 'Installed with Garrys Mod'),
    (New-ToolResult 'GMad' $true $gmad (Get-FileVersionText $gmad) 'GMod bin or PATH' 'Installed with Garrys Mod'),
    (New-ToolResult 'Crowbar' $false $crowbar (Get-FileVersionText $crowbar) 'PATH or common tools folder' 'https://steamcommunity.com/groups/CrowbarTool'),
    (New-ToolResult 'VTFEdit Reloaded or VTFCmd' $false $vtf (Get-FileVersionText $vtf) 'PATH or common tools folder' 'https://developer.valvesoftware.com/wiki/VTFEdit'),
    (New-ToolResult 'GLuaLint' $false $glualint (Get-FileVersionText $glualint) 'PATH' 'https://github.com/FPtje/GLuaFixer'),
    (New-ToolResult '7-Zip' $false $sevenZip (Get-FileVersionText $sevenZip) 'PATH or Program Files' 'https://www.7-zip.org/'),
    (New-ToolResult 'AssetRipper' $false $assetRipper (Get-FileVersionText $assetRipper) 'PATH' 'https://github.com/AssetRipper/AssetRipper'),
    (New-ToolResult 'Git' $false $git $gitVersion 'PATH' 'https://git-scm.com/download/win')
)

$results | Format-Table Category,Name,Status,Version,Path -AutoSize -Wrap
$missingRequired = @($results | Where-Object { $_.Category -eq 'required' -and $_.Status -eq 'MISSING' })
Write-Host ("Required: {0} found, {1} missing" -f (($results | Where-Object { $_.Category -eq 'required' -and $_.Status -eq 'FOUND' }).Count), $missingRequired.Count)

if ($JsonPath) {
    $fullJsonPath = [IO.Path]::GetFullPath($JsonPath)
    $parent = Split-Path -Parent $fullJsonPath
    if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    $report = [ordered]@{
        generated_at = [DateTimeOffset]::Now.ToString('o')
        required_missing = @($missingRequired | ForEach-Object { $_.Name })
        tools = @($results)
    }
    $temp = "$fullJsonPath.tmp"
    $report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $temp -Encoding UTF8
    Move-Item -LiteralPath $temp -Destination $fullJsonPath -Force
    Write-Host "JSON: $fullJsonPath"
}

if ($Strict -and $missingRequired.Count -gt 0) { exit 2 }
exit 0
