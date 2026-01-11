# Design: KVM-as-a-Service UI

## Architecture
The UI will be designed as a lightweight Single Page Application (SPA). Although it will be hosted within the same project repository, it will be architecturally decoupled from the backend logic, communicating solely via the REST API.

### Components
1. **Frontend**:
   - `index.html`: The main structure of the dashboard.
   - `style.css`: Custom styles (if needed) on top of a base framework.
   - `app.js`: Logic for API interaction, state management, and UI updates.
   - **Framework**: [Pico.css](https://picocss.com/) (Classless/Minimal CSS) is chosen for immediate, clean aesthetics without complex build steps or heavy dependencies.

2. **Backend Integration**:
   - The FastAPI application (`src/main.py`) will be updated to mount a static file directory (e.g., `static/`) to serve the UI at the root URL (`/`) or a dedicated path (`/ui`).

## User Interface Layout

### Header
- Title: "KVM Control Panel"
- Status Bar:
  - **API Connection**: [Online/Offline] (Indicator Dot)
  - **Hardware Connection**: [Connected/Disconnected] (Indicator Dot)

### Main Content Area

#### Section 1: KVM Status
- Display current port (if retrievable via API/State) - *Note: The current MVP API doesn't seem to support querying the ACTIVE port, only setting it. We will assume stateless operation for now, or track the last sent command in the UI session.*

#### Section 2: Input Control
- **Label**: "Select Active Input"
- **Component**: A grid or list of Radio Buttons (or styled Buttons acting as radios).
- **Options**: Port 1, Port 2, Port 3, Port 4, Port 5, Port 6, Port 7, Port 8.
- **Action**: Clicking an option immediately triggers the `POST /api/v1/switch` endpoint.

#### Section 3: Settings
- **Label**: "Buzzer Control"
- **Component**: Radio group or Toggle Switch.
- **Options**: On / Off.
- **Action**: Changing the selection triggers `POST /api/v1/buzzer`.

### Footer
- Simple footer with version info or logs container for "Last Action" status (e.g., "Successfully switched to Port 2").

## Data Flow

1. **Initialization (`DOMContentLoaded`)**:
   - Start polling interval (e.g., every 5 seconds).
   - Initial check of API status.

2. **Polling (`checkStatus()`)**:
   - `GET /api/v1/status`
   - Update UI Status Bar based on response (`healthy`, `hardware_connected`).

3. **User Action (Switch Input)**:
   - User clicks "Port 3".
   - UI shows "Switching..." spinner or disables controls.
   - `POST /api/v1/switch` with payload `{ "port": 3 }`.
   - On Success: Update "Last Action" log, re-enable controls.
   - On Error: Show error alert, re-enable controls.

4. **User Action (Buzzer)**:
   - User clicks "Off".
   - `POST /api/v1/buzzer` with payload `{ "state": "off" }`.
   - Handle response similar to Switch Input.

## File Structure
```
/workspaces/KVM-as-a-Service
├── ...
├── static/              # New directory for frontend assets
│   ├── index.html
│   ├── app.js
│   └── style.css
├── src/
│   ├── main.py          # Updated to serve static files
│   └── ...
```

## API Interactions (Client-Side)

```javascript
// Example Fetch Wrapper
async function sendCommand(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Request failed');
        return await response.json();
    } catch (error) {
        console.error(error);
        showError(error.message);
    }
}
```
