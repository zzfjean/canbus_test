import can
import time
import random


class CanBusSend(object):
    PGN_CxD_MachineStatus = 0x0CF21000
    PGN_CxD_MachineCommand = 0x04F21100
    PGN_CxD_MachineInfo = 0x0CF21200

    def __init__(self):
        self.bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=500000)
        self.send_count = 0  # maximum 255
        self.rand_seed = 10  # need to be sync between this computer and the target machine
        random.seed(self.rand_seed)

    def broadcast_message(self, pgn, command_or_status, register_index, register_select, register_value):
        # message to broadcast
        can_msg = can.Message(arbitration_id=pgn,
                              data=[command_or_status, register_index, register_select,
                                    register_value[0], register_value[1], register_value[2], register_value[3],
                                    self.send_count],
                              is_extended_id=True)
        # do broadcast
        try:
            self.bus.send(can_msg)
            if pgn == self.PGN_CxD_MachineCommand:
                self.send_count = self.send_count + 1 if self.send_count < 255 else 0
            return True
        except can.CanError:
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

    def send_negotiate_nop(self):
        # CxD -> machine status
        pgn = self.PGN_CxD_MachineStatus
        # emergency stop command, with motion inhibit (maybe should be removed)
        spn_status_negotiate_nop = 0xF1
        # does not need register, so all zero
        spn_register_index = 0
        spn_register_select = 0
        spn_register_value = (0).to_bytes(4, byteorder='big')
        # do broadcast
        return self.broadcast_message(pgn, spn_status_negotiate_nop, spn_register_index,
                                      spn_register_select, register_value=spn_register_value)

    def get_negotiate_register(self):
        # CxD -> machine command
        pgn = self.PGN_CxD_MachineStatus
        # emergency stop command, with motion inhibit (maybe should be removed)
        spn_status_get_protocol_register = 0xF6
        # TODO: set index to "negotiation seed", correct register select, and right credential in value
        spn_register_index = 0
        spn_register_select = 0
        spn_register_value = (0).to_bytes(4, byteorder='big')
        # do broadcast
        return self.broadcast_message(pgn, spn_status_get_protocol_register, spn_register_index,
                                      spn_register_select, register_value=spn_register_value)

    def send_closest_obstacle_info(self, obstacle_type, obstacle_angle, obstacle_distance):
        pgn = self.PGN_CxD_MachineInfo
        if obstacle_type == 'person':
            spn_obstacle_type = 0x01
        elif obstacle_type == 'vehicle':
            spn_obstacle_type = 0x02
        else:
            spn_obstacle_type = 0x03
        if obstacle_angle == 'left':
            spn_obstacle_angle = 0x01
        elif obstacle_angle == 'right':
            spn_obstacle_angle = 0x02
        else:
            spn_obstacle_angle = 0
        # distance is supposed to be in mm and should be an integer
        spn_obstacle_distance = obstacle_distance.to_bytes(4, byteorder='big')
        can_msg = can.Message(arbitration_id=pgn,
                              data=[spn_obstacle_type, spn_obstacle_angle, 0, 0,
                                    spn_obstacle_distance[0], spn_obstacle_distance[1],
                                    spn_obstacle_distance[2], spn_obstacle_distance[3]],
                              is_extended_id=True)
        # return True if broadcast finished with no error
        try:
            self.bus.send(can_msg)
            return True  # there is CANBus available
        except can.CanError:
            return False  # there is no CANBus available


can_available = True
can_bus = CanBusSend()
# TODO: need test the emergency stop ability, currently only testing the can-bus availability
emergency_available = can_bus.send_stop(emergency=True, confirm=True)
while True:
    if emergency_available:
        start = time.time()
        can_bus.send_stop()
        can_bus.send_closest_obstacle_info(obstacle_type='person', obstacle_angle='left', obstacle_distance=1221)
        print(time.time() - start)
    time.sleep(0.5)
