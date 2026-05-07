#!/usr/bin/env python3
"""Einmal-Test: CP2102N init + ein Bulk-Read der LSU200."""
import struct, time
import usb.core, usb.util

USB_VID, USB_PID = 0x18ef, 0xe02c
EP_OUT, EP_IN    = 0x02, 0x82

# CP2102N control requests
H2I              = 0x41   # bmRequestType: Vendor, Host→Interface
IFC_ENABLE       = 0x00
SET_BAUDRATE     = 0x1E
SET_LINE_CTL     = 0x03

dev = usb.core.find(idVendor=USB_VID, idProduct=USB_PID)
if dev is None:
    print("FEHLER: Gerät nicht gefunden (lsusb prüfen, udev-Regel?)")
    raise SystemExit(1)

print(f"Gerät: {dev}")

try:
    dev.detach_kernel_driver(0)
    print("Kernel-Treiber getrennt")
except usb.core.USBError:
    print("Kein Kernel-Treiber gebunden (ok)")

try:
    dev.set_configuration()
    print("Konfiguration gesetzt")
except usb.core.USBError as e:
    if e.errno == 16:
        print("Konfiguration bereits gesetzt (ok)")
    else:
        raise

usb.util.claim_interface(dev, 0)
print("Interface 0 geclaimed")

# CP2102N: UART enable
ret = dev.ctrl_transfer(H2I, IFC_ENABLE, 0x0001, 0, None, 1000)
print(f"IFC_ENABLE → {ret}")

# CP2102N: Baudrate 19200
ret = dev.ctrl_transfer(H2I, SET_BAUDRATE, 0, 0, struct.pack('<I', 19200), 1000)
print(f"SET_BAUDRATE(19200) → {ret}")

# CP2102N: 8N1
ret = dev.ctrl_transfer(H2I, SET_LINE_CTL, 0x0800, 0, None, 1000)
print(f"SET_LINE_CTL(8N1) → {ret}")

def parse_time(t):
    t = t.strip()
    try:
        if t.isdigit() and len(t) == 9:
            return int(t[0:2])*3600 + int(t[2:4])*60 + int(t[4:6]) + int(t[6:9])/1000.0
        parts = t.replace(",",":").split(":")
        if len(parts) >= 3:
            return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2]) + \
                   (int(parts[3]) if len(parts)>3 else 0)/1000.0
    except Exception:
        pass
    return None

print("\n--- Poll 10×, Interval 0.2 s ---")
for i in range(10):
    dev.write(EP_OUT, b"w", timeout=3000)
    try:
        raw = bytes(dev.read(EP_IN, 64, timeout=3000)).decode("ascii", errors="ignore").strip()
        if raw.startswith("w"):
            raw = raw[1:]
        if ";" in raw:
            state_str, time_str = raw.split(";", 1)
            secs = parse_time(time_str)
            print(f"  [{i+1:2d}] state={state_str!r:4s}  time_str={time_str!r:12s}  → {secs} s")
        else:
            print(f"  [{i+1:2d}] raw={raw!r}")
    except usb.core.USBError as e:
        print(f"  [{i+1:2d}] READ ERROR: {e}")
    time.sleep(0.2)

usb.util.release_interface(dev, 0)
usb.util.dispose_resources(dev)
print("Fertig.")
