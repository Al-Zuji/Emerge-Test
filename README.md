# 🛠 Autonomous Buggy – Control & Test Scripts

This repository contains low-level test and control scripts used during the development of an autonomous buggy system.  
The scripts are intended for hardware validation, manual control, and integration testing before higher-level autonomy (ROS 2) is enabled.

The focus is on:
- RS485 (Modbus RTU) communication
- PLC control logic
- Encoder feedback validation
- Steering motor control
- Joystick / keyboard based manual driving

--------------------------------------------------------------------

SYSTEM OVERVIEW

Hardware:
- PLC (Modbus RTU over RS485)
- Wheel encoders (Modbus RTU)
- Steering motor controller (RS232 / USB-Serial)
- Game controller or keyboard
- Jetson / PC (Linux or Windows)

Communication:
- RS485 → PLC and encoders
- RS232 → Steering motor
- USB → Gamepad / Keyboard

--------------------------------------------------------------------

RECOMMENDED WORKFLOW ORDER

1. ID_scan_rs485.py        → Detect Modbus slave IDs
2. ENC_Buggy_test_01.py   → Verify encoder readings
3. PLC_control_01.py      → Test PLC coil control
4. steering_motor_test.py or AV_Joystick_01.py → Test steering only
5. BBW_control_limit.py   → Full manual driving & monitoring

--------------------------------------------------------------------

1) ID_scan_rs485.py

Purpose:
This script scans RS485 Modbus RTU slave addresses to identify which devices are responding.
It is the first script to run when setting up new wiring, changing USB-RS485 adapters,
or troubleshooting communication issues.

Interfaces:
- RS485 (Modbus RTU)

How it works:
- Iterates through slave IDs (typically 1 to 16)
- Sends a Modbus read request to a test register
- Prints which slave IDs respond successfully

Typical parameters to adjust:
- Serial port (e.g. /dev/ttyUSB1 or COMx)
- Baudrate
- Stop bits
- Timeout value

Expected result:
- Terminal output shows active Modbus slave IDs
- Confirms wiring and Modbus settings are correct

--------------------------------------------------------------------

2) ENC_Buggy_test_01.py

Purpose:
This script reads encoder values from the buggy system, including:
- Left wheel encoder
- Right wheel encoder
- Steering encoder
- BBW encoder (if applicable)

It is used to verify correct encoder mapping, register addresses, and data sign.

Interfaces:
- RS485 (Modbus RTU encoders)

How it works:
- Reads encoder registers using Modbus
- Converts raw 16-bit values into signed integers
- Continuously prints live encoder values

Typical parameters to adjust:
- Serial port (Windows COMx or Linux /dev/ttyUSBx)
- Encoder slave IDs
- Encoder register addresses
- Read interval (sleep time)

Expected result:
- Encoder values change smoothly when wheels or steering move
- Negative and positive directions behave correctly

--------------------------------------------------------------------

3) BBW_control_limit.py

Purpose:
This is the main manual control script.
It integrates joystick input with:
- PLC control (forward, reverse, enable, stop)
- Speed control via Modbus register writes
- Steering control via serial communication
- Encoder feedback monitoring

Interfaces:
- RS485 → PLC and encoders
- RS232 → Steering motor controller
- USB → Game controller

How it works:
- Joystick buttons control PLC state (enable, forward, reverse, stop)
- Left joystick controls speed (mapped to a Modbus holding register)
- Right joystick controls steering (single-byte serial command)
- Encoders are read continuously for monitoring
- Edge-trigger logic prevents repeated command spamming

Safety logic:
A defined STOP sequence is always used:
STOP_ON → ENABLE_OFF → STOP_OFF

Typical parameters to adjust:
- Serial ports for PLC, encoders, and steering
- Speed scaling limits
- Joystick deadzones
- Steering center value and speed
- PLC coil addresses and register addresses

Expected result:
- Stable manual driving
- Predictable steering and speed control
- Live encoder feedback during operation

--------------------------------------------------------------------

4) steering_motor_test.py

Purpose:
This script provides a simple keyboard-based steering test.
It is used to validate the steering motor and serial communication
without involving PLC logic or joystick input.

Interfaces:
- RS232 / USB-Serial steering controller

How it works:
- Left arrow key steers left
- Right arrow key steers right
- Releasing keys returns steering to center

Typical parameters to adjust:
- Serial port
- Baudrate
- Steering speed
- Center value (usually 127)

Expected result:
- Immediate steering response
- Steering returns to center when keys are released

--------------------------------------------------------------------

5) PLC_control_01.py

Purpose:
This script allows direct manual control of PLC outputs using keyboard input.
It is used to validate PLC coil mapping and system logic independently
from joystick or autonomous control.

Interfaces:
- RS485 (PLC)

How it works:
- User types single-character commands in the terminal
- Commands trigger Modbus coil writes (forward, reverse, stop, signals, horn)
- Includes a safe STOP sequence

Typical commands:
- f → forward
- r → reverse
- s → stop
- l → left signal
- k → right signal
- h → horn
- q → quit

Typical parameters to adjust:
- Serial port
- Baudrate
- Coil addresses
- Timing delays

Expected result:
- PLC responds correctly to each command
- System enters safe STOP state when required

--------------------------------------------------------------------

6) AV_Joystick_01.py

Purpose:
This is a cleaner, Linux-friendly keyboard steering controller.
It improves basic steering tests by minimizing serial traffic
and ensuring the steering always returns to center.

Interfaces:
- RS232 / USB-Serial steering controller

How it works:
- Supports arrow keys and A/D keys
- Tracks key press and release states
- Sends steering commands only when output changes
- Automatically centers steering on release or exit

Typical parameters to adjust:
- Serial port (e.g. /dev/ttyACM3)
- Steering speed
- Center value

Expected result:
- Smooth, jitter-free steering
- Reduced serial traffic
- Reliable centering behavior

--------------------------------------------------------------------

DESIGN PHILOSOPHY

- Test hardware in isolation before integration
- Validate communication first, then control logic
- Always provide a safe STOP state
- Avoid spamming Modbus or serial commands
- Manual control is validated before autonomy is enabled

--------------------------------------------------------------------

NOTES FOR TEAM MEMBERS

- Always verify serial ports using ls /dev/tty* (Linux) or Device Manager (Windows)
- Run ID_scan_rs485.py after any wiring or hardware change
- Do not start with BBW_control_limit.py on new hardware
- Ensure STOP functionality is always accessible during testing
