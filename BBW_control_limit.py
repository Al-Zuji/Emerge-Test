#!/usr/bin/env python3
import serial
from time import sleep
from pynput import keyboard

# ========================= CONFIG =========================
PORT = "/dev/ttyACM3"  # ttyACM3 = steering ttyACM0 = BBW
""    # change to your steering serial device
BAUD = 9600

STEER_CENTER = 127
STEER_SPEED  = 80        # try 40–100; lower = gentler

LEFT_CMD  = max(0,   STEER_CENTER - STEER_SPEED)
RIGHT_CMD = min(255, STEER_CENTER + STEER_SPEED)

# ========================= SERIAL =========================
ser = serial.Serial(
    port=PORT,
    baudrate=BAUD,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=0.1
)

def steer_cmd(val: int):
    """Send 1-byte steering command."""
    val = max(0, min(255, val))
    ser.write(bytes([val]))

# ========================= STATE =========================
key_left_down = False
key_right_down = False
last_sent = None  # avoid spamming identical bytes

def apply_output():
    """Compute desired output from key state and send if changed."""
    global last_sent
    if key_left_down and not key_right_down:
        target = LEFT_CMD
    elif key_right_down and not key_left_down:
        target = RIGHT_CMD
    else:
        target = STEER_CENTER  # none (or both) pressed -> center/stop

    if target != last_sent:
        steer_cmd(target)
        last_sent = target

# ========================= HANDLERS =======================
LEFT_KEYS  = {keyboard.Key.left, keyboard.KeyCode.from_char('a'), keyboard.KeyCode.from_char('A')}
RIGHT_KEYS = {keyboard.Key.right, keyboard.KeyCode.from_char('d'), keyboard.KeyCode.from_char('D')}

def on_press(key):
    global key_left_down, key_right_down
    if key in LEFT_KEYS:
        key_left_down = True
        apply_output()
    elif key in RIGHT_KEYS:
        key_right_down = True
        apply_output()

def on_release(key):
    global key_left_down, key_right_down
    if key in LEFT_KEYS:
        key_left_down = False
        apply_output()
    elif key in RIGHT_KEYS:
        key_right_down = False
        apply_output()

# ========================= MAIN ===========================
def main():
    print("Keyboard steering active:")
    print("  ← / A  = left (hold)")
    print("  → / D  = right (hold)")
    print("  release = center/stop")
    print("Press Ctrl+C to exit.\n")

    # Ensure centered at start
    steer_cmd(STEER_CENTER)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()  # blocks until Ctrl+C or window close
        except KeyboardInterrupt:
            pass
        finally:
            # Fail-safe: center on exit
            steer_cmd(STEER_CENTER)
            ser.close()
            print("\nExited. Steering centered.")

if __name__ == "__main__":
    main()
