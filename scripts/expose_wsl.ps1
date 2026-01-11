<#
.SYNOPSIS
Configures Windows networking to expose a WSL 2 service to the local network.

.DESCRIPTION
This script performs the following actions:
1. Identifies the IP address of the WSL 2 instance.
2. Removes any existing port proxy rules for the specified port.
3. Adds a new port proxy rule forwarding traffic from the Windows host (0.0.0.0) to the WSL 2 instance.
4. Adds a Windows Firewall rule to allow inbound traffic on the specified port.

.PARAMETER Port
The port number to expose (default: 8000).

.EXAMPLE
.\expose_wsl.ps1
Exposes port 8000.

.EXAMPLE
.\expose_wsl.ps1 -Port 3000
Exposes port 3000.
#>

param (
    [int]$Port = 8000
)

# Ensure script is run as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script requires Administrator privileges to configure networking."
    Write-Warning "Please right-click PowerShell and select 'Run as Administrator'."
    exit
}

Write-Host "Configuring network access for WSL on Port $Port..." -ForegroundColor Cyan

# 1. Get WSL IP Address
$wslOutput = wsl hostname -i
if (-not $wslOutput) {
    Write-Error "Could not determine WSL IP address. Is WSL running?"
    exit
}
# 'wsl hostname -I' might return multiple IPs; take the first one.
$wslIP = $wslOutput.Split(" ")[0].Trim()
Write-Host "Found WSL IP: $wslIP" -ForegroundColor Green

# 2. Configure Port Forwarding (netsh)
$listenAddress = "0.0.0.0" # Listen on all interfaces

# Remove existing rule to ensure clean state
Write-Host "Removing any existing proxy rules for port $Port..."
netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=$listenAddress | Out-Null

# Add new rule
# netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=127.0.1.1
Write-Host "Forwarding Windows Port $Port -> WSL (${wslIP}:$Port)..."
netsh interface portproxy add v4tov4 listenport=$Port listenaddress=$listenAddress connectport=$Port connectaddress=$wslIP

# 3. Configure Windows Firewall
$firewallRuleName = "WSL-KVM-Service-Port-$Port"

# Remove existing firewall rule if it exists
Remove-NetFirewallRule -DisplayName $firewallRuleName -ErrorAction SilentlyContinue | Out-Null

# Add new firewall rule
Write-Host "Adding Firewall Rule: '$firewallRuleName'..."
New-NetFirewallRule -DisplayName $firewallRuleName `
                    -Direction Inbound `
                    -LocalPort $Port `
                    -Protocol TCP `
                    -Action Allow `
                    -Profile Any `
                    | Out-Null

# 4. Identify Host IP for User Convenience
Write-Host "Identifying primary Windows Host IP..." -ForegroundColor Cyan

$hostIP = "YOUR_WINDOWS_IP"

try {
    # Get active network adapters with a default gateway
    $netConfigs = Get-NetIPConfiguration -ErrorAction Stop | Where-Object { 
        $_.IPv4DefaultGateway -ne $null -and 
        $_.NetAdapter.Status -eq "Up" 
    }
} catch {
    Write-Warning "Unable to automatically determine network configuration. Please check manually."
}

if ($netConfigs) {
    # Map to custom object
    $candidates = $netConfigs | ForEach-Object {
        [PSCustomObject]@{
            InterfaceAlias = $_.InterfaceAlias
            IPAddress      = $_.IPv4Address.IPAddress
            Description    = $_.NetAdapter.InterfaceDescription
            # Identify virtual adapters to deprioritize them
            IsVirtual      = ($_.InterfaceAlias -match "vEthernet|WSL|Default Switch" -or $_.NetAdapter.InterfaceDescription -match "Hyper-V|Virtual")
        }
    }

    # Sort: Physical (IsVirtual=False) first
    $candidates = $candidates | Sort-Object IsVirtual

    if ($candidates.Count -eq 1) {
        $hostIP = $candidates[0].IPAddress
        Write-Host "Selected Adapter: $($candidates[0].InterfaceAlias)"
    }
    elseif ($candidates.Count -gt 1) {
        Write-Host "`nMultiple active network adapters found:" -ForegroundColor Yellow
        Write-Host "Tip: Choose the adapter connected to your router/internet." -ForegroundColor Gray
        
        for ($i = 0; $i -lt $candidates.Count; $i++) {
            $c = $candidates[$i]
            $typeStr = if ($c.IsVirtual) { "[Virtual]" } else { "[Physical]" }
            Write-Host " [$($i+1)] $($c.InterfaceAlias) ($($c.IPAddress))"
            Write-Host "       $($c.Description) $typeStr"
        }

        $selectedIndex = 0
        
        # Check if running interactively to prompt user
        if ([Environment]::UserInteractive) {
            $selection = Read-Host "`nSelect adapter number to use (Default: 1)"
            if (-not [string]::IsNullOrWhiteSpace($selection) -and $selection -match "^\d+$") {
                $parsedIndex = [int]$selection - 1
                if ($parsedIndex -ge 0 -and $parsedIndex -lt $candidates.Count) {
                    $selectedIndex = $parsedIndex
                }
            }
        }
        
        $selected = $candidates[$selectedIndex]
        $hostIP = $selected.IPAddress
        Write-Host "Selected Adapter: $($selected.InterfaceAlias)"
    }
}

Write-Host "`nSUCCESS! Your service is now exposed." -ForegroundColor Green
Write-Host "You can access it from other devices on your LAN using:"
Write-Host "  http://$($hostIP):$Port" -ForegroundColor Cyan
if ($hostIP -eq "YOUR_WINDOWS_IP") {
    Write-Host "(Run 'ipconfig' to verify your actual IP address)" -ForegroundColor Gray
}
