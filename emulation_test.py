import time
import random
import threading
from queue import Queue

# Simulated CAN bus
can_bus = Queue()

# CxD Class (Transmitting Commands)
class CanBusSend:
    PGN_CxD_MachineStatus = 0x0CF21000
    PGN_CxD_MachineCommand = 0x04F21100
    PGN_CxD_MachineInfo = 0x0CF21200

    def __init__(self):
        self.send_count = 0  # maximum 255
        self.rand_seed = 10  # need to be sync between this computer and the target machine
        random.seed(self.rand_seed)

    def broadcast_message(self, pgn, command_or_status, register_index, register_select, register_value):
        # message to broadcast
        can_msg = [pgn, command_or_status, register_index, register_select,
                   register_value[0], register_value[1], register_value[2], register_value[3], self.send_count]
        # do broadcast
        try:
            can_bus.put(can_msg)
            if pgn == self.PGN_CxD_MachineCommand:
                self.send_count = self.send_count + 1 if self.send_count < 255 else 0
            return True
        except Exception as e:
            print(f"Error broadcasting message: {e}")
            return False

    def send_stop(self, emergency=True, confirm=False):
        # CxD -> machine command
        pgn = self.PGN_CxD_MachineCommand
        # emergency stop command, without motion inhibit
        if emergency:
            if not confirm:
                spn_command_emergency_stop = 0x01
            else:
                spn_command_emergency_stop = 0x81
        # controlled stop command, without motion inhibit
        else:
            if not confirm:
                spn_command_emergency_stop = 0x02
            else:
                spn_command_emergency_stop = 0x82
        # does not need register, so all zero
        spn_register_index = 0
        spn_register_select = 0
        # credential (register value bytes)
        credential = random.randrange(2 ** 32 - 1).to_bytes(4, byteorder='big')
        # identifier (use count to identify this command, so we are sure the credential will match)
        return self.broadcast_message(pgn, spn_command_emergency_stop, spn_register_index,
                                      spn_register_select, register_value=credential)

# Machine Emulation Class (Receiving Commands)
class MachineEmulation:
    CAN_ID = 0x18EAFF00  # Example CAN ID, change as required
    PGN_MACHINE_STATUS = 0x0CF21000
    PGN_MACHINE_COMMAND = 0x04F21100
    PGN_MACHINE_REPLY = 0x0CF21200
    NEGOTIATE_NOP = 0x01
    NEGOTIATE_ENQ = 0x02

    def __init__(self):
        pass

    def send_can_message(self, id, data):
        can_bus.put([id] + data)
        print(f"Sent message: {[id] + data}")

    def receive_can_message(self):
        while True:
            if not can_bus.empty():
                msg = can_bus.get()
                print(f"Received message: {msg}")
                return msg

    def handle_negotiation(self):
        # Send NEGOTIATE_NOP to start the negotiation
        self.send_can_message(self.CAN_ID, [self.NEGOTIATE_NOP])
        
        # Wait for a reply
        msg = self.receive_can_message()
        
        if msg[1] == self.NEGOTIATE_NOP:
            print("Negotiation NOP received")
            return True
        else:
            print("Negotiation failed")
            return False

    def handle_initialization(self):
        # Send initialization command to read all registers
        self.send_can_message(self.PGN_MACHINE_STATUS, [0xF0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        
        # Wait for a reply
        msg = self.receive_can_message()
        print("Initialization message received")
        if msg[0] == self.PGN_MACHINE_STATUS and msg[1] == 0xF0:
            print("Initialization reply received")
            return True
        else:
            print("Initialization failed")
            return False

    def handle_operation(self):
        while True:
            msg = self.receive_can_message()
            if msg[0] == self.PGN_MACHINE_COMMAND:
                print("Command received")
                # Handle the command
                reply = self.handle_command(msg)
                self.send_can_message(self.PGN_MACHINE_REPLY, reply)
            elif msg[0] == self.PGN_MACHINE_STATUS:
                print("Status update received")
                # Handle the status update
                reply = self.handle_status_update(msg)
                self.send_can_message(self.PGN_MACHINE_REPLY, reply)
            else:
                print("Unknown message received")

    def handle_command(self, msg):
        # Parse and handle the command message
        command = msg[1]
        if command == 0x01:  # EMERGENCY_STOP
            print("Handling EMERGENCY_STOP")
            return [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        elif command == 0x02:  # CONTROLLED_STOP
            print("Handling CONTROLLED_STOP")
            return [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        elif command == 0x03:  # SLOW_DOWN
            print("Handling SLOW_DOWN")
            return [0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        elif command == 0x04:  # STAND_DOWN
            print("Handling STAND_DOWN")
            return [0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        elif command == 0x05:  # BYPASS_PROPULSION
            print("Handling BYPASS_PROPULSION")
            return [0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        elif command == 0x06:  # APPLY_PROPULSION_SETPOINTS
            print("Handling APPLY_PROPULSION_SETPOINTS")
            return [0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        else:
            print("Unknown command")
            return [0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

    def handle_status_update(self, msg):
        # Parse and handle the status update
        status = msg[1]
        print(f"Handling status update: {status}")
        return [status, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

    def main(self):
        if self.handle_negotiation():
            if self.handle_initialization():
                self.handle_operation()

def cxd_send_stop_command():
    can_bus_sender = CanBusSend()
    while True:
        can_bus_sender.send_stop()
        time.sleep(1)

# Start the machine emulation in a separate thread
machine_emulation = MachineEmulation()
threading.Thread(target=machine_emulation.main).start()

# Start sending stop commands from the CxD
cxd_send_stop_command()
