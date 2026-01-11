# Requirements: KVM-as-a-Service UI

## Overview
This document outlines the requirements for a web-based User Interface (UI) for the KVM-as-a-Service REST API. The UI will provide a user-friendly way to control the physical KVM switch, view system status, and manage settings without interacting directly with the API endpoints. The design will prioritize simplicity and decoupling, allowing the frontend to be separated from the backend in the future if necessary.

## User Stories

### Dashboard View
**As a** user
**I want** to see a single dashboard with all controls and status indicators
**So that** I can assess the system state and make changes quickly.

### System Status
**As a** user
**I want** to clearly see if the UI is connected to the backend server
**And** if the backend server is successfully connected to the physical KVM hardware
**So that** I know if my commands will be executed.

### Input Selection
**As a** user
**I want** to select the active input source (PC 1-8) using a clear set of radio buttons
**So that** I can switch displays easily with a single click.

### Buzzer Control
**As a** user
**I want** to toggle the KVM buzzer on or off
**So that** I can control the audio feedback of the device.

## Functional Requirements

### Architecture & Tech Stack
- The UI shall be a Single Page Application (SPA) or a simple static HTML/JS page.
- The UI shall interact with the backend exclusively via the defined REST API (`/api/v1/*`).
- The UI should be capable of being hosted independently (e.g., separate web server) or served statically by the backend framework (FastAPI).
- Standard CSS libraries (e.g., Bootstrap, Tailwind, or simple CSS frameworks like Pico.css/MVP.css) should be used for basic styling and responsiveness.

### Status Indicators
- **Server Status**: The UI shall periodically poll the health endpoint (`/api/v1/status`) to determine connectivity.
- **KVM Connection Status**: The UI shall display whether the serial connection to the hardware is active based on the API response.
- Visual indicators (e.g., Green/Red badges or text) shall represent these states.

### Controls
- **Input Switching**: A radio button group (or similar single-selection UI) for Ports 1 through 8.
- **Buzzer Control**: A toggle or pair of radio buttons for "Buzzer On" and "Buzzer Off".

### Error Handling
- **If** an API request fails, **then** the UI shall display a user-friendly error message (e.g., toast notification or alert box).
- **If** the server is unreachable, **then** the UI shall disable control inputs to prevent phantom actions.

## Acceptance Criteria

### Scenario 1: Load Dashboard
**Given** the backend is running
**When** the user opens the UI in a browser
**Then** they see the current connection status of the server and KVM
**And** they see the control options for Input Selection and Buzzer.

### Scenario 2: Switch Input
**Given** the UI is loaded and connected
**When** the user clicks "Port 2"
**Then** a request is sent to `POST /api/v1/switch` with `{ "port": 2 }`
**And** a success message is briefly shown upon completion.

### Scenario 3: Handle Disconnection
**Given** the backend service stops
**When** the UI next polls for status
**Then** the "Server Status" indicator changes to "Disconnected" (or Error)
**And** the controls become disabled or show a warning.
