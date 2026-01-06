#!/usr/bin/env python3
import time
from pymodbus.client.sync import ModbusSerialClient

# ================== SERIAL SETTINGS ==================
PORT = "COM3"
BAUDRATE = 38400
STOPBITS = 2
TIMEOUT = 1

# ================== ENCODER MAP ==================
# (name, slave_id, register_addr)
ENCODERS = [
    ("LEFT",  4, 1001),
    ("RIGHT", 2, 1001),
    ("STEER", 3, 1003),
    ("BBW",   8, 1001),
]

# ================== SETUP CLIENT ==================
client = ModbusSerialClient(
    method="rtu",
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=8,
    parity='N',
    stopbits=STOPBITS,
    timeout=TIMEOUT
)

# ================== HELPER FUNCTIONS ==================
def to_signed(val, bits=16):
    """Convert unsigned to signed integer"""
    if val & (1 << (bits - 1)):
        val -= 1 << bits
    return val

def read_counter(unit_id, reg_addr):
    """Read one encoder register"""
    rr = client.read_input_registers(reg_addr, 1, unit=unit_id)
    if not rr.isError():
        raw = rr.registers[0]
        signed = to_signed(raw, 16)
        return signed
    else:
        return None

# ================== MAIN LOOP ==================
if client.connect():
    print(f"✅ Connected to Modbus network on {PORT}\n")
    print("Reading all encoders (LEFT, RIGHT, STEER, BBW)... Ctrl+C to stop.\n")

    try:
        i = 0
        while True:
            values = {}
            for name, slave_id, reg in ENCODERS:
                val = read_counter(slave_id, reg)
                values[name] = val

            # formatted output
            line = f"{i:05d} | " + " | ".join(
                f"{name:<6}: {val if val is not None else 'ERR':>6}"
                for name, val in values.items()
            )
            print(line, end="\r")

            i += 1
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    finally:
        client.close()
else:
    print("❌ Could not connect to Modbus device.")
