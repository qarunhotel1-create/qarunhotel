# Run as Administrator
# This script creates a venv, installs requirements, opens firewall ports, and starts the scan agent in a new window.
param(
    [int]$httpPort = 5005,
    [int]$ftpPort = 2121
)

$ErrorActionPreference = 'Stop'

Write-Host "Creating virtual environment..."
if (-Not (Test-Path ".\.venv")) {
    python -m venv .venv
}

Write-Host "Activating venv and installing requirements..."
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r .\scan_agent\requirements.txt

Write-Host "Adding firewall rules for ports $httpPort (HTTP) and $ftpPort (FTP)..."
# Create firewall rules
New-NetFirewallRule -DisplayName "ScanAgent HTTP" -Direction Inbound -LocalPort $httpPort -Protocol TCP -Action Allow -Profile Any -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "ScanAgent FTP" -Direction Inbound -LocalPort $ftpPort -Protocol TCP -Action Allow -Profile Any -ErrorAction SilentlyContinue

Write-Host "Starting scan agent in a new PowerShell window..."
$agentPath = Join-Path (Get-Location) 'scan_agent\scan_agent.py'
Start-Process powershell -ArgumentList "-NoExit -Command \". .\\.venv\\Scripts\\Activate.ps1; python '$agentPath'\"" -WindowStyle Normal

Write-Host "Scan agent should now be running. If the agent fails, check scan_agent\scan_agent.log for details."
