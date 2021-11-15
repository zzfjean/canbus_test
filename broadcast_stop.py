import time
import os
import random


class CanBusSend(object):
    can_prefix = 'cansend can0 '

    PGN_CxD_MachineStatus = '0CF21000'
    PGN_CxD_MachineCommand = '04F21100'

    def __init__(self):
        self.send_count = 0  # maximum 255
        self.rand_seed = 10  # need to be sync between this computer and the target machine
        random.seed(self.rand_seed)

    def send_emergency_stop(self):
        # CxD -> machine command
        PGN = self.PGN_CxD_MachineCommand
        # emergency stop command, with motion inhibit (maybe should be removed)
        SPN_command_emergency_stop = '0B'
        # does not need register, so all zero
        SPN_register_index = '00'
        SPN_register_select = '00'
        # credential (register value bytes)
        credential = '{:08x}'.format(random.randrange(2 ** 32 - 1))
        # identifier (use count to identify this command, so we are sure the credential will match)
        message_identifier = '{:02x}'.format(self.send_count)
        # broadcast message
        can_message = self.can_prefix + PGN + '#' + SPN_command_emergency_stop + \
                      SPN_register_index + SPN_register_select + \
                      credential + message_identifier
        no_can_bus = os.system(can_message)
        # return True if broadcast finished with no error
        if no_can_bus:
            return False    # there is no canbus available
        else:
            self.send_count += 1
            return True     # there is canbus available


can_available = True
can_bus = CanBusSend()
while True:
    if can_available:
        start = time.time()
        can_available = can_bus.send_emergency_stop()
        print(time.time() - start)
    time.sleep(0.5)
