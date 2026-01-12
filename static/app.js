// Constants
const API_BASE = '/api/v1';
const POLLING_INTERVAL = 5000; // 5 seconds

// DOM Elements
const apiStatusDot = document.getElementById('api-status-dot');
const hwStatusDot = document.getElementById('hw-status-dot');
const statusMessage = document.getElementById('status-message');
const portRadios = document.querySelectorAll('input[name="kvm-port"]');
const toast = document.getElementById('toast');
const protocolSelect = document.getElementById('protocol-select');
const baudrateSelect = document.getElementById('baudrate-select');
const terminatorSelect = document.getElementById('terminator-select');

// State
let isConnected = false;
let currentConfig = {
    protocol: 'hdc202_x24',
    baudrate: 115200,
    terminator: 'none'
};

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initial check
    checkStatus();
    
    // Start polling
    setInterval(checkStatus, POLLING_INTERVAL);

    // Bind Port Click Events
    portRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                switchPort(parseInt(e.target.value));
            }
        });
    });
});

/**
 * Check API Status
 */
async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        if (!response.ok) throw new Error('API Error');
        
        const data = await response.json();
        
        // Update API Status
        updateStatusDot(apiStatusDot, true);
        isConnected = true;

        // Update Hardware Status
        const isHardwareOk = data.status === 'healthy';
        updateStatusDot(hwStatusDot, isHardwareOk);

        // Update Config UI if changed externally (or initial load)
        if (data.protocol && data.protocol !== currentConfig.protocol) {
            currentConfig.protocol = data.protocol;
            protocolSelect.value = data.protocol;
        }
        if (data.baudrate && data.baudrate !== currentConfig.baudrate) {
            currentConfig.baudrate = data.baudrate;
            baudrateSelect.value = data.baudrate;
        }
        if (data.terminator && data.terminator !== currentConfig.terminator) {
            currentConfig.terminator = data.terminator;
            terminatorSelect.value = data.terminator;
        }

        statusMessage.innerHTML = `<p><small>System: ${data.status}</small></p>`;
        
        enableControls(true);

    } catch (error) {
        console.error('Status check failed:', error);
        updateStatusDot(apiStatusDot, false);
        updateStatusDot(hwStatusDot, false);
        statusMessage.innerHTML = `<p><small style="color:red">Connection Lost</small></p>`;
        isConnected = false;
        enableControls(false);
    }
}

/**
 * Update Configuration
 */
async function updateConfig() {
    // Allow config update even if disconnected, to allow fixing connection params
    // if (!isConnected) return;

    const protocol = protocolSelect.value;
    const baudrate = parseInt(baudrateSelect.value);
    const terminator = terminatorSelect.value;

    // Optimistic update
    currentConfig = { protocol, baudrate, terminator };

    try {
        const response = await fetch(`${API_BASE}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ protocol, baudrate, terminator })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update config');
        }

        const result = await response.json();
        showToast(result.message);

    } catch (error) {
        console.error('Config update failed:', error);
        showToast(`Error: ${error.message}`, true);
        // Could revert UI here if needed, but next poll will fix it
    }
}

/**
 * Switch KVM Port
 * @param {number} portId 
 */
async function switchPort(portId) {
    if (!isConnected) return;

    // Visual feedback immediately (already checked by radio logic, but good to reinforce)
    showToast(`Switching to Port ${portId}...`);

    try {
        const response = await fetch(`${API_BASE}/switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port: portId })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to switch port');
        }

        const result = await response.json();
        showToast(result.message);

    } catch (error) {
        console.error('Switch failed:', error);
        showToast(`Error: ${error.message}`, true);
        
        // Optional: Reset radio button selection if failed? 
        // For now, leave as is or user might try again.
    }
}

/**
 * Control Buzzer
 * @param {string} state 'on' or 'off'
 */
