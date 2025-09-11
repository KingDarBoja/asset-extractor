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

# Pull the repository of the current directory
Write-Host "Pulling the repository..."
git fetch origin
git pull origin main

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
} catch {
    # dotnet command not found
}

if (-not $dotnetVersion -or -not ($dotnetVersion -match "^6\.")) {
    Write-Host "Installing .NET 6 Framework..."
    $dotnetInstaller = "https://download.microsoft.com/download/6/a/b/6ab8a03f-c4a0-4c5e-b9d5-4c4f3c4e6f0e/dotnet-sdk-6.0.427-win-x64.exe"
    try {
        Invoke-WebRequest -Uri $dotnetInstaller -OutFile "$env:TEMP\dotnet-sdk-6.0.exe"
        Start-Process "$env:TEMP\dotnet-sdk-6.0.exe" -ArgumentList "/quiet" -Wait
        Remove-Item "$env:TEMP\dotnet-sdk-6.0.exe"
        Write-Host ".NET 6 Framework installed successfully."
    } catch {
        Write-Host "Failed to download or install .NET 6 Framework automatically."
        Write-Host "Please manually install .NET 6 from: https://dotnet.microsoft.com/download/dotnet/6.0"
        Write-Host "Press any key to continue..."
        Read-Host
    }
} else {
    Write-Host ".NET 6 Framework is already installed (version: $dotnetVersion)."
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
    } catch {
        Write-Host "Failed to download RDAConsole automatically: $_"
        Write-Host "Please manually download RDAConsole from: https://github.com/anno-mods/RdaConsole/releases/latest"
        Write-Host "Extract it to the 'RDAConsole' folder in the repository root."
        Write-Host "Press any key to continue..."
        Read-Host
    }
} else {
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
        } else {
            throw "RDAConsole.exe execution failed"
        }
    } else {
        throw "RDAConsole.exe not found at $rdaConsoleExe"
    }
} catch {
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
