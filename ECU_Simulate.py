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
        self._defaultConfig()

    def _defaultConfig(self):
        msgDataStat_active.canData_DashB_Curnt = msgDataStat_active.canData_DashB_Def
        msgDataStat_active.canData_Emergnc_Curnt = msgDataStat_active.canData_Emergnc_Def

class msgDataStatus ():
    def __init__(self):
        self.db = cantools.database.load_file('Sample.dbc')
        self.DashboardMessage = self.db.get_message_by_name('DashboardMessage')
        self.EmergencyMessage = self.db.get_message_by_name('EmergencyMessage')

        # Normal Situation
        self.canData_DashB_Def = self.DashboardMessage.encode({'Temperature': 50, 'Speed':15 , 'DoorLock': 1, 'SeatBelt':1})
        self.canData_Emergnc_Def = self.EmergencyMessage.encode({'CrashStat': 0, 'AirbagStat': 0})
        # Mock Events
        self.crashDetect = self.EmergencyMessage.encode({'CrashStat': 1, 'AirbagStat': 0})
        self.airbagRelease = self.EmergencyMessage.encode({'CrashStat': 1, 'AirbagStat': 1})
        self.overTemp = self.DashboardMessage.encode({'Temperature': 150, 'Speed':15 , 'DoorLock': 1, 'SeatBelt':1})
        self.vhclStop = self.DashboardMessage.encode({'Temperature': 150, 'Speed': 0, 'DoorLock': 0, 'SeatBelt': 0})

        self.canData_DashB_Curnt = None
        self.canData_Emergnc_Curnt = None

class traceCAN():

    def __init__(self):
        self.bus = vcan_active.bus

    def _recieveAll(self, stop_event):
        print("Start receiving messages")
        while not stop_event.is_set():
            rx_msg = self.bus.recv(1)
            if rx_msg is not None:
                msgDisp = (rx_msg.arbitration_id, msgDataStat_active.db.decode_message(rx_msg.arbitration_id, rx_msg.data))
                msgDt = (msgDataStat_active.db.decode_message(rx_msg.arbitration_id, rx_msg.data))
                # try:
                #     if (((msgDt['CrashStat'] == 'Crash_Detect')) and ((msgDt['AirbagStat'] == 'Fine_Airbag'))):
                #         canID_Q = msgDataStat_active.EmergencyMessage.frame_id
                #         canData_Q = msgDataStat_active.EmergencyMessage.encode({'CrashStat': 1, 'AirbagStat': 1})  #(msgDataStat_active.airbagRelease)
                #         sendMsg()._send(canId=canID_Q, canData=canData_Q)
                #         #sendMsg()._send(canId=canID_Q, canData=canData_Q)
                #         logging.info('AirBag Released')
                # except KeyError:
                #     pass

                print("rx: {}".format(msgDisp))
        print("Stopped receiving messages")
        #return can.Notifier(self.bus, [can.Printer()])

    def _conditionalSignal(self,msg):
        msg = 1

class sendMsg(vcan_config):
    def __init__(self):
        self.cyclicTask = None

    def _send(self, canId, canData):
        # send message
        msg = can.Message(arbitration_id= canId, is_extended_id=False, data= canData)
        try:
            # Send Single Message
            vcan_active.bus.send(msg)
        except can.CanError:
            print("Message NOT sent")

    def _sendPeriodic(self, canId, canData, period):
        print("Periodic Can Message - Every" + str(period) + "sec")
        msg = can.Message(arbitration_id=canId, is_extended_id=False, data=canData)
        try:
            self.cyclictask = can.send_periodic(vcan_active.bus, msg, period)
        except can.CanError:
            print("Message NOT sent")

class cyclicMsg (sendMsg,traceCAN, msgDataStatus):
    def __init__(self):
        # Send Periodic CAN Messages
        canID_Q = msgDataStat_active.DashboardMessage.frame_id
        canData_Q = msgDataStat_active.canData_DashB_Curnt
            #msgDataStat_active.DashboardMessage.encode({'Temperature': 50, 'Speed':15 , 'DoorLock': 1, 'SeatBelt':1})
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
        self._button1.setText('Crash')
        self._button2 = QPushButton(self)
        self._button2.setText('Over Heat')

        layout = QVBoxLayout()
        btnLayout =QHBoxLayout()
        # Add the new logging box widget to the layout
        layout.addWidget(logTextBox.widget)
        btnLayout.addWidget(self._button1)
        btnLayout.addWidget(self._button2)
        layout.addLayout(btnLayout)
        self.setLayout(layout)
        # Connect signal to slot
        self._button1.clicked.connect(self._btnCrash)
        self._button2.clicked.connect(self._btnEngHeat)

    def _btnCrash(self):
        # Send CAN Message
        canID_Q = msgDataStat_active.EmergencyMessage.frame_id
        canData_Q = msgDataStat_active.EmergencyMessage.encode({'CrashStat': 1, 'AirbagStat': 0}) #(msgDataStat_active.crashDetect)

        sendMsg()._send(canId=canID_Q, canData=canData_Q)
        logging.info('Crash Detected')

    def _btnEngHeat(self):
        # Send CAN Message
        canPeriod_Q = 1
        canID_Q = msgDataStat_active.DashboardMessage.frame_id
        canData_Q = msgDataStat_active.DashboardMessage.encode({'Temperature': 100, 'Speed':15 , 'DoorLock': 1, 'SeatBelt':1})

        msg = can.Message(arbitration_id=canID_Q, is_extended_id=False, data=canData_Q)
        #cyclicMsg_active.cyclicTask.modify_data(vcan_active.bus, msg, canPeriod_Q)
        cyclicMsg_active._sendPeriodic(canId=canID_Q, canData=canData_Q, period=canPeriod_Q)
        #sendMsg()._send(canId=canID_Q, canData=canData_Q)
        logging.info('Engine - Over Temperature Detected')

if (__name__ == '__main__'):
    msgDataStat_active = msgDataStatus()
    vcan_active = vcan_config()
    cyclicMsg_active = cyclicMsg()
    trace_active = traceCAN()
    stop_event = threading.Event()
    t_receive = threading.Thread(target=trace_active._recieveAll, args=(stop_event,))
    t_receive.start()
    app = None
    if (not QApplication.instance()):
        app = QApplication([])
    dlg = simulatorWindow()
    dlg.show()
    dlg.raise_()
    if (app):
        app.exec_()
    stop_event.set()