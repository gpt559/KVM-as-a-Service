// Constants
const API_BASE = '/api/v1';
const POLLING_INTERVAL = 5000; // 5 seconds
const PORT_COUNT = 4;           // SV04 is a 4-port switch; adjust here if hardware changes

// DOM Elements
const apiStatusDot = document.getElementById('api-status-dot');
const hwStatusDot = document.getElementById('hw-status-dot');
const statusMessage = document.getElementById('status-message');
const serialPortEl = document.getElementById('serial-port');
const baudRateEl = document.getElementById('baud-rate');
const inputGrid = document.getElementById('input-grid');
const toast = document.getElementById('toast');

// State
let isConnected = false;
let pendingSwitch = null; // port number currently awaiting hardware echo, or null

// Build the input-selection grid so PORT_COUNT is the single source of truth.
function buildInputGrid() {
    for (let i = 1; i <= PORT_COUNT; i++) {
        const div = document.createElement('div');
        div.className = 'input-option';

        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'usb-port';
        radio.id = `port-${i}`;
        radio.value = String(i);
        radio.addEventListener('change', (e) => {
            if (e.target.checked) switchPort(i);
        });

        const label = document.createElement('label');
        label.htmlFor = `port-${i}`;
        label.textContent = `Input ${i}`;

        div.appendChild(radio);
        div.appendChild(label);
        inputGrid.appendChild(div);
    }
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    buildInputGrid();
    checkStatus();
    setInterval(checkStatus, POLLING_INTERVAL);
});

/**
 * Poll the API for hardware status and sync UI state.
 */
async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        if (!response.ok) throw new Error('API Error');

        const data = await response.json();

        updateStatusDot(apiStatusDot, true);
        isConnected = true;

        const isHardwareOk = data.status === 'healthy';
        updateStatusDot(hwStatusDot, isHardwareOk);

        // Sync the selected radio from confirmed hardware state.
        // active_port is null until a switch has been echo-confirmed since startup —
        // treat null as "unknown" rather than rendering it as input 0 or an error.
        if (data.active_port != null) {
            const portRadio = document.getElementById(`port-${data.active_port}`);
            if (portRadio && !portRadio.checked) {
                portRadio.checked = true;
            }
        } else {
            // No switch confirmed yet — clear any stale selection
            document.querySelectorAll('input[name="usb-port"]').forEach(r => { r.checked = false; });
        }

        // Reflect connection details read-only. These come from env vars via the backend;
        // we never let the UI write them back (wrong baud wedges the hardware).
        if (data.port)     serialPortEl.textContent = data.port;
        if (data.baudrate) baudRateEl.textContent = data.baudrate;

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
 * Send a switch command and wait for hardware echo confirmation.
 *
 * The SV04 echoes each command within ~40-95ms; the backend holds the request open
 * until it hears the echo, so a 200 is genuine hardware confirmation.
 * A 503 means no echo within the timeout — the RS-232 controller has likely latched up
 * and needs a power cycle. The detail field already carries that guidance; surface it as-is.
 *
 * @param {number} portId
 */
async function switchPort(portId) {
    if (!isConnected) return;

    pendingSwitch = portId;
    enableControls(false); // disable all inputs while in flight
    setPendingVisual(portId, true);

    try {
        const response = await fetch(`${API_BASE}/switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port: portId })
        });

        if (!response.ok) {
            const errorData = await response.json();
            const msg = errorData.detail || 'Switch failed';
            // Give the user extra time to read the recovery instructions on a hardware failure
            const isHardwareFailure = response.status === 503;
            showToast(msg, true, isHardwareFailure ? 8000 : 3000);
            // Uncheck the optimistically-selected radio; next poll restores ground truth
            revertPortSelection(portId);
        } else {
            const result = await response.json();
            showToast(result.message || `Switched to Input ${portId}`);
        }

    } catch (error) {
        console.error('Switch failed:', error);
        showToast(`Error: ${error.message}`, true);
        revertPortSelection(portId);
    } finally {
        setPendingVisual(portId, false);
        pendingSwitch = null;
        enableControls(isConnected);
    }
}

// Uncheck a radio after a failed switch; the next status poll will re-sync to hardware state.
function revertPortSelection(portId) {
    const radio = document.getElementById(`port-${portId}`);
    if (radio) radio.checked = false;
}

// Show a loading indicator on the label while its switch command is in flight.
function setPendingVisual(portId, pending) {
    const label = document.querySelector(`label[for="port-${portId}"]`);
    if (!label) return;
    // aria-busy triggers Pico's built-in spinner and our CSS opacity/cursor rule
    if (pending) {
        label.setAttribute('aria-busy', 'true');
    } else {
        label.removeAttribute('aria-busy');
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
    // Do not re-enable while a switch is still awaiting echo confirmation
    if (enabled && pendingSwitch !== null) return;
    document.querySelectorAll('input[name="usb-port"]').forEach(r => { r.disabled = !enabled; });
}

let toastTimer = null;

/**
 * @param {string}  message
 * @param {boolean} isError
 * @param {number}  duration  ms to show the toast (default 3000; use 8000 for 503 errors
 *                            so the user has time to read power-cycle instructions)
 */
function showToast(message, isError = false, duration = 3000) {
    toast.textContent = message;
    toast.style.display = 'block';
    toast.style.borderLeftColor = isError ? '#e74c3c' : '#2ecc71';

    // Reset the clock each time a new message arrives
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.style.display = 'none';
        toastTimer = null;
    }, duration);
}
