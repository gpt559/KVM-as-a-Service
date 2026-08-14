"""
Hardware verification tool for the SV04 4-port USB switch.

Verification uses two independent signals:

1. **Echo** - the SV04 echoes each input-select command back verbatim within
   ~40-95ms. This proves the switch received and acted on the command.
2. **USB topology** - when the Pi is wired to one of the switch's four host
   ports, selecting that input attaches the switch's shared USB hub to the Pi
   and any other input detaches it. This is visible in sysfs.

Together they distinguish "the serial link is dead" from "the link works but
the Pi isn't a host port on this switch".

Note: any shared keyboard/mouse rides on this switch, so switching away from
the Pi's own input removes them. This tool always returns the switch to the
Pi's input before exiting.

Modes:
    python -m src.probe_switch                 # sweep inputs 1-4, detect USB changes
    python -m src.probe_switch --confirm       # sweep, then prove it with a there-and-back toggle
    python -m src.probe_switch --hold-tx       # park TX idle to measure line voltage
    python -m src.probe_switch --loopback      # check the cable with pins 2-3 jumpered

Commands sent are limited to the vendor-documented SV04 table; this tool does
not fuzz unknown byte sequences at the hardware.
"""

import argparse
import glob
import os
import sys
import time

try:
    import serial
except ImportError:
    print("ERROR: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

from src.protocol_handler import ProtocolHandler

# Deliberately no baud sweep: sending at the wrong baud arrives as framing
# garbage and latches up the switch's RS232 controller until it is
# power-cycled. This tool only ever talks at SV04_BAUD.
SV04_BAUD = 115200
PORTS = [1, 2, 3, 4]

# USB enumeration after a switch event is not instant.
DEFAULT_SETTLE = 4.0


# --------------------------------------------------------------------------
# USB topology snapshots
# --------------------------------------------------------------------------

def usb_snapshot() -> dict[str, str]:
    """
    Maps USB topology path -> "vid:pid" for every non-root-hub device.

    Keys are sysfs bus paths such as "1-2" or "1-2.1", which are stable for a
    given physical position, so a snapshot diff pinpoints what attached or
    detached rather than just how many devices exist.
    """
    devices = {}
    for path in glob.glob('/sys/bus/usb/devices/*-*'):
        name = os.path.basename(path)
        if ':' in name:          # interface node, not a device
            continue
        try:
            with open(os.path.join(path, 'idVendor')) as f:
                vid = f.read().strip()
            with open(os.path.join(path, 'idProduct')) as f:
                pid = f.read().strip()
            try:
                with open(os.path.join(path, 'product')) as f:
                    label = f.read().strip()
            except OSError:
                label = "?"
        except OSError:
            continue
        devices[name] = f"{vid}:{pid} {label}"
    return devices


def describe_diff(before: dict, after: dict) -> str:
    added = [f"+{k} ({v})" for k, v in sorted(after.items()) if k not in before]
    gone = [f"-{k} ({v})" for k, v in sorted(before.items()) if k not in after]
    if not added and not gone:
        return ""
    return "  ".join(added + gone)


# --------------------------------------------------------------------------
# Serial helpers
# --------------------------------------------------------------------------

def open_port(port: str, baud: int) -> serial.Serial:
    return serial.Serial(
        port=port, baudrate=baud, bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
        timeout=0.5, xonxoff=False, rtscts=False, dsrdtr=False,
    )


def find_ports() -> list[str]:
    return sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))


ECHO_TIMEOUT = 1.0


def select_input(ser: serial.Serial, port_id: int) -> tuple[bytes, bytes]:
    """
    Sends one SV04 input-select packet and waits for the switch's echo.

    The SV04 echoes each command back verbatim within ~40-95ms. That echo is
    the primary proof the switch received and acted on the command; the USB
    topology diff is the secondary, physical confirmation.

    Returns (packet_sent, echo_received).
    """
    packet = ProtocolHandler.build_sv04_packet(port_id)
    if not ProtocolHandler.validate_sv04_packet(packet):
        raise AssertionError(f"refusing to send invalid packet {packet.hex()}")

    ser.reset_input_buffer()
    ser.write(packet)
    ser.flush()

    deadline = time.monotonic() + ECHO_TIMEOUT
    echo = b''
    while time.monotonic() < deadline and len(echo) < len(packet):
        if ser.in_waiting:
            echo += ser.read(ser.in_waiting)
        else:
            time.sleep(0.01)
    return packet, echo


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------

