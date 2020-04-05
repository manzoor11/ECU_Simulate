# import the library
import can
import cantools

import socket, sys
from PyQt5.QtWidgets import QApplication, QPlainTextEdit, QWidget, QVBoxLayout, QDialog, QPushButton, QTableWidget

import logging
import time

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

        self.db = cantools.database.load_file('Sample.dbc')
        self.example_message = self.db.get_message_by_name('ExampleMessage')
        self.test_message = self.db.get_message_by_name('Message1')

class traceCAN():
    def __init__(self):
        self.bus = vcan_active.bus
        self._recieveAll()

    def _recieveAll(self):
        # iterate over received messages
        for msg in self.bus:
            if (msg.arbitration_id == vcan_active.test_message.frame_id):
                data = vcan_active.test_message.encode({'Signal1': 1})
                rsp_msg = can.Message(arbitration_id=vcan_active.test_message.frame_id, data=data)
                self.bus.send(rsp_msg)
            #print(msg)
            try:
                print(msg.arbitration_id, vcan_active.db.decode_message(msg.arbitration_id, msg.data))
                logging.info((msg.arbitration_id, vcan_active.db.decode_message(msg.arbitration_id, msg.data)))
                break
            except:
                print("Message NOT sent")

class canMsg(vcan_config):
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
        # send message
        #msg = can.Message(arbitration_id=0x123, is_extended_id=False,data=[0x11, 0x22, 0x33])
        msg = can.Message(arbitration_id=canId, is_extended_id=False, data=canData)
        try:
            # Send Periodic Message
            task = can.send_periodic(self.bus, msg, period)
        except can.CanError:
            print("Message NOT sent")

        """
    def simple_periodic_send(self, canId, canData, period):
        
        #Sends a message every 20ms with no explicit timeout
        #Sleeps for 2 seconds then stops the task.
       
        print("Starting to send a message every 200ms for 2s")
        msg = can.Message(arbitration_id=canId, data=canData, is_extended_id=False)
        task = self.bus.send_periodic(msg, 0.20)
        assert isinstance(task, can.CyclicSendTaskABC)
        time.sleep(5)
        task.stop()
        print("stopped cyclic send")
        """

class canTasks (canMsg,traceCAN):
    def __init__(self):
        # Activate the Trace Window to Recieve all
        traceCAN()._recieveAll()

        # Send Periodic CAN Messages
        canID_Q = vcan_active.example_message.frame_id
        canData_Q = vcan_active.example_message.encode({'Temperature': 250.1, 'AverageRadius': (3.2), 'Enable': 1})
        canPeriod_Q = 1
        canMsg()._sendPeriodic(canId=canID_Q, canData=canData_Q, period=canPeriod_Q)
        # canMsg().simple_periodic_send(canId=canID_Q, canData=canData_Q,period=canPeriod_Q)


class QPlainTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

class MyDialog(QDialog, QPlainTextEdit, QTableWidget, canMsg):
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

    def test(self):
        # Send CAN Message
        canID_Q = vcan_active.test_message.frame_id
        canData_Q = vcan_active.test_message.encode({'Signal1': 1})
        canMsg()._send(canId=canID_Q, canData=canData_Q)

        #logging.debug('damn, a bug')
        #logging.info('\tcanId='+str(canID_Q)+'\tcanData='+str(canData_Q))
        #logging.warning('that\'s not right')
        #logging.error('foobar')

if (__name__ == '__main__'):
    vcan_active = vcan_config()
    canTask = canTasks()
    app = None
    if (not QApplication.instance()):
        app = QApplication([])
    #dlg = MyDialog()
    #dlg.show()
    #dlg.raise_()
    if (app):
        app.exec_()