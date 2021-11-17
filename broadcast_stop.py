import time
import os
import random


class CanBusSend(object):
    can_prefix = 'cansend can0 '

    PGN_CxD_MachineStatus = '0CF21000'
    PGN_CxD_MachineCommand = '04F21100'
    PGN_CxD_MachineInfo = '04F21200'

    def __init__(self):
        self.send_count = 0  # maximum 255
        self.rand_seed = 10  # need to be sync between this computer and the target machine
        random.seed(self.rand_seed)

    def broadcast_message(self, pgn, command_or_status, register_index, register_select, register_value):
        # identifier (use count to identify this command, so we are sure the credential will match)
        message_identifier = '{:02x}'.format(self.send_count)
        # broadcast message
        can_message = self.can_prefix + pgn + '#' + command_or_status + \
            register_index + register_select + register_value + \
            message_identifier
        no_can_bus = os.system(can_message)
        # return True if broadcast finished with no error
        if no_can_bus:
            return False  # there is no canbus available
        else:
            self.send_count += 1
            return True  # there is canbus available

    def send_emergency_stop(self):
        # CxD -> machine command
        pgn = self.PGN_CxD_MachineCommand
        # emergency stop command, with motion inhibit (maybe should be removed)
        spn_command_emergency_stop = '0B'
        # does not need register, so all zero
        spn_register_index = '00'
        spn_register_select = '00'
        # credential (register value bytes)
        credential = '{:08x}'.format(random.randrange(2 ** 32 - 1))
        # identifier (use count to identify this command, so we are sure the credential will match)
        return self.broadcast_message(pgn, spn_command_emergency_stop, spn_register_index,
                                      spn_register_select, register_value=credential)

    def send_negotiate_nop(self):
        # CxD -> machine status
        pgn = self.PGN_CxD_MachineStatus
        # emergency stop command, with motion inhibit (maybe should be removed)
        spn_status_negotiate_nop = 'F1'
        # does not need register, so all zero
        spn_register_index = '00'
        spn_register_select = '00'
        spn_register_value = '00000000'
        # do broadcast
        return self.broadcast_message(pgn, spn_status_negotiate_nop, spn_register_index,
                                      spn_register_select, register_value=spn_register_value)

    def get_negotiate_register(self):
        # CxD -> machine command
        pgn = self.PGN_CxD_MachineStatus
        # emergency stop command, with motion inhibit (maybe should be removed)
        spn_status_get_protocol_register = 'F6'
        # TODO: set index to "negotiation seed", correct register select, and right credential in value
        spn_register_index = '00'
        spn_register_select = '00'
        spn_register_value = '00000000'
        # do broadcast
        return self.broadcast_message(pgn, spn_status_get_protocol_register, spn_register_index,
                                      spn_register_select, register_value=spn_register_value)

    def send_closest_obstacle_info(self, obstacle_type, obstacle_distance):
        pgn = self.PGN_CxD_MachineInfo = '04F21200'
        if obstacle_type == 'person':
            spn_obstacle_type = '01'
        elif obstacle_type == 'vehicle':
            spn_obstacle_type = '02'
        else:
            spn_obstacle_type = '03'
        spn_obstacle_distance = '{:08x}'.format(obstacle_distance)
        can_message = self.can_prefix + pgn + '#' + spn_obstacle_type + '000000' + spn_obstacle_distance
        no_can_bus = os.system(can_message)
        # return True if broadcast finished with no error
        if no_can_bus:
            return False  # there is no canbus available
        else:
            self.send_count += 1
            return True  # there is canbus available


can_available = True
can_bus = CanBusSend()
while True:
    if can_available:
        start = time.time()
        can_available = can_bus.send_emergency_stop()
        print(time.time() - start)
    time.sleep(0.5)
