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
initialPos=[-10,-50,-145]
placingPos=[0,-70,-225]
waypoint=[0,0,-180]

#If the end effector is not grabbing the coin, set the X-Y-Z offsets
calc_Z=-240     #Z value of the coins
x_offset=-10 
y_offset=20
dev.pick(True)
theta=robot.inverse_kin(initialPos[0],initialPos[1],initialPos[2])
pos=robot.angletoPos(theta)
dev.set_motors(np.int_(pos)) # Go to initial position
dev.update()
while 1:
    circlePoint=robot.detect_coins()
    if circlePoint is not None:
        for i in range(4):
            startTime = time.time()
            endTime = time.time()
            coinPos= [circlePoint[0]/5-55,circlePoint[1]/5-55,calc_Z] #Convert the pixel to the real world coordinates
            waypoint =[coinPos[0],(coinPos[1]+placingPos[1])/2,-180]
            """
            i=0 picking
            i=1 go to initial
            i=2 placing
            i=3 go to initial
            """
            if i==0:
                print("Initial Point")
                dev.pick(True)
                Ipos=initialPos
                Fpos=coinPos
            if i==1:
                print("Picking Point")
                dev.pick(True)
                Ipos=coinPos
                Fpos=waypoint
            if i==2:
                print("Initial Point")
                Ipos=waypoint
                Fpos=placingPos
            if i==3:
                print("Placing Point")
                dev.pick(False)
                Ipos=placingPos
                Fpos=initialPos
            while(endTime-startTime)<trajTime:
                traj_pos=robot.trajectory(startTime,Ipos,Fpos,trajTime)
                theta=robot.inverse_kin(traj_pos[0]+x_offset,traj_pos[1]+y_offset,traj_pos[2])
                pos=robot.angletoPos(theta)
                dev.set_motors(np.int_(pos))
                dev.update()
                time.sleep(0.1)
                endTime = time.time()
    else:
        print("not detected")
        break

