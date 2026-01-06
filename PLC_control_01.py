import serial
from time import sleep

# ============================ SERIAL CONFIG ============================
PORT = "COM18"        # change as needed
BAUD = 38400
TIMEOUT = 0.1

try:
    plc = serial.Serial(
        port=PORT,
        baudrate=BAUD,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=TIMEOUT
    )
    print(f"[OK] Connected to PLC on {PORT} @ {BAUD}")
except Exception as e:
    raise SystemExit(f"[Serial Error] {e}")

# ============================ PREDEFINED COMMANDS ============================
STOP_ON     = bytearray([0x01, 0x05, 0x00, 0x08, 0xFF, 0x00, 0x0D, 0xF8])
STOP_OFF    = bytearray([0x01, 0x05, 0x00, 0x08, 0x00, 0x00, 0x4C, 0x08])
ENABLE_ON   = bytearray([0x01, 0x05, 0x00, 0x0F, 0xFF, 0x00, 0xBC, 0x39])
ENABLE_OFF  = bytearray([0x01, 0x05, 0x00, 0x0F, 0x00, 0x00, 0xFD, 0xC9])
FORWARD     = bytearray([0x01, 0x05, 0x00, 0x01, 0xFF, 0x00, 0xDD, 0xFA])
REVERSE     = bytearray([0x01, 0x05, 0x00, 0x02, 0xFF, 0x00, 0x2D, 0xFA])
LSIGNAL_ON  = bytearray([0x01, 0x05, 0x00, 0x06, 0xFF, 0x00, 0x6C, 0x3B])
LSIGNAL_OFF = bytearray([0x01, 0x05, 0x00, 0x06, 0x00, 0x00, 0x2D, 0xCB])
RSIGNAL_ON  = bytearray([0x01, 0x05, 0x00, 0x07, 0xFF, 0x00, 0x3D, 0xFB])
RSIGNAL_OFF = bytearray([0x01, 0x05, 0x00, 0x07, 0x00, 0x00, 0x7C, 0x0B])
HORN_ON     = bytearray([0x01, 0x05, 0x00, 0x09, 0xFF, 0x00, 0x7C, 0x0B])
HORN_OFF    = bytearray([0x01, 0x05, 0x00, 0x09, 0x00, 0x00, 0x3D, 0xFB])

# ============================ FUNCTIONS ============================
def send(cmd: bytearray, delay=0.05):
    """Send Modbus command to PLC."""
    plc.write(cmd)
    sleep(delay)

def stop_sequence():
    """Safely stop motor and disable control."""
    print("[PLC] Stop sequence...")
    send(STOP_ON)
    sleep(0.1)
    send(ENABLE_OFF)
    sleep(0.1)
    send(STOP_OFF)
    print("[PLC] Motor stopped.")

def forward():
    print("[PLC] Forward mode")
    send(FORWARD)
    send(ENABLE_ON)

def reverse():
    print("[PLC] Reverse mode")
    send(REVERSE)
    send(ENABLE_ON)

def left_signal(on=True):
    send(LSIGNAL_ON if on else LSIGNAL_OFF)
    print(f"[PLC] Left signal {'ON' if on else 'OFF'}")

def right_signal(on=True):
    send(RSIGNAL_ON if on else RSIGNAL_OFF)
    print(f"[PLC] Right signal {'ON' if on else 'OFF'}")

def horn(on=True):
    send(HORN_ON if on else HORN_OFF)
    print(f"[PLC] Horn {'ON' if on else 'OFF'}")

# ============================ MAIN MENU LOOP ============================
def main():
    print("""
==================== PLC CONTROL MENU ====================
[f] Forward
[r] Reverse
[s] Stop
[l] Toggle Left Signal
[k] Toggle Right Signal
[h] Toggle Horn
[q] Quit
==========================================================
    """)
    left_on = False
    right_on = False
    horn_on = False

    try:
        while True:
            cmd = input("Enter command: ").strip().lower()
            if cmd == 'f':
                forward()
            elif cmd == 'r':
                reverse()
            elif cmd == 's':
                stop_sequence()
            elif cmd == 'l':
                left_on = not left_on
                left_signal(left_on)
            elif cmd == 'k':
                right_on = not right_on
                right_signal(right_on)
            elif cmd == 'h':
                horn_on = not horn_on
                horn(horn_on)
            elif cmd == 'q':
                print("[Exit] Closing connection.")
                break
            else:
                print("Invalid input. Try again.")
    except KeyboardInterrupt:
        print("\n[Exit] Interrupted by user.")
    finally:
        plc.close()

if __name__ == "__main__":
    main()
