# Exposing the KVM Service to the Local Network

This guide explains how to make the KVM service (running on your PC) accessible to other devices on your home network, such as a phone, tablet, or laptop.

## Overview

By default, services running in development environments (like WSL 2 or Docker) are often only accessible from the machine they are running on (`localhost`). To access them from another device, we need to:

1.  **Find your PC's Local IP Address.**
2.  **Open the Firewall** to allow incoming connections.
3.  **(If using WSL 2)** Forward the port from Windows to WSL.

---

## 🚀 Option 1: Automatic Setup (Windows/WSL Users)

If you are running this project on Windows using WSL 2 (Windows Subsystem for Linux), we have provided a helper script to automate the configuration.

1.  Open **PowerShell** as **Administrator**.
    *   Right-click the Start button or search "PowerShell", then select "Run as administrator".
2.  Navigate to the project `scripts` folder.
    *   *Note: You need to navigate to where this project is stored on your Windows file system.*
3.  Run the script:

    ```powershell
    .\scripts\expose_wsl.ps1
    ```

    *   This script will automatically find your WSL IP, configure port forwarding, and open the Windows Firewall for port `8000`.

---

## 🛠 Option 2: Manual Setup

### 1. Find Your Local IP Address

You need the IP address of the computer running the service.

**Windows:**
1.  Open Command Prompt or PowerShell.
2.  Run `ipconfig`.
3.  Look for **IPv4 Address** under your main connection (Ethernet or Wi-Fi). It usually looks like `192.168.1.x`.

**Linux / Mac:**
1.  Open Terminal.
2.  Run `ifconfig` (or `ip addr` on Linux).
3.  Look for the IP address associated with `eth0` or `wlan0`.

### 2. Configure Firewall

Ensure your computer allows incoming traffic on port **8000**.

**Windows:**
*   Search for "Windows Defender Firewall with Advanced Security".
*   Create a new **Inbound Rule**.
*   Type: **Port** -> **TCP** -> Specific local ports: **8000**.
*   Action: **Allow the connection**.
*   Profile: Check all (Domain, Private, Public).
*   Name: "KVM Service".

**Linux (Ubuntu/UFW):**
```bash
sudo ufw allow 8000/tcp
```

### 3. Verify WSL 2 Forwarding (Windows Only)

If you are on Windows but not using the script, you must manually forward traffic from Windows (the host) to WSL 2.

1.  Get WSL IP: `wsl hostname -I`
2.  Run command (Admin PowerShell):
    ```powershell
    netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=<WSL_IP>
    ```

---

## 📱 Testing the Connection

1.  Ensure the KVM Service is running (`docker-compose up` or `python src/main.py`).
2.  Grab your **Local IP Address** (from Step 1).
3.  On your phone or another device connected to the **same Wi-Fi/Network**:
    *   Open a web browser.
    *   Go to: `http://<YOUR_IP_ADDRESS>:8000`
4.  You should see the KVM Interface.

**Troubleshooting:**
*   **Can't connect?** ensure both devices are on the same network.
*   **Timeout?** Double-check firewall settings.
*   **WSL IP changed?** WSL 2 changes IP addresses on reboot. You may need to re-run the `expose_wsl.ps1` script after restarting your computer.

---

## 🔒 Security: Reverting Changes

If you no longer need to expose the service or want to secure your Windows machine, you should undo the network changes.

### Automated Cleanup

1.  Open **PowerShell** as **Administrator**.
2.  Run the cleanup script:

    ```powershell
    .\scripts\unexpose_wsl.ps1
    ```

    *   This removes the port forwarding rule and deletes the "WSL-KVM-Service-Port-8000" firewall rule.

### Manual Cleanup

1.  **Remove Firewall Rule:**
    *   Open "Windows Defender Firewall with Advanced Security".
    *   Find the Inbound Rule named "WSL-KVM-Service-Port-8000" (or "KVM Service").
    *   Right-click and select **Delete**.
2.  **Remove Port Forwarding:**
    *   Run command (Admin PowerShell):
        ```powershell
        netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
        ```
