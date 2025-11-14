# Check if Visual Studio Code is installed
if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Visual Studio Code..."
    $vsCodeInstaller = "https://aka.ms/win32-x64-user-stable"
    Invoke-WebRequest -Uri $vsCodeInstaller -OutFile "$env:TEMP\VSCodeSetup.exe"
    Start-Process "$env:TEMP\VSCodeSetup.exe" -ArgumentList "/silent" -Wait
    Remove-Item "$env:TEMP\VSCodeSetup.exe"
}
else {
    Write-Host "Visual Studio Code is already installed."
}

# Check if Git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Git..."
    $gitInstaller = "https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/Git-2.49.0-64-bit.exe"
    Invoke-WebRequest -Uri $gitInstaller -OutFile "$env:TEMP\GitSetup.exe"
    Start-Process "$env:TEMP\GitSetup.exe" -ArgumentList "/silent" -Wait
    Remove-Item "$env:TEMP\GitSetup.exe"
}
else {
    Write-Host "Git is already installed."
}

# Check if repository is properly checked out
Write-Host "Checking repository status..."
$isGitRepo = Test-Path -Path ".git"
$hasProjectFiles = Test-Path -Path "pyproject.toml"

if (-not $isGitRepo) {
    # No .git folder - not a git repository
    Write-Host ""
    Write-Host "ERROR: Git repository not found!" -ForegroundColor Red
    Write-Host "Current directory: $PWD"
    Write-Host ""
    Write-Host "This script requires the .git folder to be present."
    Write-Host "Please ensure you have extracted the complete zip file including the .git folder."
    Write-Host ""
    Write-Host "Press any key to exit..."
    Read-Host
    exit 1
}

if (-not $hasProjectFiles) {
    # .git exists but project files missing - need to checkout
    Write-Host "Git repository found, but project files are missing."
    Write-Host "Checking out project files from repository..."
    try {
        git reset --hard HEAD
        git checkout main
        Write-Host "Project files checked out successfully."
    }
    catch {
        Write-Host ""
        Write-Host "ERROR: Failed to checkout project files: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Press any key to exit..."
        Read-Host
        exit 1
    }
}

# Verify project files now exist
if (-not (Test-Path -Path "pyproject.toml")) {
    Write-Host ""
    Write-Host "ERROR: Project files still missing after checkout!" -ForegroundColor Red
    Write-Host "The repository may be corrupted or incomplete."
    Write-Host ""
    Write-Host "Press any key to exit..."
    Read-Host
    exit 1
}

# Pull latest changes
Write-Host "Updating repository to latest version..."
try {
    git fetch origin
    git pull origin main
    Write-Host "Repository updated successfully."
}
catch {
    Write-Host "Warning: Failed to pull latest changes: $_" -ForegroundColor Yellow
    Write-Host "Continuing with existing files..."
}

Write-Host "Project files verified successfully."

# Install uv
# Check if uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
}
else {
    Write-Host "uv is already installed."
}

# Run uv sync
Write-Host "Running uv sync..."
uv sync --dev --extra jupyter

# Install .NET 6 Framework
$dotnetVersion = $null
try {
    $dotnetVersion = dotnet --version 2>$null
}
catch {
    # dotnet command not found
}

if (-not $dotnetVersion -or -not ($dotnetVersion -match "^6\.")) {
    Write-Host "Installing .NET 6 Desktop Runtime..."
    $dotnetInstaller = "https://aka.ms/dotnet/6.0/windowsdesktop-runtime-win-x64.exe"
    try {
        Invoke-WebRequest -Uri $dotnetInstaller -OutFile "$env:TEMP\dotnet-6-desktop-runtime.exe"
        Start-Process "$env:TEMP\dotnet-6-desktop-runtime.exe" -ArgumentList "/quiet" -Wait
        Remove-Item "$env:TEMP\dotnet-6-desktop-runtime.exe"
        Write-Host ".NET 6 Desktop Runtime installed successfully."
    }
    catch {
        Write-Host "Failed to download or install .NET 6 Desktop Runtime automatically."
        Write-Host "Please manually install .NET 6 from: https://dotnet.microsoft.com/download/dotnet/6.0"
        Write-Host "Press any key to continue..."
        Read-Host
    }
}
else {
    Write-Host ".NET 6 is already installed (version: $dotnetVersion)."
}

