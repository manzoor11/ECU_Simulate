# import the library
import can
import cantools
import threading

import socket, sys
from PyQt5.QtWidgets import QApplication, QPlainTextEdit, QWidget, QVBoxLayout, QDialog, QPushButton, QTableWidget

import logging
import time


def _get_message(msg):
    return msg

# Uncomment below for terminal log messages
# logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(name)s - %(levelname)s - %(message)s')
class vcan_config():
    def __init__(self):
        #sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        #interface = "vcan0"
        #try:
            #sock.bind((interface,))
        #except OSError:
            #sys.stderr.write("Could not bind to interface '%s'\n" % interface)
            # do something about the error...

        self.bus = can.Bus(interface='socketcan',
                           channel='vcan0',
                           receive_own_messages=True)
        self.buffer = can.BufferedReader()
        self.notifier = can.Notifier(self.bus, [_get_message, self.buffer])

        self.db = cantools.database.load_file('Sample.dbc')
        self.example_message = self.db.get_message_by_name('ExampleMessage')
        self.test_message = self.db.get_message_by_name('Message1')

class traceCAN():
    def __init__(self):
        self.bus = vcan_active.bus
        self.buffer = vcan_active.buffer
        self.notifier = vcan_active.notifier

    def flush_buffer(self):

        msg = self.buffer.get_message()
        while (msg is not None):
            msg = self.buffer.get_message()

    def cleanup(self):

        self.notifier.stop()
        self.bus.shutdown()

    def _recieveAll(self, bus, stop_event):
        print("Start receiving messages")
        while not stop_event.is_set():
            rx_msg = bus.recv(1)
            if rx_msg is not None:
                #print("rx: {}".format(rx_msg))
                print("rx: {}".format((rx_msg.arbitration_id, vcan_active.db.decode_message(rx_msg.arbitration_id, rx_msg.data))))
                simulatorWindow._updateTrace(rx_msg.arbitration_id, vcan_active.db.decode_message(rx_msg.arbitration_id, rx_msg.data))
        print("Stopped receiving messages")
        #return self.bus.recv()
        #return can.Notifier(self.bus, [can.Printer()])
            #self.buffer.get_message()
        #try:
            #print(self.buffer.get_message())
            #logging.info(self.buffer.get_message())  #((msg.arbitration_id, vcan_active.db.decode_message(msg.arbitration_id, msg.data)))
        #except:
            #print("Message NOT sent")

class sendMsg(vcan_config):
    def __init__(self):
        self.bus = vcan_active.bus

    def _send(self, canId, canData):
        # send message
        #msg = can.Message(arbitration_id=0x123, is_extended_id=False,data=[0x11, 0x22, 0x33])
        msg = can.Message(arbitration_id= canId, is_extended_id=False, data= canData)
        try:
            # Send Single Message
            self.bus.send(msg)
            #print(msg)
        except can.CanError:
            print("Message NOT sent")

    def _sendPeriodic(self, canId, canData, period):
        print("Started Periodic Can Message - Every" + str(period) + "sec")
        #print("tx: {}".format(tx_msg))
        #msg = can.Message(arbitration_id=0x123, is_extended_id=False,data=[0x11, 0x22, 0x33])
        msg = can.Message(arbitration_id=canId, is_extended_id=False, data=canData)
        try:
            can.send_periodic(self.bus, msg, period)
        except can.CanError:
            print("Message NOT sent")

class canTasks (sendMsg,traceCAN):
    def __init__(self):
        # Send Periodic CAN Messages
        canID_Q = vcan_active.example_message.frame_id
        canData_Q = vcan_active.example_message.encode({'Temperature': 250.1, 'AverageRadius': (3.2), 'Enable': 1})
        canPeriod_Q = 1
        sendMsg()._sendPeriodic(canId=canID_Q, canData=canData_Q, period=canPeriod_Q)

class QPlainTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

class simulatorWindow(QDialog, QPlainTextEdit, QTableWidget, sendMsg):
    def __init__(self, parent=None):
        super().__init__(parent)

        logTextBox = QPlainTextEditLogger(self)
        # You can format what is printed to text box
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(message)s', "%H:%M:%S"))
        logging.getLogger().addHandler(logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.INFO)

        self._button = QPushButton(self)
        self._button.setText('Test Me')

        layout = QVBoxLayout()
        # Add the new logging box widget to the layout
        layout.addWidget(logTextBox.widget)
        layout.addWidget(self._button)
        self.setLayout(layout)

        # Connect signal to slot
        self._button.clicked.connect(self.test)

    def _updateTrace(self, msg):
        logging.info(msg)

    def test(self):
        # Send CAN Message
        canID_Q = vcan_active.test_message.frame_id
        canData_Q = vcan_active.test_message.encode({'Signal1': 1})
        sendMsg()._send(canId=canID_Q, canData=canData_Q)

        #logging.debug('damn, a bug')
        #logging.info('\tcanId='+str(canID_Q)+'\tcanData='+str(canData_Q))
        #logging.warning('that\'s not right')
        #logging.error('foobar')

if (__name__ == '__main__'):
    vcan_active = vcan_config()
    stop_event = threading.Event()
    trace_active = traceCAN()
    t_receive = threading.Thread(target=trace_active._recieveAll, args=(vcan_active.bus, stop_event))
    t_receive.start()
    canTask = canTasks()

    app = None
    if (not QApplication.instance()):
        app = QApplication([])
    dlg = simulatorWindow()
    dlg.show()
    dlg.raise_()
    if (app):
            app.exec_()
    stop_event.set()