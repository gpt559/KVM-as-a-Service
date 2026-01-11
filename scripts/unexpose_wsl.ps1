<#
.SYNOPSIS
Reverses the network configuration made by expose_wsl.ps1.

.DESCRIPTION
This script performs the following actions:
1. Removes the port proxy rule forwarding traffic from the Windows host to WSL 2.
2. Removes the Windows Firewall rule allowing inbound traffic on the specified port.

.PARAMETER Port
The port number to close (default: 8000).

.EXAMPLE
.\unexpose_wsl.ps1
Closes port 8000.
#>

param (
    [int]$Port = 8000
)

# Ensure script is run as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script requires Administrator privileges to clean up networking."
    Write-Warning "Please right-click PowerShell and select 'Run as Administrator'."
    exit
}

Write-Host "Reverting network access for WSL on Port $Port..." -ForegroundColor Cyan

# 1. Remove Port Forwarding (netsh)
$listenAddress = "0.0.0.0"
Write-Host "Removing proxy rules for port $Port..."
try {
    netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=$listenAddress | Out-Null
    Write-Host "Successfully removed port proxy." -ForegroundColor Green
} catch {
    Write-Warning "Error removing port proxy: $_"
}

# 2. Remove Windows Firewall Rule
$firewallRuleName = "WSL-KVM-Service-Port-$Port"
Write-Host "Removing Firewall Rule: '$firewallRuleName'..."
try {
    $ruleExists = Get-NetFirewallRule -DisplayName $firewallRuleName -ErrorAction SilentlyContinue
    if ($ruleExists) {
        Remove-NetFirewallRule -DisplayName $firewallRuleName -ErrorAction Stop
        Write-Host "Successfully removed firewall rule." -ForegroundColor Green
    } else {
        Write-Host "Firewall rule not found (already removed)." -ForegroundColor Yellow
    }
} catch {
    Write-Warning "Error removing firewall rule: $_"
}

Write-Host "`nSecurity cleanup complete. Port $Port is no longer exposed." -ForegroundColor Green
