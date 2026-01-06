import serial
from time import sleep
import pyglet
from typing import List

# ============================ CONTROL PARAMETER ============================
STEER_SPEED = 80
THROTTLE_DEADZONE = 0.25
STEER_DEADZONE = 0.25
SERIAL_TIMEOUT = 0.1

# ============================ RS485 DEVICE ID ============================
# PLC - 1
# LEFT TYRE ENC - 4
# RIGHT TYRE ENC - 2
# STEERING ENC - 3

# ============================ PLC MEMORY (Coils) ============================
# 1 - FORWARD
# 2 - REVERSE
# 8 - STOP
# F - ENABLE

# Sequence reminder:
# - Select FORWARD or REVERSE first
# - Then ENABLE_ON
# - Then you may send SPEED value
# - Before switching FORWARD/REVERSE: STOP_ON -> ENABLE_OFF -> STOP_OFF, then restart sequence

STOP_ON     = bytearray([0x01, 0x05, 0x00, 0x08, 0xFF, 0x00, 0x0D, 0xF8])  # stop operation (coil 8 = ON)
STOP_OFF    = bytearray([0x01, 0x05, 0x00, 0x08, 0x00, 0x00, 0x4C, 0x08])  # clear stop (coil 8 = OFF)
ENABLE_ON   = bytearray([0x01, 0x05, 0x00, 0x0F, 0xFF, 0x00, 0xBC, 0x39])  # enable motor control (coil 15 = ON)
ENABLE_OFF  = bytearray([0x01, 0x05, 0x00, 0x0F, 0x00, 0x00, 0xFD, 0xC9])  # disable motor control (coil 15 = OFF)

# NOTE: These comments were ambiguous in your original. Address 0x0001 = "FORWARD coil", 0x0002 = "REVERSE coil".
FORWARD     = bytearray([0x01, 0x05, 0x00, 0x01, 0xFF, 0x00, 0xDD, 0xFA])  # FORWARD (coil 1 = ON)
REVERSE     = bytearray([0x01, 0x05, 0x00, 0x02, 0xFF, 0x00, 0x2D, 0xFA])  # REVERSE (coil 2 = ON)

LSIGNAL_ON  = bytearray([0x01, 0x05, 0x00, 0x06, 0xFF, 0x00, 0x6C, 0x3B])
LSIGNAL_OFF = bytearray([0x01, 0x05, 0x00, 0x06, 0x00, 0x00, 0x2D, 0xCB])

RSIGNAL_ON  = bytearray([0x01, 0x05, 0x00, 0x07, 0xFF, 0x00, 0x3D, 0xFB])
RSIGNAL_OFF = bytearray([0x01, 0x05, 0x00, 0x07, 0x00, 0x00, 0x7C, 0x0B])

HORN_ON     = bytearray([0x01, 0x05, 0x00, 0x09, 0xFF, 0x00, 0x7C, 0x0B])  # horn ON (coil 9)
HORN_OFF    = bytearray([0x01, 0x05, 0x00, 0x09, 0x00, 0x00, 0x3D, 0xFB])  # horn OFF (coil 9) — fixed

LEFT_ENC    = bytearray([0x04, 0x04, 0x03, 0xE9, 0x00, 0x01, 0xE0, 0x2F])  # read input reg 0x03E9 (1 reg)
RIGHT_ENC   = bytearray([0x02, 0x04, 0x03, 0xE9, 0x00, 0x01, 0xE0, 0x49])
STEER_ENC   = bytearray([0x03, 0x04, 0x03, 0xEB, 0x00, 0x01, 0x40, 0x58])

# ============================ RS485/RS232 FUNCTIONS ============================
class serial_device:
    def __init__(self, PORT, BAUD) -> None:
        try:
            self.client = serial.Serial(
                port=PORT,
                baudrate=BAUD,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=SERIAL_TIMEOUT
            )
        except Exception as e:
            raise SystemExit(f"[Serial Init Error] {PORT} @ {BAUD}: {e}")

    def request(self, req: bytearray) -> int:
        """Send a Modbus request and parse a single 16-bit register (big-endian) from bytes [3:5]."""
        try:
            self.client.write(req)
            resp = self.client.read(7)  # slave | func | bytecount | hi | lo | CRCLo | CRCHi
            if len(resp) != 7:
                raise IOError(f"Incomplete Modbus response: {resp.hex(' ')}")
            val = int.from_bytes(resp[3:5], "big", signed=True)
            return val
        except Exception as e:
            print(f"[Modbus Request Error] {e}")
            return 0

    def send(self, data: int) -> None:
        """RS232 single-byte send (e.g., for steering controller expecting 1 byte)."""
        try:
            self.client.write(bytes([data & 0xFF]))
        except Exception as e:
            print(f"[RS232 Send Error] {e}")

def add_crc(data: List[int]) -> bytearray:
    """Append Modbus CRC16 (little-endian: low byte then high byte)."""
    data = bytearray(data)
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    # Append low byte then high byte
    data.append(crc & 0xFF)
    data.append((crc >> 8) & 0xFF)
    return data