# Download and extract RDAConsole
$rdaConsolePath = "./RDAConsole"
if (-not (Test-Path -Path "$rdaConsolePath/RDAConsole.exe")) {
    Write-Host "Downloading RDAConsole from GitHub..."
    try {
        # Get the latest release download URL
        $apiUrl = "https://api.github.com/repos/anno-mods/RdaConsole/releases/latest"
        $release = Invoke-RestMethod -Uri $apiUrl
        $downloadUrl = $release.assets | Where-Object { $_.name -like "*.zip" } | Select-Object -First 1 | ForEach-Object { $_.browser_download_url }

        if (-not $downloadUrl) {
            throw "No zip asset found in latest release"
        }

        # Download and extract
        $zipPath = "$env:TEMP\RDAConsole.zip"
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath

        # Create RDAConsole directory if it doesn't exist
        if (-not (Test-Path -Path $rdaConsolePath)) {
            New-Item -ItemType Directory -Path $rdaConsolePath -Force
        }

        # Extract the zip directly to RDAConsole folder (flattening any subdirectories)
        $tempExtractPath = "$env:TEMP\RDAConsole_temp"
        Expand-Archive -Path $zipPath -DestinationPath $tempExtractPath -Force

        # Move all files from any subdirectories to the target directory
        Get-ChildItem -Path $tempExtractPath -Recurse -File | ForEach-Object {
            Move-Item $_.FullName -Destination $rdaConsolePath -Force
        }

        # Clean up temporary directories
        Remove-Item $zipPath -Force
        Remove-Item $tempExtractPath -Recurse -Force

        Write-Host "RDAConsole downloaded and extracted successfully."
    }
    catch {
        Write-Host "Failed to download RDAConsole automatically: $_"
        Write-Host "Please manually download RDAConsole from: https://github.com/anno-mods/RdaConsole/releases/latest"
        Write-Host "Extract it to the 'RDAConsole' folder in the repository root."
        Write-Host "Press any key to continue..."
        Read-Host
    }
}
else {
    Write-Host "RDAConsole is already downloaded."
}

# Test RDAConsole execution
Write-Host "Testing RDAConsole.exe..."
try {
    $rdaConsoleExe = "$rdaConsolePath/RDAConsole.exe"
    if (Test-Path -Path $rdaConsoleExe) {
        $result = & $rdaConsoleExe 2>&1
        if ($LASTEXITCODE -eq 0 -or $result -match "RDAConsole|Usage|Help") {
            Write-Host "RDAConsole.exe is working correctly."
        }
        else {
            throw "RDAConsole.exe execution failed"
        }
    }
    else {
        throw "RDAConsole.exe not found at $rdaConsoleExe"
    }
}
catch {
    Write-Host "RDAConsole.exe test failed: $_"
    Write-Host ""
    Write-Host "Please ensure:"
    Write-Host "1. .NET 6 Framework is installed"
    Write-Host "2. RDAConsole is properly downloaded to ./RDAConsole/"
    Write-Host "3. RDAConsole.exe exists and is executable"
    Write-Host ""
    Write-Host "Manual steps:"
    Write-Host "1. Download .NET 6 from: https://dotnet.microsoft.com/download/dotnet/6.0"
    Write-Host "2. Download RDAConsole from: https://github.com/anno-mods/RdaConsole/releases/latest"
    Write-Host "3. Extract RDAConsole.zip to ./RDAConsole/ folder"
    Write-Host ""
    Write-Host "Press any key to continue..."
    Read-Host
}

