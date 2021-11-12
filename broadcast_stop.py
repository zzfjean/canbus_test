import time
import os
import random


random.seed(100)


def send_can_message(credential):
    can_prefix = 'cansend can0 '
    # CxD -> machine command
    PGN = '04F21100'
    # emergency stop command
    SPN_command = '0B0000'
    can_message = can_prefix + PGN + '#' + SPN_command + credential + '00'
    no_canbus = os.system(can_message)
    if no_canbus:
        return False    # there is no canbus available
    else:
        return True     # there is canbus available


count = 0
can_available = True
while True:
    if can_available:
        start = time.time()
        credential = '{:08x}'.format(random.randrange(2**32 - 1))
        can_available = send_can_message(credential)
        print(time.time() - start)
    time.sleep(0.5)
