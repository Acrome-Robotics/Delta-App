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
trajTime=0.5
circletime=6
amplitude= 50
Rect1=[0,-0,-140]
Rect2=[0,0,-229]
Rect3=[0,0,-140]
Rect4=[0,0,-229]
circlePos=[0,0,-180]

#If the end effector is not grabbing the coin, set the X-Y-Z offsets
calc_Z=-229     #Z value of the coins
x_offset=15  
y_offset=0

theta=robot.inverse_kin(Rect4[0],Rect4[1],Rect4[2])
pos=robot.angletoPos(theta)
dev.set_motors(np.int_(pos)) # Go to initial position
dev.update()
#Rectangle

while(1):
    print("Square Mode")
    for j in range(0,2):
        for i in range(0,4):
            startTime = time.time()
            endTime = time.time()
            """
            i=0 L4 -> L1
            i=1 L1 -> L2
            i=2 L2 -> L3
            i=3 L3 -> L4
            """

            if i==0:
                Ipos=Rect4
                Fpos=Rect1
            if i==1:
                Ipos=Rect1
                Fpos=Rect2
            if i==2:
                Ipos=Rect2
                Fpos=Rect3
            if i==3:
                Ipos=Rect3
                Fpos=Rect4
            while(endTime-startTime)<trajTime:
                traj_pos=robot.trajectory(startTime,Ipos,Fpos,trajTime)
                theta=robot.inverse_kin(traj_pos[0],traj_pos[1],traj_pos[2])
                pos=robot.angletoPos(theta)
                dev.set_motors(np.int_(pos))
                dev.update()
                time.sleep(1)
                endTime = time.time()
    #Circle
    print("Circle Mode")
    startTime = time.time()
    endTime = time.time()
    while(endTime-startTime)<circletime:
        circlePos=[0,0,-180]
        t=time.time()
        circlePos[0]= np.sin((t-startTime)*2)* amplitude
        circlePos[1]= np.cos((t-startTime)*2)* amplitude
        theta=robot.inverse_kin(circlePos[0],circlePos[1],circlePos[2])
        pos=robot.angletoPos(theta)
        dev.set_motors(np.int_(pos))
        dev.update()
        time.sleep(0.1)
        endTime = time.time()
