# Deployment Instructions

## Prerequisites

*   **Hardware**: Raspberry Pi (3B, 4, or 5 recommended) or any Linux server.
*   **Software**: Docker and Docker Compose **v2** installed (`docker compose`; v1
    `docker-compose` is **not** installed on the production host).
    *   *Raspberry Pi OS*: `curl -sSL https://get.docker.com | sh`
*   **Connection**: USB-to-Serial adapter connected to the switch.

    **Adapter type depends on which switch you have:**

    | Switch | Adapter type | Baud rate |
    |---|---|---|
    | TESmart KVM (hdc202_x24, enterprise, …) | **3.3 V TTL** USB-to-Serial | 9600 |
    | SV04 4-port USB peripheral switch | **RS-232 DB9** USB-to-Serial (e.g. FTDI FT232R) | 115200 |

    > **WARNING (TESmart KVMs only):** The TESmart serial port uses **3.3 V TTL**
    > logic.  Do **not** use a standard RS-232 cable or adapter — it will damage
    > the KVM.  Pinout: Pin 3 = TX, Pin 2 = RX, Pin 1 = GND.

    > **SV04:** This device uses a genuine **RS-232 DB9** port.  Use a standard
    > RS-232 USB-to-Serial adapter (the verified working adapter on the production
    > host is an FTDI FT232R).  A TTL adapter will not work.
    >
    > ⚠️ **Baud rate warning:** The SV04's RS-232 controller latches up if it
    > receives data at any baud rate other than 115200.  Recovery requires a
    > **physical power cycle of the switch** — restarting the container does not
    > help.  Always verify `BAUD_RATE=115200` before applying power.

## Configuration

1.  **Identify Serial Port**:
    On your Raspberry Pi or Linux host, run:
    ```bash
    ls /dev/ttyUSB*
    ```
    Common results: `/dev/ttyUSB0` or `/dev/ttyACM0`.

    The default `SERIAL_PORT=AUTO` scans for the first available `/dev/ttyUSB*`
    or `/dev/ttyACM*` automatically.

2.  **Check `docker-compose.yml`**:
    The current production configuration:

    ```yaml
    # devices:
    #   - /dev/ttyUSB0:/dev/ttyUSB0  # uncomment for explicit mapping
    environment:
      - SERIAL_PORT=AUTO      # AUTO scans /dev/ttyUSB* and /dev/ttyACM*
      - BAUD_RATE=115200      # SV04 requires exactly 115200; see baud warning above
      - PROTOCOL=sv04         # 4-port USB peripheral switch
    ```

    For a TESmart KVM, use `BAUD_RATE=9600` and `PROTOCOL=hdc202_x24` (or the
    appropriate protocol for your model).

    *Note: The default configuration uses `privileged: true` to access hardware.
    For better security, uncomment the `devices` section and map the specific port.*

## Build and Run

1.  **Build the Image**:
    ```bash
    docker compose build
    ```

2.  **Run the Container**:
    ```bash
    docker compose up -d
    ```
    The `-d` flag runs the container in detached mode (background).

3.  **Verify Status**:
    Check if the container is running:
    ```bash
    docker ps
    ```
    View logs:
    ```bash
    docker compose logs -f
    ```

## Usage

Once running, the API will be available at `http://localhost:8000`.

*   **Check Status**: `GET /api/v1/status`
*   **Switch Port**: `POST /api/v1/switch` (JSON: `{"port": 1}`)
*   **Control Buzzer**: `POST /api/v1/buzzer` (JSON: `{"state": "on"}`)
    *   Note: the field is `state`, not `action`.
    *   Buzzer control is **not supported on the SV04** — it returns HTTP 501.

## Unattended Boot (Production)

The production host already survives reboots via two layers:

1.  **`restart: always`** in `docker-compose.yml` — Docker restarts the container
    if it exits unexpectedly (including after a Docker daemon restart at boot).
2.  **`docker.service` is enabled** — the Docker daemon starts automatically at boot.

Together these mean the service recovers from power outages without any extra
configuration.  However the systemd units in `deploy/` provide belt-and-braces
coverage for two gaps that `restart: always` cannot handle on its own:

*   Re-applying changes to `docker-compose.yml` after a reboot (Docker keeps
    running the old container config until the stack is explicitly brought up).
*   Recovering a container that was **manually stopped**, e.g. after running
    `probe_switch.py` (which requires `docker stop kvm-service` to free
    `/dev/ttyUSB0`).

### Installing the systemd units

```bash
# Copy unit files
sudo cp deploy/kvm-service.service      /etc/systemd/system/
sudo cp deploy/kvm-healthcheck.service  /etc/systemd/system/
sudo cp deploy/kvm-healthcheck.timer    /etc/systemd/system/
sudo cp deploy/health-watchdog.sh       /usr/local/bin/kvm-health-watchdog.sh
sudo chmod +x /usr/local/bin/kvm-health-watchdog.sh

# Reload systemd and enable
sudo systemctl daemon-reload
sudo systemctl enable --now kvm-service.service
sudo systemctl enable --now kvm-healthcheck.timer
```

> **Note:** If you copy `health-watchdog.sh` to a different path, update
> `ExecStart=` in `kvm-healthcheck.service` to match.  Or leave the script in
> the repo directory and skip the copy — either works as long as the path in
> the unit file is correct.

### Verifying the units

```bash
# Boot unit
systemctl status kvm-service.service

# Watchdog timer (shows next trigger time)
systemctl status kvm-healthcheck.timer

# Watchdog run history and output
journalctl -u kvm-healthcheck
```

### How the health watchdog works

`kvm-healthcheck.timer` fires `kvm-healthcheck.service` every **5 minutes**.
The script (`deploy/health-watchdog.sh`) reads container health via
`docker inspect` and only restarts if the container has been **unhealthy for
3 consecutive checks** (~15 minutes) **and** no restart has occurred in the
last hour.

This conservative design is intentional: the two most common hardware faults
(latched RS-232 controller, unplugged adapter) cannot be fixed by restarting
the container.  Aggressive restarts would churn forever and achieve nothing.
Watchdog history is logged to the journal (`journalctl -u kvm-healthcheck`).

## Recovering a Wedged Switch

If `POST /api/v1/switch` returns HTTP 503 with a message like
`"did not acknowledge"`, the SV04's RS-232 controller has latched up.

**Restarting the container will not fix this.**

The only recovery is a **physical power cycle of the switch** (unplug power,
wait a few seconds, plug back in).  After the switch restarts, the container
will reconnect automatically.

## Updates

To deploy a new version:

1.  Pull the latest code.
2.  Rebuild: `docker compose build`
3.  Restart: `docker compose up -d`