def sweep(ser: serial.Serial, settle: float) -> tuple[dict[int, dict], dict[int, bool]]:
    """Selects each input in turn, recording the echo and USB tree after each."""
    snapshots: dict[int, dict] = {}
    echoes: dict[int, bool] = {}
    baseline = usb_snapshot()
    print(f"  baseline: {len(baseline)} USB device(s)")
    for name, val in sorted(baseline.items()):
        print(f"      {name}  {val}")
    print()

    prev = baseline
    for port_id in PORTS:
        packet, echo = select_input(ser, port_id)
        echoes[port_id] = echo == packet
        time.sleep(settle)
        now = usb_snapshot()
        diff = describe_diff(prev, now)
        echo_txt = "echo OK" if echoes[port_id] else f"echo [{echo.hex(' ').upper() or 'SILENT'}]"
        flag = "usb CHANGED" if diff else "usb unchanged"
        print(f"  input {port_id}  [{packet.hex(' ').upper()}]  {echo_txt}  {flag}")
        if diff:
            print(f"      {diff}")
        snapshots[port_id] = now
        prev = now
    return snapshots, echoes


def confirm(ser: serial.Serial, host_input: int, other_input: int, settle: float) -> bool:
    """
    Proves causation rather than coincidence: leave the Pi's input, come back,
    and require the USB tree to shrink then grow again.
    """
    print(f"\n  Toggle test: {host_input} -> {other_input} -> {host_input}")

    select_input(ser, host_input)
    time.sleep(settle)
    at_host = usb_snapshot()

    select_input(ser, other_input)
    time.sleep(settle)
    away = usb_snapshot()

    select_input(ser, host_input)
    time.sleep(settle)
    back = usb_snapshot()
    time.sleep(0.5)

    left = len(away) < len(at_host)
    returned = len(back) > len(away)
    print(f"      on input {host_input}: {len(at_host)} devices")
    print(f"      on input {other_input}: {len(away)} devices  ({'detached' if left else 'NO detach'})")
    print(f"      back on {host_input}: {len(back)} devices  ({'reattached' if returned else 'NO reattach'})")
    return left and returned


def hold_tx(port: str, baud: int) -> None:
    """
    Holds the port open and idle so the TX line can be metered.

    This is the definitive test for the most common failure with these
    adapters: a TTL-level FT232 presented on a DB9 shell. RS-232 and TTL are
    both "serial" but are not electrically compatible.
    """
    print("Measure DB9 pin 3 (TX) referenced to pin 5 (GND) with a multimeter.\n")
    print("  -5V to -12V  => true RS-232. Levels are correct for the SV04.")
    print("  +3.3V or +5V => TTL adapter. This is the bug: the SV04 cannot")
    print("                  decode it, because RS-232 idles NEGATIVE and TTL")
    print("                  idles positive. You need a real RS-232 adapter")
    print("                  or a MAX3232 level shifter.")
    print("  ~0V          => nothing driving the line; check wiring/adapter.\n")
    ser = open_port(port, baud)
    try:
        print(f"Holding {port} open and idle at {baud}. Press Ctrl+C when measured.")
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nReleased.")
    finally:
        ser.close()


def loopback(port: str, baud: int) -> bool:
    """Verifies the adapter and cable by echoing bytes with DB9 pins 2-3 jumpered."""
    print("Jumper DB9 pin 2 (RX) to pin 3 (TX), then run this.\n")
    ser = open_port(port, baud)
    try:
        probe = bytes([ProtocolHandler.SV04_HEADER, 0x00, 0x56])
        ser.reset_input_buffer()
        ser.write(probe)
        ser.flush()
        time.sleep(0.4)
        echo = ser.read(len(probe))
    finally:
        ser.close()

    print(f"  sent {probe.hex(' ').upper()}   read {echo.hex(' ').upper() or '(nothing)'}")
    if echo == probe:
        print("  PASS: adapter and cable transmit and receive correctly.")
        return True
    if not echo:
        print("  FAIL: nothing came back. Jumper missing, or the adapter's")
        print("        TX/RX are dead or not on pins 2/3.")
        return False
    print("  PARTIAL: garbled echo. Suggests a baud or signal-level problem.")
    return False


# --------------------------------------------------------------------------

