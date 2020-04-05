# import the library
import can
import cantools
from pprint import pprint

# create a bus instance
# many other interfaces are supported as well (see below)
bus = can.Bus(interface='socketcan',
              channel='vcan0',
              receive_own_messages=True)

db = cantools.database.load_file('Sample.dbc')
example_message = db.get_message_by_name('ExampleMessage')
test_message = db.get_message_by_name('Message1')

data = example_message.encode({'Temperature': 250.1, 'AverageRadius': (3.2), 'Enable': 1})
msg = can.Message(arbitration_id=example_message.frame_id, data=data)

# send message
#msg = can.Message(arbitration_id=0x123, is_extended_id=False,data=[0x11, 0x22, 0x33])
try:
    can.send_periodic(bus, msg, 1)    # Send Periodic Message
    #bus.send(msg)                    # Send Single Message
    print(msg)
except can.CanError:
    print("Message NOT sent")

# iterate over received messages
for msg in bus:
    if(msg.arbitration_id == 0x444):
        data = test_message.encode({'Signal1': 1})
        rsp_msg = can.Message(arbitration_id=test_message.frame_id, data=data)
        bus.send(rsp_msg)
    #print(msg)
    try:
        print(db.decode_message(msg.arbitration_id, msg.data))
    except:
        print("Message NOT sent")

# or use an asynchronous notifier
#notifier = can.Notifier(bus, [can.Logger("recorded.log"), can.Printer()])
