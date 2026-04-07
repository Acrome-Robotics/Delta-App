from DeltaRobot import AcromeDelta
from acrome.controller import *
import time
import numpy as np
import serial.tools.list_ports
import time

def USB_serial_port():
    ports = list(serial.tools.list_ports.comports())
    if ports:
        for port, desc, hwid in sorted(ports):
            if 'Prolific USB-to-Serial Comm Port' in desc:
                return port
    else:
        return None
print(USB_serial_port())
dev = Delta(USB_serial_port()) # Default port is COM5

robot=AcromeDelta()
initialPos=[-10,-50,-145]
dev.pick(True)
theta=robot.inverse_kin(initialPos[0],initialPos[1],initialPos[2])
pos=robot.angletoPos(theta)
dev.set_motors(np.int_(pos)) # Go to initial position
dev.update()