async function setBuzzer(state) {
    if (!isConnected) return;

    try {
        const response = await fetch(`${API_BASE}/buzzer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: state })
        });

        if (!response.ok) throw new Error('Failed to set buzzer');
        
        const result = await response.json();
        showToast(result.message);
        
        // Update button styles
        document.getElementById('btn-buzzer-on').className = state === 'on' ? '' : 'outline';
        document.getElementById('btn-buzzer-off').className = state === 'off' ? '' : 'outline';

    } catch (error) {
        showToast(`Error: ${error.message}`, true);
    }
}

/**
 * Run Query
 */
async function runQuery() {
    if (!isConnected) return;
    const command = document.getElementById('query-select').value;
    const responseEl = document.getElementById('query-response');
    responseEl.textContent = "Querying...";
    
    try {
        const response = await fetch(`${API_BASE}/query`, {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({ command: command })
        });
        
        if (!response.ok) {
            const err = await response.json();
             throw new Error(err.detail || 'Query failed');
        }
        
        const data = await response.json();
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        responseEl.textContent = `[${timestamp}] ${data.response_hex || 'No Data'}`;
        showToast("Query successful");
        
    } catch (error) {
         responseEl.textContent = `Error: ${error.message}`;
         showToast("Query failed", true);
    }
}

/**
 * Run All Queries (Batch)
 */
async function runAllQueries() {
    if (!isConnected) return;
    
    const resultsContainer = document.getElementById('batch-query-results');
    const logsContainer = document.getElementById('batch-query-logs');
    
    resultsContainer.style.display = 'block';
    logsContainer.innerHTML = 'Running all queries...';
    
    try {
        const response = await fetch(`${API_BASE}/test/queries`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to run batch queries');
        
        const data = await response.json();
        
        let logHtml = '';
        data.logs.forEach(log => {
             const color = log.status === 'success' ? '#2ecc71' : '#e74c3c';
             logHtml += `<div><span style="color:${color}">[${log.status.toUpperCase()}]</span> <strong>${log.action}</strong>: ${log.detail}</div>`;
        });
        
        logsContainer.innerHTML = logHtml;
        showToast("Batch queries completed");
        
    } catch (error) {
        console.error('Batch query failed:', error);
        logsContainer.innerHTML = `<span style="color:red">Error: ${error.message}</span>`;
        showToast("Batch query failed", true);
    }
}

/**
 * Run Diagnostics
 */
async function runDiagnostics() {
    if (!isConnected) return;
    
    const btn = document.getElementById('btn-run-test');
    const logsContainer = document.getElementById('test-logs');
    const details = document.getElementById('details-logs');
    
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    logsContainer.innerHTML = 'Running tests...';
    details.open = true; // Auto open logs
    
    try {
        const response = await fetch(`${API_BASE}/test/permutations`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Test failed to start');
        
        const data = await response.json();
        
        let logHtml = '';
        data.logs.forEach(log => {
            const color = log.status === 'success' ? '#2ecc71' : (log.status === 'skipped' ? '#f1c40f' : '#e74c3c');
            logHtml += `<div><span style="color:${color}">[${log.status.toUpperCase()}]</span> <strong>${log.action}</strong>: ${log.detail}</div>`;
        });
        
        logsContainer.innerHTML = logHtml;
        showToast("Diagnostics completed");
        
    } catch (error) {
        console.error('Diagnostics failed:', error);
        logsContainer.innerHTML = `<span style="color:red">Error: ${error.message}</span>`;
        showToast("Diagnostics failed", true);
    } finally {
        btn.setAttribute('aria-busy', 'false');
        btn.disabled = false;
    }
}

// Helpers

function updateStatusDot(element, isOnline) {
    if (isOnline) {
        element.classList.add('status-online');
        element.classList.remove('status-offline');
    } else {
        element.classList.add('status-offline');
        element.classList.remove('status-online');
    }
}

function enableControls(enabled) {
    portRadios.forEach(r => r.disabled = !enabled);
    document.getElementById('btn-buzzer-on').disabled = !enabled;
    document.getElementById('btn-buzzer-off').disabled = !enabled;
    // protocolSelect.disabled = !enabled;
    // baudrateSelect.disabled = !enabled;
    // terminatorSelect.disabled = !enabled;
}

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.style.display = 'block';
    toast.style.borderLeftColor = isError ? '#e74c3c' : '#2ecc71';
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}
