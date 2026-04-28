import time
import math
import cv2
import numpy as np

class AcromeDelta(object):
    _f = 230.59   #	Distance from center of machine base to center of each motor shaft.
    _e = 112.96  #	Distance from wrists to tool
    _rf= 64.2   #   Distance from motor shaft to elbow
    _re= 200    #   Distrance from elbow to the wrist

    """
    Calculate the forward kinematics of a robot arm based on the given joint angles.

    Args:
        theta1 (float): The angle of the first joint in degrees.
        theta2 (float): The angle of the second joint in degrees.
        theta3 (float): The angle of the third joint in degrees.

    Returns:
        list: The x, y, and z coordinates of the end effector in the global coordinate system.
    """
    def inverse_kin(self,x0,y0,z0):
        for i in range(3):
            if  i==0:
                x0_1 = x0
                y0_1 = y0
            elif i==1 :
                x0_1 = x0 * math.cos(math.pi/3*2) + y0 * math.sin(math.pi/3*2)
                y0_1 = y0 * math.cos(math.pi/3*2) - x0 * math.sin(math.pi/3*2)
            else:
                x0_1 = x0 * math.cos(math.pi/3*2) - y0 * math.sin(math.pi/3*2)
                y0_1 = y0 * math.cos(math.pi/3*2) + x0 * math.sin(math.pi/3*2)

            y1 = -0.5 * self.__class__._f * math.tan(math.pi / 6)
            y0_1 =y0_1 -(0.5 * math.tan(math.pi / 6)* self.__class__._e)

            a = (x0_1 * x0_1 + y0_1 * y0_1 + z0 * z0 + self.__class__._rf ** 2 - self.__class__._re ** 2 - y1 * y1) / (2 * z0)
            b = (y1 - y0_1) / z0

            #discriminant
            d = -( a + b * y1) * (a + b * y1) + self.__class__._rf * (b * b * self.__class__._rf + self.__class__._rf)

            yj = (y1 - a * b - math.sqrt(d)) / (b * b + 1)
            zj = a + b * yj

            if i==0 :
                if yj>y1:
                    max=180
                else:
                    max=0
                theta1 =( math.atan(-zj /(y1 - yj)) * 180) / math.pi + max
                
            elif i == 1 :
                if yj>y1 :
                    max=180
                else:
                    max=0
                theta2 =(math.atan(-zj / (y1 - yj)) * 180) / math.pi + max
                
            elif i == 2:
                if yj>y1 :
                    max=180
                else:
                    max=0
                theta3 = (math.atan(-zj /(y1 - yj)) * 180) / math.pi + max

        return [theta1,theta2,theta3]
    
    """
    Calculate the forward kinematics of a robot arm based on the given joint angles.

    Args:
        theta1 (float): The angle of the first joint in degrees.
        theta2 (float): The angle of the second joint in degrees.
        theta3 (float): The angle of the third joint in degrees.

    Returns:
        list: The x, y, and z coordinates of the end effector in the global coordinate system.
    """
    def forward_kin(self,theta1,theta2,theta3):
        theta1= theta1 * math.pi/180
        theta2= theta2 * math.pi/180
        theta3= theta3 * math.pi/180

        t = (self.__class__._f-self.__class__._e)*math.tan(math.pi/6)/2    

        y1 = -(t + self.__class__._rf*math.cos(theta1))
        z1 = -self.__class__._rf*math.sin(theta1)

        x2 = (t + self.__class__._rf*math.cos(theta2))*math.sin(math.pi/6)*math.tan(math.pi/3)
        y2 = (t + self.__class__._rf*math.cos(theta2))*math.sin(math.pi/6)
        z2 = -self.__class__._rf*math.sin(theta2)

        x3 = -((t + self.__class__._rf*math.cos(theta3))*math.sin(math.pi/6))*math.tan(math.pi/3)
        y3 = (t + self.__class__._rf*math.cos(theta3))*math.sin(math.pi/6)
        z3 = -self.__class__._rf*math.sin(theta3)
        #   Define the deminator parameter 
        d = (y2-y1)*x3-(y3-y1)*x2

        #   Define the wi parameters for i=1,2,3 as wi=xi*xi+yi*yi+zi*zi
        w1 = y1*y1 + z1*z1
        w2 = x2*x2 + y2*y2 + z2*z2
        w3 = x3*x3 + y3*y3 + z3*z3

        a1 = (z2-z1)*(y3-y1)-(z3-z1)*(y2-y1)
        b1 = -((w2-w1)*(y3-y1)-(w3-w1)*(y2-y1))/2.0

        a2 = -(z2-z1)*x3+(z3-z1)*x2
        b2 = ((w2-w1)*x3 - (w3-w1)*x2)/2.0

        a = a1**2 + a2**2 + d**2
        b = 2*(a1*b1 + a2*(b2-y1*d) - z1*d*d)
        c = (b2-y1*d)*(b2-y1*d) + b1*b1 + d*d*(z1*z1 - self.__class__._re**2)

        #discriminant
        disc = b*b - 4*a*c

        z = -0.5*(b+math.sqrt(disc))/a
        x = (a1*z + b1)/d
        y = (a2*z + b2)/d
        return [x,y,z]
    """
    This function performs object detection on the captured frame and returns the coordinates and label of the detected object.
    """
    def detect(self):

        y_offset = -20
        camera = cv2.VideoCapture(0+cv2.CAP_DSHOW)
        return_value, frame = camera.read()

        """img = cv2.imread("calibrationimage.JPG")
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        gray = np.float32(gray)
        dst = cv2.cornerHarris(gray,2,3,0.04)
        #result is dilated for marking the corners, not important
        dst = cv2.dilate(dst,None)
        ret, dst = cv2.threshold(dst,0.01*dst.max(),255,0)
        dst = np.uint8(dst)
        # find centroids
        ret, labels, stats, centroids = cv2.connectedComponentsWithStats(dst)
        print(centroids)"""
        centroids = np.float32([[319.49176421, 239.49275074],
                        [179.6, 118.4],
                        [489.57894737, 127.10526316],
                        [141.5, 432],
                        [505.42105263, 443.10526316]])
        pts1 = np.float32([centroids[2],centroids[1],centroids[4],centroids[3]]) # dont flip the image
        pts2 = np.float32([[0, 0], [550, 0], [0, 550], [550, 550]])

        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        correctedImg = cv2.warpPerspective(frame, matrix, (550, 550))
        gray = cv2.cvtColor(correctedImg, cv2.COLOR_BGR2GRAY)
        height, width= gray.shape[:2]
        y1 = 20
        roi_coordinates = (0, 550, 160+y1, 420+y1)  # Example coordinates, adjust as needed

        # Crop the image using slicing
        roi = gray[roi_coordinates[0]:roi_coordinates[1], roi_coordinates[2]:roi_coordinates[3]]
        height, width= roi.shape[:2]
        _, thresh = cv2.threshold(roi, 90, 200, cv2.THRESH_BINARY)
        cv2.imshow('thresh', roi)
        #cv2.waitKey(1) & 0xFF
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
            num_sides = len(approx)
            x=None
            y=None
            if num_sides == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                label=4
                if 0.95 <= aspect_ratio <= 1.05 and w > 30 and h > 30:
                    print("square detected")
                    print("x,y,label",x,y,label )
                    cv2.drawContours(thresh, [approx], 0, (0, 255, 0), -1)
                    cv2.putText(thresh, "Square", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)              
                else:
                    x=None
                    y=None
            elif num_sides == 3:
                M = cv2.moments(contour)
                if 800 < M['m00'] < 1000: 
                    print("triangle detected")
                    x = int(M['m10']/M['m00'])
                    y = int(M['m01']/M['m00'])
                    cv2.drawContours(thresh, [approx], 0, (0, 0, 255), -1)
                    cv2.putText(thresh, "Triangle", (approx[0][0][0], approx[0][0][1]), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                    label=3
                else:
                    x=None
                    y=None
            elif num_sides > 4 and num_sides < 15:
                (x, y), radius = cv2.minEnclosingCircle(contour)
                center = (int(x), int(y))
                radius = int(radius)
                if 15 < radius < 22:
                    print("circle detected")
                    cv2.circle(thresh, center, radius, (255, 0, 0), 2)
                    cv2.putText(thresh, "Circle", (int(x) - radius, int(y) - radius), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                    x=center[0]
                    y=center[1]
                    label=5
                else:
                    x=None
                    y=None
            if x is not None:
                cv2.imshow('Region of Interest', thresh)
                cv2.waitKey(1) & 0xFF
                valX=5-(x-34)/4.35
                valY=(y-158)/4.21+y_offset
                if (-50<valX<50 and y_offset<valY<50):
                    return (valX,valY,label)
        return None
    """
    Higher(5th) order trajectory function that calculates the position trajectory based on initial and final positions, start and end times, and initial and final velocities and accelerations. 

    Parameters:
    - startTime: the start time for the trajectory calculation
    - Ipos: list of initial positions
    - Fpos: list of final positions
    - tf: the end time for the trajectory calculation

    Returns:
    - PosTraj: list of position trajectory at each time step
    """
    def trajectory(self,startTime,Ipos,Fpos,tf):
        #Higher(5th) order trajectory function 
        endTime = time.time()
        t=(endTime-startTime) #ElapsedTime
        Final_Velocity=0 
        Final_Acceleration=0
        Initial_Velocity=0
        Initial_Acceleration=0
        PosTraj = [0,0,0]  # Initialize the position trajectory
        for i in range(3):
            a0 = Ipos[i]
            a1 = Initial_Velocity
            a2 = Initial_Acceleration/2
            a3 = (20*Fpos[i] - 20*Ipos[i] - ((8*Final_Velocity + 12*Initial_Velocity)*tf) - (tf*tf*(3*Initial_Acceleration - Final_Acceleration)))/(2*tf**3)
            a4 = (30*Ipos[i] - 30*Fpos[i] + ((14*Final_Velocity + 16*Initial_Velocity)*tf) + (tf*tf*(3*Initial_Acceleration - 2*Final_Acceleration)))/(2*tf**4)
            a5 = (12*Fpos[i] - 12*Ipos[i] - ((6*Final_Velocity + 6*Initial_Velocity)*tf) - (tf*tf*(Initial_Acceleration - Final_Acceleration)))/(2*tf**5)
            PosTraj[i] = a5*t**5 + a4*t**4 + a3*t**3 + a2*t**2 + a1*t + a0
        return PosTraj
    """
    Converts the position to angle
    """        
    def postoAngle(self,pos):
        theta=-np.multiply(pos-512,0.32612)     #Converts the position to angle
        return theta
    """
    Converts the angle to position.
    """
    def angletoPos(self,theta):
        pos = np.divide(theta,-0.32612) + 512   #Converts the angle to position
        return pos
    
"""robot=AcromeDelta()
robot.detect()"""