@echo off
setlocal enabledelayedexpansion

:: ---------- CONFIGURATION ----------
set "OUTPUT_FILE=FILE_STRUCTURE.md"
set "EXCLUDE_FOLDERS=.git .agents"
set "MAX_DEPTH=10"
:: -----------------------------------

set "TEMP_SCRIPT=%~dp0temp_tree.ps1"

echo Extracting PowerShell script...
set "in=0"
(for /f "usebackq delims=" %%a in ("%~f0") do (
    set "line=%%a"
    if "!line!"=="::PS_BEGIN" set "in=1"
    if "!line!"=="::PS_END" set "in=0"
    if !in! equ 1 if not "!line!"=="::PS_BEGIN" echo(!line!
)) > "%TEMP_SCRIPT%"

:: Check if extraction succeeded
for %%A in ("%TEMP_SCRIPT%") do if %%~zA equ 0 (
    echo ERROR: Temporary script is empty. Extraction failed.
    pause
    exit /b 1
)

echo Running PowerShell...
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_SCRIPT%" -OutputFile "%OUTPUT_FILE%" -ExcludeFolders "%EXCLUDE_FOLDERS%" -MaxDepth %MAX_DEPTH%

:: Check if output file was created
if exist "%OUTPUT_FILE%" (
    for %%A in ("%OUTPUT_FILE%") do if %%~zA gtr 0 (
        echo ✅ Structure saved to %OUTPUT_FILE%
    ) else (
        echo ERROR: Output file is empty. Something went wrong.
    )
) else (
    echo ERROR: Output file not created.
)

del "%TEMP_SCRIPT%"

pause
exit /b

::PS_BEGIN
# PowerShell script – embedded between markers
param(
    [string]$OutputFile = "FILE_STRUCTURE.md",
    [string]$ExcludeFolders = ".git .agents",
    [int]$MaxDepth = 10
)

$rootDir = Get-Location
Write-Host "Processing: $rootDir"

# Build exclusion sets (case‑insensitive)
$excludeFoldersArray = $ExcludeFolders -split ' '
$summaryFolders = @('__pycache__', '.pytest_cache', '.ruff_cache')
$excludeSet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($name in ($excludeFoldersArray + $OutputFile)) { $excludeSet.Add($name) | Out-Null }
$summarySet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($name in $summaryFolders) { $summarySet.Add($name) | Out-Null }

# Human‑readable file size
function Get-FileSize($bytes) {
    if ($bytes -ge 1TB) { "{0:N2} TB" -f ($bytes / 1TB) }
    elseif ($bytes -ge 1GB) { "{0:N2} GB" -f ($bytes / 1GB) }
    elseif ($bytes -ge 1MB) { "{0:N2} MB" -f ($bytes / 1MB) }
    elseif ($bytes -ge 1KB) { "{0:N2} KB" -f ($bytes / 1KB) }
    else { "$bytes B" }
}

# Tree characters as ASCII codes (safe for plain‑text embedding)
$script:dirCount = 0
$script:fileCount = 0
$script:treeLines = @()

function Get-Tree {
    param([string]$path, [string]$indent = "", [int]$depth = 0)
    if ($depth -gt $MaxDepth) { return }

    $items = Get-ChildItem -Path $path -Force | Sort-Object { $_.PSIsContainer }, Name
    $count = $items.Count
    $index = 0
    foreach ($item in $items) {
        $index++
        $isLast = ($index -eq $count)
        $prefix = if ($isLast) { "$([char]0x2514)$([char]0x2500)$([char]0x2500) " } else { "$([char]0x251C)$([char]0x2500)$([char]0x2500) " }
        $linePrefix = if ($isLast) { "    " } else { "$([char]0x2502)   " }

        if ($excludeSet.Contains($item.Name)) { continue }

        if ($item.PSIsContainer -and $summarySet.Contains($item.Name)) {
            $script:treeLines += "$indent$prefix$($item.Name)/ (summary: compiled/pycache)"
            $script:dirCount++
            continue
        }

        $line = "$indent$prefix$($item.Name)"
        if ($item.PSIsContainer) {
            $line += "/"
            $script:treeLines += $line
            $script:dirCount++
            $newIndent = $indent + $linePrefix
            Get-Tree $item.FullName $newIndent ($depth + 1)
        } else {
            $size = Get-FileSize $item.Length
            $line += " ($size)"
            $script:treeLines += $line
            $script:fileCount++
        }
    }
}

# First, traverse the tree to collect lines and counts
Get-Tree $rootDir

# Now build the header with correct counts
$header = @"
# Repository file structure

Generated: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')

A cleaner, hierarchical view of the repository. Directories end with '/'.
Cache folders ($($summaryFolders -join ', ')) are summarised.
Excluded: $($excludeFoldersArray -join ', '), $OutputFile.

## Summary
- Directories: $($script:dirCount)
- Files: $($script:fileCount)

## Tree
"@

# Write header and tree lines
$header | Out-File -Encoding UTF8 $OutputFile
$script:treeLines | Out-File -Append -Encoding UTF8 $OutputFile

Write-Host "Done. Directories: $($script:dirCount), Files: $($script:fileCount)"
::PS_END