from DeltaRobot import AcromeDelta
from acrome.controller import *
import time
import numpy as np

dev = Delta('COM10') # Default port is COM5


calc_Z=-206   #Z value of the coins
x_offset=2  
y_offset=-15
trajTime=2  #Time for the trajectory to complete
waypoint=[0,0, calc_Z+20]
placingPos=[0,-55,calc_Z]

#If the end effector is not grabbing the coin/touching the object on the tablet, change the X-Y-Z offsets
initialPos=[-15,-20,-180]

robot=AcromeDelta()
circlePoint=[0,0,3]

theta=robot.inverse_kin(initialPos[0],initialPos[1],initialPos[2])
pos=robot.angletoPos(theta)
dev.set_motors(np.int_(pos)) # Go to waypoint
dev.update()
while True:
    try:
        circlePoint=robot.detect()
        if circlePoint is not None:
            for i in range(6):
                startTime = time.time()
                endTime = time.time()

                coinPos= [circlePoint[0] + x_offset,circlePoint[1]-circlePoint[1]/20,calc_Z]

                if circlePoint[2]==3: # Triangle
                    placingPos=[20,coinPos[1],calc_Z]
                elif circlePoint[2]==4: # Square
                    placingPos=[32,coinPos[1],calc_Z]
                elif circlePoint[2]==5: #Circle
                    placingPos=[45,coinPos[1],calc_Z]
                    
                waypoint=[placingPos[0],coinPos[1],calc_Z+20]
                if i==0:
                    Ipos=initialPos
                    coinPos[2]=initialPos[2]
                    Fpos=coinPos
                    trajTime=1
                elif i==1:
                    Ipos=coinPos
                    coinPos[2]=calc_Z
                    Fpos=coinPos
                    trajTime=0.5
                elif i==2:
                    Ipos=coinPos
                    coinPos[2]=initialPos[2]
                    Fpos=coinPos
                    trajTime=0.5
                elif i==3:
                    Ipos=coinPos
                    Fpos=waypoint
                    trajTime=0.5
                elif i==4:
                    Ipos=waypoint
                    Fpos=placingPos
                elif i==5:
                    Ipos=placingPos
                    Fpos=initialPos
                while(endTime-startTime)<trajTime:
                    traj_pos=robot.trajectory(startTime,Ipos,Fpos,trajTime)
                    theta=robot.inverse_kin(Fpos[0],Fpos[1],Fpos[2])
                    pos=robot.angletoPos(theta)
                    dev.pick(True)
                    dev.set_motors(np.int_(pos))
                    dev.update()
                    endTime = time.time()
                    time.sleep(0.05)
        else:
            theta=robot.inverse_kin(initialPos[0],initialPos[1],initialPos[2])
            pos=robot.angletoPos(theta)
            dev.set_motors(np.int_(pos)) # Go to waypoint
            dev.update()
            print("not detected")
    except Exception as e: 
        print(e)  
        pass