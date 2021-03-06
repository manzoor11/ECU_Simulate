# import the library
import can
import cantools
import threading

import socket, sys
from PyQt5.QtWidgets import QApplication, QPlainTextEdit, QVBoxLayout,QHBoxLayout, QDialog, QPushButton, QTableWidget

import logging

# Uncomment below for terminal log messages
# logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(name)s - %(levelname)s - %(message)s')
class vcan_config():
    def __init__(self):
        """
        sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        interface = "vcan0"
        try:
            sock.bind((interface,))
        except OSError:
            sys.stderr.write("Could not bind to interface '%s'\n" % interface)
            do something about the error...
        """
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

    def _recieveAll(self, stop_event):
        print("Start receiving messages")
        while not stop_event.is_set():
            rx_msg = self.bus.recv(1)
            if rx_msg is not None:
                msgDisp = (rx_msg.arbitration_id, vcan_active.db.decode_message(rx_msg.arbitration_id, rx_msg.data))
                print("rx: {}".format(msgDisp))
        print("Stopped receiving messages")
        #return can.Notifier(self.bus, [can.Printer()])

class sendMsg(vcan_config):
    def __init__(self):
        self.bus = vcan_active.bus

    def _send(self, canId, canData):
        # send message
        msg = can.Message(arbitration_id= canId, is_extended_id=False, data= canData)
        try:
            # Send Single Message
            self.bus.send(msg)
        except can.CanError:
            print("Message NOT sent")

    def _sendPeriodic(self, canId, canData, period):
        print("Started Periodic Can Message - Every" + str(period) + "sec")
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

class simulatorWindow(QDialog, QPlainTextEdit, QTableWidget, sendMsg, traceCAN):
    def __init__(self, parent=None):
        super().__init__(parent)

        logTextBox = QPlainTextEditLogger(self)
        # You can format what is printed to text box
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(message)s', "%H:%M:%S"))
        logging.getLogger().addHandler(logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.INFO)

        self._button1 = QPushButton(self)
        self._button1.setText('Test Me')
        self._button2 = QPushButton(self)
        self._button2.setText('Start')

        layout = QVBoxLayout()
        btnLayout =QHBoxLayout()
        # Add the new logging box widget to the layout
        layout.addWidget(logTextBox.widget)
        btnLayout.addWidget(self._button1)
        btnLayout.addWidget(self._button2)
        layout.addLayout(btnLayout)
        self.setLayout(layout)
        # Connect signal to slot
        self._button1.clicked.connect(self._btn1Action)
        self._button2.clicked.connect(self._updateTrace)

    def _btnCrash(self):
        # Send CAN Message
        canID_Q = vcan_active.test_message.frame_id
        canData_Q = vcan_active.test_message.encode({'Signal1': 1})
        sendMsg()._send(canId=canID_Q, canData=canData_Q)
        logging.info('Crash Detected')

    def _btnEngHeat(self):
        # Send CAN Message
        canID_Q = vcan_active.test_message.frame_id
        canData_Q = vcan_active.example_message.encode({'Temperature': 265.0, 'AverageRadius': (3.2), 'Enable': 1})
        sendMsg()._send(canId=canID_Q, canData=canData_Q)
        logging.info('Engine - Over Temperature Detected')

if (__name__ == '__main__'):
    vcan_active = vcan_config()
    canTask = canTasks()
    trace_active = traceCAN()
    app = None
    if (not QApplication.instance()):
        app = QApplication([])
    dlg = simulatorWindow()
    dlg.show()
    dlg.raise_()
    stop_event = threading.Event()
    t_receive = threading.Thread(target=trace_active._recieveAll, args=(stop_event,))
    t_receive.start()
    if (app):
        app.exec_()
    stop_event.set()