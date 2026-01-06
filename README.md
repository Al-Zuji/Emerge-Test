# 🛠 Autonomous Buggy – Control & Test Scripts

This repository contains **low-level test and control scripts** used during the development of an **autonomous buggy system**.

These scripts are intended for:
- Hardware bring-up and validation
- Manual control and safety testing
- Integration testing before higher-level autonomy (ROS 2)

They form the **foundation layer** of the system and must be verified before any autonomous logic is enabled.

====================================================================

SYSTEM OVERVIEW

--------------------------------------------------------------------
Hardware Components
--------------------------------------------------------------------
- PLC (Modbus RTU over RS485)
- Wheel encoders (Modbus RTU)
- Steering motor controller (RS232 / USB-Serial)
- Game controller or keyboard
- Jetson / PC (Linux or Windows)

--------------------------------------------------------------------
Communication Interfaces
--------------------------------------------------------------------
- RS485 → PLC and encoders
- RS232 → Steering motor
- USB   → Gamepad / Keyboard

====================================================================

RECOMMENDED WORKFLOW ORDER

Always follow this sequence when setting up new hardware or debugging:

1. ID_scan_rs485.py
   - Detect Modbus slave IDs on RS485 bus

2. ENC_Buggy_test_01.py
   - Verify encoder data and direction

3. PLC_control_01.py
   - Test PLC coil logic and safety states

4. steering_motor_test.py
   OR
   AV_Joystick_01.py
   - Test steering motor only

5. BBW_control_limit.py
   - Full manual driving and monitoring

====================================================================

1) ID_scan_rs485.py
------------------------------------------------------------

Purpose:
- Scan RS485 Modbus RTU slave addresses
- Identify which devices are responding

Use this script FIRST when:
- New wiring is installed
- USB-RS485 adapter is changed
- Modbus communication is unstable

Interface:
- RS485 (Modbus RTU)

How It Works:
- Iterates through slave IDs (usually 1–16)
- Sends a Modbus read request to a test register
- Prints responding slave IDs

Typical Parameters to Adjust:
- Serial port (e.g. /dev/ttyUSB1 or COMx)
- Baudrate
- Stop bits
- Timeout

Expected Result:
- Active Modbus slave IDs are displayed
- Confirms RS485 wiring and settings are correct

====================================================================

2) ENC_Buggy_test_01.py
------------------------------------------------------------

Purpose:
- Read encoder values from the buggy system:
  - Left wheel
  - Right wheel
  - Steering
  - BBW (if available)

Used to verify:
- Encoder slave ID mapping
- Register addresses
- Data sign and direction

Interface:
- RS485 (Modbus RTU encoders)

How It Works:
- Reads encoder registers continuously
- Converts raw 16-bit values to signed integers
- Prints live encoder values to terminal

Typical Parameters to Adjust:
- Serial port (COMx or /dev/ttyUSBx)
- Encoder slave IDs
- Encoder register addresses
- Read interval (sleep time)

Expected Result:
- Smooth encoder updates
- Correct positive and negative direction

====================================================================

3) BBW_control_limit.py
------------------------------------------------------------

Purpose:
This is the MAIN manual control script.

It integrates:
- PLC control (enable, forward, reverse, stop)
- Speed control via Modbus register writes
- Steering control via serial communication
- Encoder feedback monitoring
- Gamepad input

Interfaces:
- RS485 → PLC and encoders
- RS232 → Steering motor controller
- USB   → Game controller

How It Works:
- Joystick buttons control PLC states
- Left joystick controls vehicle speed
- Right joystick controls steering angle
- Encoder values are read continuously
- Edge-trigger logic prevents command spamming

Safety Logic:
A mandatory stop sequence is enforced:

STOP_ON → ENABLE_OFF → STOP_OFF

Typical Parameters to Adjust:
- Serial ports (PLC / encoders / steering)
- Speed scaling limits
- Joystick deadzones
- Steering center value and speed
- PLC coil and register addresses

Expected Result:
- Stable manual driving
- Predictable steering and speed control
- Live encoder feedback during motion

====================================================================

4) steering_motor_test.py
------------------------------------------------------------

Purpose:
- Simple keyboard-based steering test
- No PLC or joystick dependency

Used to validate:
- Steering motor operation
- Serial communication
- Steering center calibration

Interface:
- RS232 / USB-Serial steering controller

How It Works:
- Left arrow  → steer left
- Right arrow → steer right
- Key release → return to center

Typical Parameters to Adjust:
- Serial port
- Baudrate
- Steering speed
- Center value (usually 127)

Expected Result:
- Immediate steering response
- Automatic return to center

====================================================================

5) PLC_control_01.py
------------------------------------------------------------

Purpose:
- Direct manual control of PLC outputs
- Validate PLC logic independently

Interface:
- RS485 (PLC)

How It Works:
- Single-character terminal commands
- Sends Modbus coil write requests
- Includes a safe STOP sequence

Command List:
- f → forward
- r → reverse
- s → stop
- l → left signal
- k → right signal
- h → horn
- q → quit

Typical Parameters to Adjust:
- Serial port
- Baudrate
- Coil addresses
- Timing delays

Expected Result:
- PLC responds correctly
- System enters safe STOP state when required

====================================================================

6) AV_Joystick_01.py
------------------------------------------------------------

Purpose:
- Clean, Linux-friendly keyboard steering controller
- Improved version of basic steering test

Improvements:
- Reduced serial traffic
- No repeated command spamming
- Guaranteed steering centering

Interface:
- RS232 / USB-Serial steering controller

How It Works:
- Supports arrow keys and A/D keys
- Tracks key press and release states
- Sends steering command only when output changes
- Automatically centers steering on release or exit

Typical Parameters to Adjust:
- Serial port (e.g. /dev/ttyACM3)
- Steering speed
- Center value

Expected Result:
- Smooth, jitter-free steering
- Clean serial communication
- Reliable centering behavior

====================================================================

DESIGN PHILOSOPHY

- Test hardware in isolation before integration
- Validate communication before control logic
- Safety is always the highest priority
- Avoid spamming Modbus or serial commands
- Manual control must be stable before autonomy

====================================================================

NOTES FOR TEAM MEMBERS

- Always verify serial ports using:
  - Linux: ls /dev/tty*
  - Windows: Device Manager
- Run ID_scan_rs485.py after any wiring change
- Do NOT start with BBW_control_limit.py on new hardware
- Ensure STOP functionality is always accessible during testing
