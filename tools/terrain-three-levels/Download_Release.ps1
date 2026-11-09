param(
    [ValidateSet('Unity','Windows','All')][string]$Mode='Unity',
    [string]$PartsDirectory='',
    [string]$OutputDirectory='',
    [switch]$LocalOnly,
    [switch]$AssembleOnly,
    [switch]$Extract
)
$ErrorActionPreference='Stop'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Release_Manifest_v0.4.0.json') -Raw | ConvertFrom-Json
if ($manifest.schema -ne 'terrain-release-segments-v1') { throw 'Unsupported manifest.' }
if (-not $OutputDirectory) { $OutputDirectory=Join-Path $PSScriptRoot 'Ready' }
if (-not $PartsDirectory) { $PartsDirectory=Join-Path $PSScriptRoot 'Parts' }
$OutputDirectory=[IO.Path]::GetFullPath($OutputDirectory)
$PartsDirectory=[IO.Path]::GetFullPath($PartsDirectory)
[IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null
[IO.Directory]::CreateDirectory($PartsDirectory) | Out-Null
function FileMatches([string]$Path,[long]$Length,[string]$Hash) {
    if (-not [IO.File]::Exists($Path)) { return $false }
    if ((Get-Item -LiteralPath $Path).Length -ne $Length) { return $false }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -eq $Hash
}
function SafeChild([string]$Folder,[string]$Name) {
    if ($Name -notmatch '^Lunar_(Unity_Project|Unity_Resources|Windows_Demo)_v0\.4\.0\.zip(\.(part[0-9]{3}|chunk[0-9]{4}))?$') { throw 'Unsafe archive filename.' }
    $result=[IO.Path]::GetFullPath((Join-Path $Folder $Name))
    if ([IO.Path]::GetDirectoryName($result) -ne $Folder.TrimEnd('\')) { throw 'Unexpected output path.' }
    return $result
}
$roles=@('project','resources')
if ($Mode -eq 'Windows') { $roles=@('windows') }
if ($Mode -eq 'All') { $roles=@('project','resources','windows') }
$archives=@($manifest.archives | Where-Object { $roles -contains $_.role })
$completed=0
$totalParts=0
foreach ($archive in $archives) { $totalParts+=$archive.parts.Count }
foreach ($archive in $archives) {
    $zipPath=SafeChild $OutputDirectory $archive.name
    if (FileMatches $zipPath $archive.bytes $archive.sha256) {
        Write-Host ('ZIP already verified: '+$archive.name)
        $completed+=$archive.parts.Count
        continue
    }
    if ([IO.File]::Exists($zipPath)) { throw ('An existing ZIP has a different checksum: '+$zipPath) }
    foreach ($part in $archive.parts) {
        $partPath=SafeChild $PartsDirectory $part.name
        if (-not (FileMatches $partPath $part.bytes $part.sha256)) {
            if ($LocalOnly) { throw ('Missing or corrupt local part: '+$part.name) }
            $temporary=$partPath+'.download'
            $success=$false
            for ($attempt=1;$attempt -le 4;$attempt++) {
                try {
                    Write-Host ('Downloading '+$part.name+' (attempt '+$attempt+')')
                    $oldProgress=$ProgressPreference
                    $ProgressPreference='SilentlyContinue'
                    try { Invoke-WebRequest -Uri ($manifest.baseUrl+$part.name) -OutFile $temporary -UseBasicParsing -TimeoutSec 600 }
                    finally { $ProgressPreference=$oldProgress }
                    if (-not (FileMatches $temporary $part.bytes $part.sha256)) { throw 'Part checksum mismatch.' }
                    if ([IO.File]::Exists($partPath)) { [IO.File]::Delete($partPath) }
                    [IO.File]::Move($temporary,$partPath)
                    $success=$true
                    break
                } catch {
                    if ($attempt -eq 4) { throw }
                    Start-Sleep -Seconds (2*$attempt)
                }
            }
            if (-not $success) { throw 'Download did not finish.' }
        }
        $completed++
        Write-Host ('Verified part '+$completed+'/'+$totalParts)
    }
    Write-Host ('Assembling '+$archive.name)
    $assembling=$zipPath+'.assembling'
    $writer=[IO.File]::Open($assembling,[IO.FileMode]::Create,[IO.FileAccess]::Write)
    try {
        foreach ($part in $archive.parts) {
            $reader=[IO.File]::OpenRead((SafeChild $PartsDirectory $part.name))
            try { $reader.CopyTo($writer,4MB) } finally { $reader.Dispose() }
        }
    } finally { $writer.Dispose() }
    if (-not (FileMatches $assembling $archive.bytes $archive.sha256)) { throw 'Assembled ZIP checksum mismatch.' }
    [IO.File]::Move($assembling,$zipPath)
    Write-Host ('ZIP verified: '+$zipPath)
}
if ($Extract -and -not $AssembleOnly) {
    $destination=Join-Path $OutputDirectory ('Extracted_'+$Mode)
    if ([IO.Directory]::Exists($destination)) {
        Write-Host ('Extraction folder already exists; kept existing files: '+$destination)
        Write-Host 'The verified ZIPs are ready. Extract them into a new folder if needed.'
    } else {
        [IO.Directory]::CreateDirectory($destination) | Out-Null
        foreach ($archive in $archives) {
            Write-Host ('Extracting '+$archive.name)
            Expand-Archive -LiteralPath (SafeChild $OutputDirectory $archive.name) -DestinationPath $destination -Force
        }
        Write-Host ('READY: '+(Join-Path $destination 'Lunar_Terrain_Three_Levels'))
    }
}
Write-Host 'SUCCESS: all selected ZIPs match the published SHA-256 checksums.'