def build_write_single_register(slave: int, reg_addr: int, value: int) -> bytearray:
    """Modbus function 0x06: write single holding register (big-endian payload)."""
    frame = [slave & 0xFF, 0x06, (reg_addr >> 8) & 0xFF, reg_addr & 0xFF,
             (value >> 8) & 0xFF, value & 0xFF]
    return add_crc(frame)

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def map_range(val, in_min=0.0, in_max=1.0, out_min=0, out_max=1000):
    """Map [in_min, in_max] → [out_min, out_max]."""
    if in_max == in_min:
        return out_min
    t = (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return clamp(int(t), out_min, out_max)

# ====== Ports (adjust as needed) ======
plc_enc  = serial_device("COM9", 38400)   # PLC/encoders on RS485
steering = serial_device("COM19", 9600)   # Steering controller on RS232 (1-byte command)
encoder  = serial_device("COM3", 38400)   # Separate RS485 converter for encoders (if applicable)

# ============== CONTROLLER INIT ==============
manager = pyglet.input.ControllerManager()
controllers = manager.get_controllers()
if not controllers:
    raise SystemExit("[Gamepad] No controllers detected. Plug one in and try again.")
controller = controllers[0]
controller.open()

class EdgeButton:
    def __init__(self):
        self.isPressed = False
        self.isToggle = False  # for on/off features (signals)

    def on_press_send(self, pressed: bool, payload: bytearray, ser: serial_device):
        """Send once on rising edge."""
        if not self.isPressed and pressed:
            ser.client.write(bytearray(payload))
            self.isPressed = True
        elif self.isPressed and not pressed:
            self.isPressed = False

# Buttons
btn_a  = EdgeButton()
btn_b  = EdgeButton()
btn_x  = EdgeButton()
btn_y  = EdgeButton()
btn_lb = EdgeButton()
btn_rb = EdgeButton()

def main():
    i = 0
    isTurning = False  # <-- FIXED: initialize
    try:
        while True:
            pyglet.clock.tick()
            pyglet.app.platform_event_loop.step(0)

            # ================== BUTTONS ==================
            # X(BLUE) = FORWARD
            btn_x.on_press_send(getattr(controller, "x", False), FORWARD, plc_enc)

            # Y(YELLOW) = REVERSE
            btn_y.on_press_send(getattr(controller, "y", False), REVERSE, plc_enc)

            # A(GREEN) = ENABLE
            btn_a.on_press_send(getattr(controller, "a", False), ENABLE_ON, plc_enc)

            # B(RED) = STOP sequence + clear enable (required before gear changes)
            if not btn_b.isPressed and getattr(controller, "b", False):
                btn_b.isPressed = True
                plc_enc.client.write(STOP_ON)
                sleep(0.1)
                plc_enc.client.write(ENABLE_OFF)
                sleep(0.1)
                plc_enc.client.write(STOP_OFF)
            elif btn_b.isPressed and not getattr(controller, "b", False):
                btn_b.isPressed = False

            # LEFT SHOULDER = LEFT SIGNAL toggle
            if not btn_lb.isPressed and getattr(controller, "leftshoulder", False):
                btn_lb.isPressed = True
                if not btn_lb.isToggle:
                    plc_enc.client.write(LSIGNAL_ON)
                    btn_lb.isToggle = True
                else:
                    plc_enc.client.write(LSIGNAL_OFF)
                    btn_lb.isToggle = False
            elif btn_lb.isPressed and not getattr(controller, "leftshoulder", False):
                btn_lb.isPressed = False

            # RIGHT SHOULDER = RIGHT SIGNAL toggle
            if not btn_rb.isPressed and getattr(controller, "rightshoulder", False):
                btn_rb.isPressed = True
                if not btn_rb.isToggle:
                    plc_enc.client.write(RSIGNAL_ON)
                    btn_rb.isToggle = True
                else:
                    plc_enc.client.write(RSIGNAL_OFF)
                    btn_rb.isToggle = False
            elif btn_rb.isPressed and not getattr(controller, "rightshoulder", False):
                btn_rb.isPressed = False

            # ================== LEFT JOYSTICK (speed control) ==================
            ly = getattr(controller, "lefty", 0.0)
            if ly > THROTTLE_DEADZONE:
                # map 0.25..1.0 → 0..1000 (linear)
                norm = (ly - THROTTLE_DEADZONE) / (1.0 - THROTTLE_DEADZONE)
                speed_cmd = map_range(norm, 0.0, 1.0, 0, 1000)
                pkt = build_write_single_register(slave=0x01, reg_addr=0x0008, value=speed_cmd)
                plc_enc.client.write(pkt)
                sleep(0.02)
            else:
                # write 0 speed using proper CRC (not hardcoded)
                pkt0 = build_write_single_register(slave=0x01, reg_addr=0x0008, value=0)
                plc_enc.client.write(pkt0)

            # ================== RIGHT JOYSTICK (steer control) ==================
            rx = getattr(controller, "rightx", 0.0)
            if rx <= -STEER_DEADZONE and not isTurning:
                isTurning = True
                steering.send(127 - STEER_SPEED)
            elif rx >= STEER_DEADZONE and not isTurning:
                isTurning = True
                steering.send(127 + STEER_SPEED)
            elif (-0.35 < rx < 0.35) and isTurning:
                isTurning = False
                steering.send(127)  # center

            # ================== ENCODER READ ==================
            i += 1
            left_pv  = encoder.request(LEFT_ENC)
            right_pv = encoder.request(RIGHT_ENC)
            steer_pv = encoder.request(STEER_ENC)
            print(f"{i}. Steering: {steer_pv}\tLEFT: {left_pv}\tRIGHT: {right_pv}")

    except KeyboardInterrupt:
        print("\n[Exit] Interrupted by user.")
    except Exception as e:
        print(f"\n[Runtime Error] {e}")
    finally:
        try:
            steering.client.close()
            plc_enc.client.close()
            encoder.client.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