# Install ImageMagick for Python Wand
$magickHome = $env:MAGICK_HOME
if (-not $magickHome -or -not (Test-Path "$magickHome\magick.exe")) {
    Write-Host "Installing ImageMagick for Python Wand support..."
    try {
        # Get the latest Q8 build from ImageMagick binaries
        Write-Host "Fetching latest ImageMagick Q8 build..."
        $binariesPage = Invoke-WebRequest -Uri "https://imagemagick.org/archive/binaries/" -UseBasicParsing

        # Find all Q8 x64 dll.exe files and get the latest version
        $q8Files = $binariesPage.Links | Where-Object {
            $_.href -match "ImageMagick-.*-Q8-x64-dll\.exe$"
        } | Select-Object -ExpandProperty href | Sort-Object -Descending

        if (-not $q8Files -or $q8Files.Count -eq 0) {
            throw "No Q8 build found on binaries page"
        }

        $latestQ8 = $q8Files[0]
        $magickInstaller = "https://imagemagick.org/archive/binaries/$latestQ8"
        $installerPath = "$env:TEMP\ImageMagick-installer.exe"

        Write-Host "Downloading ImageMagick Q8 ($latestQ8)..."
        Invoke-WebRequest -Uri $magickInstaller -OutFile $installerPath

        Write-Host "Installing ImageMagick..."
        Start-Process $installerPath -ArgumentList "/SILENT" -Wait
        Remove-Item $installerPath

        # Find ImageMagick installation directory
        # Search for any ImageMagick installation with Q8 in the name
        $magickInstallPath = $null
        $searchPaths = Get-ChildItem -Path "C:\Program Files" -Filter "ImageMagick*" -Directory -ErrorAction SilentlyContinue

        # Prioritize Q8 installations
        foreach ($dir in $searchPaths) {
            if (Test-Path "$($dir.FullName)\magick.exe") {
                if ($dir.Name -match "-Q8-") {
                    $magickInstallPath = $dir.FullName
                    break
                }
                elseif (-not $magickInstallPath) {
                    # Fallback to any ImageMagick installation
                    $magickInstallPath = $dir.FullName
                }
            }
        }

        if ($magickInstallPath) {
            # Set MAGICK_HOME environment variable permanently
            # Try Machine level first, fall back to User level if no admin rights
            try {
                [Environment]::SetEnvironmentVariable("MAGICK_HOME", $magickInstallPath, "Machine")
                Write-Host "ImageMagick installed successfully at: $magickInstallPath"
                Write-Host "MAGICK_HOME environment variable set at Machine level."
            }
            catch {
                # Fall back to User level if Machine level requires admin
                try {
                    [Environment]::SetEnvironmentVariable("MAGICK_HOME", $magickInstallPath, "User")
                    Write-Host "ImageMagick installed successfully at: $magickInstallPath"
                    Write-Host "MAGICK_HOME environment variable set at User level."
                    Write-Host "Note: Run as Administrator to set system-wide environment variable." -ForegroundColor Yellow
                }
                catch {
                    Write-Host "Warning: Failed to set MAGICK_HOME environment variable: $_" -ForegroundColor Yellow
                    Write-Host "You may need to set it manually to: $magickInstallPath"
                }
            }

            # Set for current session
            $env:MAGICK_HOME = $magickInstallPath
        }
        else {
            throw "ImageMagick installation not found"
        }

    }
    catch {
        Write-Host "Failed to install ImageMagick automatically: $_"
        Write-Host "Please manually install ImageMagick:"
        Write-Host "1. Download Q8 build from: https://imagemagick.org/archive/binaries/"
        Write-Host "   Look for: ImageMagick-*-Q8-x64-dll.exe"
        Write-Host "2. During installation, check all checkboxes (except Perl related)"
        Write-Host "3. Set MAGICK_HOME environment variable to installation path"
        Write-Host "   (e.g., C:\Program Files\ImageMagick-7.1.1-Q8-x64)"
        Write-Host "Press any key to continue..."
        Read-Host
    }
}
else {
    Write-Host "ImageMagick is already installed at: $magickHome"
}

# Test ImageMagick installation
Write-Host "Testing ImageMagick installation..."
try {
    $magickPath = if ($env:MAGICK_HOME) { "$env:MAGICK_HOME\magick.exe" } else { "magick" }
    $result = & $magickPath -version 2>&1
    if ($LASTEXITCODE -eq 0 -and $result -match "ImageMagick") {
        Write-Host "ImageMagick is working correctly."
    }
    else {
        throw "ImageMagick test failed"
    }
}
catch {
    Write-Host "ImageMagick test failed: $_"
    Write-Host ""
    Write-Host "Please ensure ImageMagick is properly installed and MAGICK_HOME is set."
    Write-Host "You may need to restart your terminal or computer for environment variables to take effect."
    Write-Host ""
    Write-Host "Press any key to continue..."
    Read-Host
}

# Copy config.template.json to config.json if it does not exist
if (-not (Test-Path -Path "./config.json")) {
    Write-Host "config.json does not exist. Creating from config.template.json..."
    Copy-Item -Path "./config.template.json" -Destination "./config.json"
    Write-Host ""
    Write-Host "Open config.json and check that the game_path points to the installation directory of your Anno game."
    Write-Host "Press any key to continue..."
    Read-Host
}
else {
    Write-Host "config.json already exists."
}



# Run initial extraction
Write-Host ""
Write-Host "Running initial RDA extraction..."
Write-Host "This will extract required files from your Anno game directory."
Write-Host ""
.\extract.cmd

# Open browsing.ipynb in Visual Studio Code
Write-Host "Opening browsing.ipynb in Visual Studio Code..."
Start-Process -FilePath "code" -ArgumentList "browsing.ipynb"

Write-Host ""
Write-Host "Setup completed! Remember to run extract.cmd whenever there is a game update."
