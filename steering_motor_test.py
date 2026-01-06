import serial
from pynput import keyboard
from time import sleep

# ============================ SETTINGS ============================
PORT = "COM14"        # RS232 port for steering controller
BAUD = 9600           # Baud rate
STEER_SPEED = 80      # Steering movement speed (127 ± this)
CENTER = 127          # Center position value

# ============================ SERIAL INIT ============================
try:
    ser = serial.Serial(
        port=PORT,
        baudrate=BAUD,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0.1
    )
    print(f"[OK] Connected to {PORT} @ {BAUD}")
except Exception as e:
    raise SystemExit(f"[Serial Error] {e}")

# ============================ STEERING CONTROL ============================
def steer_left():
    """Turn left"""
    cmd = CENTER - STEER_SPEED
    ser.write(bytes([cmd & 0xFF]))
    print(f"← Left ({cmd})")

def steer_right():
    """Turn right"""
    cmd = CENTER + STEER_SPEED
    ser.write(bytes([cmd & 0xFF]))
    print(f"→ Right ({cmd})")

def steer_center():
    """Return to center"""
    ser.write(bytes([CENTER]))
    print("• Center (127)")

# ============================ KEYBOARD EVENTS ============================
def on_press(key):
    try:
        if key == keyboard.Key.left:
            steer_left()
        elif key == keyboard.Key.right:
            steer_right()
    except Exception as e:
        print(f"[Error] {e}")

def on_release(key):
    try:
        if key in (keyboard.Key.left, keyboard.Key.right):
            steer_center()
        elif key == keyboard.Key.esc:
            print("[Exit] ESC pressed")
            steer_center()
            return False  # Stop listener
    except Exception as e:
        print(f"[Error] {e}")

# ============================ MAIN LOOP ============================
print("Use ← and → to steer. Press ESC to exit.\n")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

# ============================ CLEANUP ============================
ser.close()
print("Serial port closed.")
