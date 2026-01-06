from pymodbus.client.sync import ModbusSerialClient

client = ModbusSerialClient(
    method="rtu",
    port="/dev/ttyUSB1",
    baudrate=38400,
    bytesize=8,
    parity='N',
    stopbits=2,
    timeout=0.5
)

if client.connect():
    print("Connected. Scanning addresses...")
    for addr in range(1, 17):  # Scan 1–16
        rr = client.read_input_registers(1003, 1, unit=addr)
        if not rr.isError():
            print(f"✅ Device found at address {addr}, value={rr.registers[0]}")
        else:
            print(f"❌ No response from address {addr}")
    client.close()
else:
    print("Connection failed.")