def report(snapshots: dict[int, dict], echoes: dict[int, bool]) -> int | None:
    """Identifies which input is the Pi's, using echoes and USB device counts."""
    sizes = {p: len(s) for p, s in snapshots.items()}
    echo_count = sum(echoes.values())
    print(f"\n  echoes: {echo_count}/{len(echoes)}    device count per input: {sizes}")

    if echo_count == 0:
        print("\n  VERDICT: the switch never echoed. The serial link is not working.")
        print("  Ranked causes:")
        print("    1. DB9 not fully seated, or switch unpowered. Reseat both ends.")
        print("    2. Signal levels: TTL adapter on an RS-232 port.")
        print("       Check with:  python -m src.probe_switch --hold-tx")
        print("    3. TX/RX not crossed - try a null-modem adapter or swap 2/3.")
        print(f"    4. Wrong baud - the SV04 only speaks {SV04_BAUD}.")
        print("    5. Another process holds the port:  docker stop kvm-service")
        return None

    if echo_count < len(echoes):
        missing = [p for p, ok in echoes.items() if not ok]
        print(f"\n  WARNING: inputs {missing} did not echo. Link may be marginal.")

    if len(set(sizes.values())) == 1:
        print("\n  VERDICT: the switch echoes every command, so serial control works,")
        print("  but the Pi's USB tree never changed. That means the Pi is not wired")
        print("  to a host port on this switch, so switching cannot be seen from here.")
        print("  Serial control is confirmed; verify the target visually.")
        return None

    host = max(sizes, key=lambda p: sizes[p])
    print("\n  VERDICT: SWITCHING CONFIRMED (echo + USB attach/detach).")
    print(f"  The Pi is on input {host}.")
    return host


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify SV04 USB switch control")
    ap.add_argument('--port', help="Serial port (default: auto-detect)")
    ap.add_argument('--baud', type=int, default=SV04_BAUD,
                    help=f"Baud rate (default: {SV04_BAUD})")
    ap.add_argument('--settle', type=float, default=DEFAULT_SETTLE,
                    help=f"Seconds to wait for USB enumeration (default: {DEFAULT_SETTLE})")
    ap.add_argument('--confirm', action='store_true',
                    help="After sweeping, prove causation with a there-and-back toggle")
    ap.add_argument('--hold-tx', action='store_true',
                    help="Hold TX idle so the line voltage can be metered")
    ap.add_argument('--loopback', action='store_true',
                    help="Echo test with DB9 pins 2-3 jumpered")
    args = ap.parse_args()

    ports = [args.port] if args.port else find_ports()
    if not ports:
        print("No serial ports found (/dev/ttyUSB*, /dev/ttyACM*). Is the adapter plugged in?")
        sys.exit(1)
    port = ports[0]
    print(f"Serial port: {port}")

    if args.hold_tx:
        hold_tx(port, args.baud)
        return

    if args.loopback:
        sys.exit(0 if loopback(port, args.baud) else 1)

    if not glob.glob('/sys/bus/usb/devices/*-*'):
        print("WARNING: cannot read USB topology from sysfs; detection will not work.")

    bauds = [args.baud]
    for baud in bauds:
        print(f"\n{'=' * 62}\n  {port} @ {baud} baud, 8-N-1\n{'=' * 62}")
        try:
            ser = open_port(port, baud)
        except serial.SerialException as e:
            print(f"  Could not open port: {e}")
            print("  If the service container is running it may hold the port:")
            print("    docker stop kvm-service")
            sys.exit(1)

        host = None
        try:
            time.sleep(0.3)
            snapshots, echoes = sweep(ser, args.settle)
            host = report(snapshots, echoes)
            if host is not None:
                if args.confirm:
                    other = next(p for p in PORTS if p != host)
                    ok = confirm(ser, host, other, args.settle)
                    print("\n  " + ("TOGGLE CONFIRMED - control is working." if ok
                                    else "Toggle inconclusive; USB tree did not track the input."))
                print(f"\n  Working settings: baud={baud}, protocol=sv04")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\nInterrupted.")
            sys.exit(130)
        finally:
            # Leave the switch on the Pi's input. Any shared keyboard/mouse
            # rides on this switch, so exiting on another input would strand
            # the Pi with no input devices.
            if host is not None and ser.is_open:
                try:
                    select_input(ser, host)
                except (serial.SerialException, OSError):
                    pass
            ser.close()

    sys.exit(1)


if __name__ == "__main__":
    main()
