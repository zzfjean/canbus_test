import time
from machine import Pin, CAN

# Configuration for the CAN interface
CAN_ID = 0x18EAFF00  # Example CAN ID, change as required
BAUD_RATE = 250000

# Initialize the CAN interface
can = CAN(0, baudrate=BAUD_RATE, mode=CAN.NORMAL)

# Define the PGNs
PGN_MACHINE_STATUS = 0xF0
PGN_MACHINE_COMMAND = 0xE0
PGN_MACHINE_REPLY = 0xD0

# Define the negotiation constants
NEGOTIATE_NOP = 0x01
NEGOTIATE_ENQ = 0x02

def send_can_message(id, data):
    can.send(data, id)

def receive_can_message():
    while True:
        if can.any():
            msg = can.recv()
            return msg

def handle_negotiation():
    # Send NEGOTIATE_NOP to start the negotiation
    send_can_message(CAN_ID, bytes([NEGOTIATE_NOP]))
    
    # Wait for a reply
    msg = receive_can_message()
    
    if msg[0] == NEGOTIATE_NOP:
        print("Negotiation NOP received")
        return True
    else:
        print("Negotiation failed")
        return False

def handle_initialization():
    # Send initialization command to read all registers
    send_can_message(CAN_ID, bytes([PGN_MACHINE_STATUS, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
    
    # Wait for a reply
    msg = receive_can_message()
    if msg[0] == PGN_MACHINE_REPLY:
        print("Initialization reply received")
        return True
    else:
        print("Initialization failed")
        return False

def handle_operation():
    while True:
        msg = receive_can_message()
        if msg[0] == PGN_MACHINE_COMMAND:
            print("Command received")
            # Handle the command
            reply = handle_command(msg)
            send_can_message(CAN_ID, reply)
        elif msg[0] == PGN_MACHINE_STATUS:
            print("Status update received")
            # Handle the status update
            reply = handle_status_update(msg)
            send_can_message(CAN_ID, reply)
        else:
            print("Unknown message received")

def handle_command(msg):
    # Parse and handle the command message
    command = msg[1]
    if command == 0x01:  # EMERGENCY_STOP
        print("Handling EMERGENCY_STOP")
        return bytes([PGN_MACHINE_REPLY, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    elif command == 0x02:  # CONTROLLED_STOP
        print("Handling CONTROLLED_STOP")
        return bytes([PGN_MACHINE_REPLY, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    elif command == 0x03:  # SLOW_DOWN
        print("Handling SLOW_DOWN")
        return bytes([PGN_MACHINE_REPLY, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    elif command == 0x04:  # STAND_DOWN
        print("Handling STAND_DOWN")
        return bytes([PGN_MACHINE_REPLY, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    elif command == 0x05:  # BYPASS_PROPULSION
        print("Handling BYPASS_PROPULSION")
        return bytes([PGN_MACHINE_REPLY, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    elif command == 0x06:  # APPLY_PROPULSION_SETPOINTS
        print("Handling APPLY_PROPULSION_SETPOINTS")
        return bytes([PGN_MACHINE_REPLY, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    else:
        print("Unknown command")
        return bytes([PGN_MACHINE_REPLY, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

def handle_status_update(msg):
    # Parse and handle the status update
    status = msg[1]
    print(f"Handling status update: {status}")
    return bytes([PGN_MACHINE_REPLY, status, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

# Main function
def main():
    if handle_negotiation():
        if handle_initialization():
            handle_operation()

if __name__ == "__main__":
    main()
