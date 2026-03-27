# Adds Windows Firewall rule to allow inbound TCP on port specified (default 5000)
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\add_firewall_rule.ps1 -Port 5000 -Name "QarunHotel HTTP"
param(
    [int]$Port = 5000,
    [string]$Name = "QarunHotel HTTP"
)

$ErrorActionPreference = 'Stop'

Write-Host "Adding Windows Firewall rule for TCP port $Port ..."

# Remove existing rule with same name if exists
$existing = Get-NetFirewallRule -DisplayName $Name -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Existing rule found. Removing..."
    $existing | Remove-NetFirewallRule -Confirm:$false
}

New-NetFirewallRule -DisplayName $Name -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null

Write-Host "Firewall rule added successfully."
