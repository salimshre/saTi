@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Copying ALL files to tmp/ (flat)
echo  No folders, just files!
echo ========================================
echo.

REM Get the current directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 1. Delete old tmp folder
if exist tmp (
    echo Removing old tmp folder...
    rmdir /s /q tmp
)

REM 2. Create fresh tmp folder
mkdir tmp

if not exist tmp (
    echo ERROR: Could not create tmp folder!
    pause
    exit /b 1
)

echo Copying all files from: %CD%
echo.

REM 3. Find all files (recursively) and copy them flat to tmp
set "file_count=0"
set "duplicate_count=0"

for /r %%f in (*) do (
    REM Skip the batch file itself and the tmp folder
    echo %%~f | find /i "copy_to_tmp.bat" >nul
    if errorlevel 1 (
        echo %%~f | find /i "\tmp\" >nul
        if errorlevel 1 (
            REM Copy the file to tmp with its original name
            copy "%%f" "tmp\" >nul 2>&1
            if !errorlevel! equ 0 (
                set /a file_count+=1
                echo Copied: %%~nxf
            ) else (
                REM If file already exists, rename with folder name
                set "duplicate_count+=1"
                echo WARNING: Duplicate filename: %%~nxf
                REM Copy with folder name prefix
                for %%p in ("%%~dpf.") do set "folder_name=%%~np"
                copy "%%f" "tmp\!folder_name!_%%~nxf" >nul 2>&1
                echo   Renamed to: !folder_name!_%%~nxf
            )
        )
    )
)

echo.
echo ========================================
echo  Copy complete!
echo  Total files copied: %file_count%
if !duplicate_count! gtr 0 echo  Duplicates renamed: !duplicate_count!
echo ========================================

REM 4. List all files in tmp
echo.
echo Files in tmp:
dir /b tmp

echo.
echo ========================================

REM 5. Open tmp folder
echo Opening tmp folder in Explorer...
start explorer tmp

echo.
echo Done! All files are now in the tmp folder.
pause