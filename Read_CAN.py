import can
import logging
import cantools


def _get_message(msg):

    return msg


class VCANBus(object):

    def __init__(self):

        print("Initializing CANbus")
        # create a bus instance
        # many other interfaces are supported as well (see below)
        self.bus = can.Bus(interface='socketcan',
                      channel='vcan0',
                      receive_own_messages=True)

        self.db = cantools.database.load_file('Sample.dbc')
        self.example_message = self.db.get_message_by_name('ExampleMessage')
        self.test_message = self.db.get_message_by_name('Message1')

        self.buffer = can.BufferedReader()
        self.notifier = can.Notifier(self.bus, [_get_message, self.buffer])

    def send_message(self, message):

        try:
            self.bus.send(message)
            return True
        except can.CanError:
            print("message not sent!")
            return False

    def send_message_periodic(self):
        msg = can.Message(arbitration_id=0x222, is_extended_id=False,data=[0x11, 0x22, 0x33])
        try:
            can.send_periodic(self.bus, msg, 2)
            return True
        except can.CanError:
            print("message not sent!")
            return False

    def read_input(self):

        #msg = can.Message(arbitration_id=0x78,
                          #data=[0x00],
                          #is_extended_id=False)

        #self.send_message(msg)
        return self.buffer.get_message()

    def flush_buffer(self):

        msg = self.buffer.get_message()
        while (msg is not None):
            msg = self.buffer.get_message()

    def cleanup(self):

        self.notifier.stop()
        self.bus.shutdown()

    def disable_update(self):

        for i in [50, 51, 52, 53]:

            data = self.example_message.encode({'Temperature': 250.1, 'AverageRadius': (3.2), 'Enable': 1})
            msg = can.Message(arbitration_id=self.example_message.frame_id, data=data)

            self.send_message(msg)

if (__name__ == '__main__'):
    vcan_active = VCANBus()
    #msg = can.Message(arbitration_id=0x123, is_extended_id=False, data=[0x4F, 0x00])
    # vcan_active.send_message(msg)
    vcan_active.send_message_periodic()
    while (1):
        ret = vcan_active.read_input()
        if (ret != None):
            print(ret)
    vcan_active.cleanup()