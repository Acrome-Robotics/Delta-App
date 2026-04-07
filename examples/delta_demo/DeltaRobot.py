import time
import math
import cv2
import numpy as np

class AcromeDelta(object):
    _f = 230.59   #	Distance from center of machine base to center of each motor shaft.
    _e = 112.96  #	Distance from wrists to tool
    _rf= 64.2   #   Distance from motor shaft to elbow
    _re= 200    #   Distrance from elbow to the wrist

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

    def detect_coins(self):
        camera = cv2.VideoCapture(1+cv2.CAP_DSHOW)
        return_value, frame = camera.read()
        cv2.imshow('gray', frame)
        cv2.waitKey(1) & 0xFF == ord('0')
        img = cv2.imread("calibrationimage.JPG")
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        gray = np.float32(gray)
        dst = cv2.cornerHarris(gray,2,3,0.04)
        #result is dilated for marking the corners, not important
        dst = cv2.dilate(dst,None)
        ret, dst = cv2.threshold(dst,0.01*dst.max(),255,0)
        dst = np.uint8(dst)
        # find centroids
        ret, labels, stats, centroids = cv2.connectedComponentsWithStats(dst)

        pts1 = np.float32([centroids[2],centroids[1],centroids[4],centroids[3]]) # dont flip the image
        pts2 = np.float32([[0, 0], [550, 0], [0, 550], [550, 550]])

        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        correctedImg = cv2.warpPerspective(frame, matrix, (550, 550))
        # Convert to grayscale.
        gray = cv2.cvtColor(correctedImg, cv2.COLOR_BGR2GRAY)
        # Blur using 3 * 3 kernel.
        gray_blurred = cv2.blur(gray, (3, 3))
        # Apply Hough transform on the blurred image.
        cv2.imshow('gray', gray_blurred)
        cv2.waitKey(1) & 0xFF == ord('0')
        detected_circles = cv2.HoughCircles(gray_blurred, 
                        cv2.HOUGH_GRADIENT, 1, 50, param1 = 100,
                    param2 = 30, minRadius = 1, maxRadius = 100) #dp=1, minDist=50
        # convert nparray to list
        if detected_circles is not None:
            detected_circles = detected_circles[0].tolist()
            deletedItems = []
            for i in detected_circles:
                if i[1]<101:
                    #delete element from detected_circles
                    deletedItems.append(i)
            for j in deletedItems:
                detected_circles.remove(j)
            if detected_circles is not None and len(detected_circles) > 0:
                # Convert the circle parameters a, b and r to integers.
                detected_circles = np.uint16(np.around(detected_circles))
                print(detected_circles[0, :])
                return(detected_circles[0, :])
            else:
                return None

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
            
    def postoAngle(self,pos):
        theta=-np.multiply(pos-512,0.32612)     #Converts the position to angle
        return theta

    def angletoPos(self,theta):
        pos = np.divide(theta,-0.32612) + 512   #Converts the angle to position
        return pos