"""
Delta Robot kinematics, trajectory planning, and object detection module.
Consolidated from delta_conveyor/DeltaRobot.py and delta_demo/DeltaRobot.py.
"""

import time
import math
import cv2
import numpy as np


class AcromeDelta:
    """Delta robot kinematics and utility class."""

    # Geometric parameters (mm)
    _f = 230.59   # Distance from center of machine base to center of each motor shaft
    _e = 112.96   # Distance from wrists to tool
    _rf = 64.2    # Distance from motor shaft to elbow
    _re = 200     # Distance from elbow to the wrist

    def inverse_kin(self, x0, y0, z0):
        """
        Calculate inverse kinematics: Cartesian (x, y, z) → joint angles (θ1, θ2, θ3).

        Args:
            x0, y0, z0: End-effector position in mm.

        Returns:
            list: [theta1, theta2, theta3] in degrees.
        """
        theta = [0.0, 0.0, 0.0]

        for i in range(3):
            if i == 0:
                x0_1 = x0
                y0_1 = y0
            elif i == 1:
                x0_1 = x0 * math.cos(math.pi / 3 * 2) + y0 * math.sin(math.pi / 3 * 2)
                y0_1 = y0 * math.cos(math.pi / 3 * 2) - x0 * math.sin(math.pi / 3 * 2)
            else:
                x0_1 = x0 * math.cos(math.pi / 3 * 2) - y0 * math.sin(math.pi / 3 * 2)
                y0_1 = y0 * math.cos(math.pi / 3 * 2) + x0 * math.sin(math.pi / 3 * 2)

            y1 = -0.5 * self._f * math.tan(math.pi / 6)
            y0_1 = y0_1 - (0.5 * math.tan(math.pi / 6) * self._e)

            a = (x0_1 ** 2 + y0_1 ** 2 + z0 ** 2 + self._rf ** 2 - self._re ** 2 - y1 ** 2) / (2 * z0)
            b = (y1 - y0_1) / z0

            # Discriminant
            d = -(a + b * y1) ** 2 + self._rf * (b ** 2 * self._rf + self._rf)

            yj = (y1 - a * b - math.sqrt(d)) / (b ** 2 + 1)
            zj = a + b * yj

            if yj > y1:
                offset = 180
            else:
                offset = 0
            theta[i] = (math.atan(-zj / (y1 - yj)) * 180) / math.pi + offset

        return theta

    def forward_kin(self, theta1, theta2, theta3):
        """
        Calculate forward kinematics: joint angles (θ1, θ2, θ3) → Cartesian (x, y, z).

        Args:
            theta1, theta2, theta3: Joint angles in degrees.

        Returns:
            list: [x, y, z] position in mm.
        """
        theta1 = theta1 * math.pi / 180
        theta2 = theta2 * math.pi / 180
        theta3 = theta3 * math.pi / 180

        t = (self._f - self._e) * math.tan(math.pi / 6) / 2

        y1 = -(t + self._rf * math.cos(theta1))
        z1 = -self._rf * math.sin(theta1)

        x2 = (t + self._rf * math.cos(theta2)) * math.sin(math.pi / 6) * math.tan(math.pi / 3)
        y2 = (t + self._rf * math.cos(theta2)) * math.sin(math.pi / 6)
        z2 = -self._rf * math.sin(theta2)

        x3 = -((t + self._rf * math.cos(theta3)) * math.sin(math.pi / 6)) * math.tan(math.pi / 3)
        y3 = (t + self._rf * math.cos(theta3)) * math.sin(math.pi / 6)
        z3 = -self._rf * math.sin(theta3)

        # Denominator
        d = (y2 - y1) * x3 - (y3 - y1) * x2

        # w_i parameters
        w1 = y1 ** 2 + z1 ** 2
        w2 = x2 ** 2 + y2 ** 2 + z2 ** 2
        w3 = x3 ** 2 + y3 ** 2 + z3 ** 2

        a1 = (z2 - z1) * (y3 - y1) - (z3 - z1) * (y2 - y1)
        b1 = -((w2 - w1) * (y3 - y1) - (w3 - w1) * (y2 - y1)) / 2.0

        a2 = -(z2 - z1) * x3 + (z3 - z1) * x2
        b2 = ((w2 - w1) * x3 - (w3 - w1) * x2) / 2.0

        a = a1 ** 2 + a2 ** 2 + d ** 2
        b = 2 * (a1 * b1 + a2 * (b2 - y1 * d) - z1 * d * d)
        c = (b2 - y1 * d) ** 2 + b1 ** 2 + d ** 2 * (z1 ** 2 - self._re ** 2)

        # Discriminant
        disc = b ** 2 - 4 * a * c

        z = -0.5 * (b + math.sqrt(disc)) / a
        x = (a1 * z + b1) / d
        y = (a2 * z + b2) / d

        return [x, y, z]

    def trajectory(self, start_time, initial_pos, final_pos, tf):
        """
        5th-order polynomial trajectory planner.

        Args:
            start_time: Start timestamp (time.time()).
            initial_pos: [x, y, z] initial position.
            final_pos: [x, y, z] final position.
            tf: Total trajectory duration in seconds.

        Returns:
            list: [x, y, z] interpolated position at current time.
        """
        t = time.time() - start_time
        pos_traj = [0.0, 0.0, 0.0]

        for i in range(3):
            a0 = initial_pos[i]
            a1 = 0  # Initial velocity
            a2 = 0  # Initial acceleration / 2
            a3 = (20 * final_pos[i] - 20 * initial_pos[i]) / (2 * tf ** 3)
            a4 = (30 * initial_pos[i] - 30 * final_pos[i]) / (2 * tf ** 4)
            a5 = (12 * final_pos[i] - 12 * initial_pos[i]) / (2 * tf ** 5)
            pos_traj[i] = a5 * t ** 5 + a4 * t ** 4 + a3 * t ** 3 + a2 * t ** 2 + a1 * t + a0

        return pos_traj

    def pos_to_angle(self, pos):
        """Convert motor position (0-1023) to angle (degrees)."""
        theta = -np.multiply(pos - 512, 0.32612)
        return theta

    def angle_to_pos(self, theta):
        """Convert angle (degrees) to motor position (0-1023)."""
        pos = np.divide(theta, -0.32612) + 512
        return pos

    def detect(self, frame):
        """
        Detect shapes (square, triangle, circle) in a given frame.

        Args:
            frame: BGR image (numpy array) from camera.

        Returns:
            tuple: (valX, valY, label) or None if nothing detected.
                   label: 3=triangle, 4=square, 5=circle
            annotated_frame: The frame with detection annotations drawn on it.
        """
        y_offset = -20

        centroids = np.float32([
            [319.49176421, 239.49275074],
            [179.6, 118.4],
            [489.57894737, 127.10526316],
            [141.5, 432],
            [505.42105263, 443.10526316]
        ])

        pts1 = np.float32([centroids[2], centroids[1], centroids[4], centroids[3]])
        pts2 = np.float32([[0, 0], [550, 0], [0, 550], [550, 550]])

        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        corrected_img = cv2.warpPerspective(frame, matrix, (550, 550))
        gray = cv2.cvtColor(corrected_img, cv2.COLOR_BGR2GRAY)

        y1 = 20
        roi_coordinates = (0, 550, 160 + y1, 420 + y1)
        roi = gray[roi_coordinates[0]:roi_coordinates[1], roi_coordinates[2]:roi_coordinates[3]]

        _, thresh = cv2.threshold(roi, 90, 200, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Create an annotated copy for display
        annotated = frame.copy()

        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
            num_sides = len(approx)
            x = None
            y = None
            label = None

            if num_sides == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.95 <= aspect_ratio <= 1.05 and w > 30 and h > 30:
                    label = 4
                    cv2.drawContours(annotated, [approx], 0, (0, 255, 0), 2)
                    cv2.putText(annotated, "Square", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    x, y = None, None

            elif num_sides == 3:
                M = cv2.moments(contour)
                if 800 < M['m00'] < 1000:
                    x = int(M['m10'] / M['m00'])
                    y = int(M['m01'] / M['m00'])
                    label = 3
                    cv2.drawContours(annotated, [approx], 0, (0, 0, 255), 2)
                    cv2.putText(annotated, "Triangle", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            elif 4 < num_sides < 15:
                (cx, cy), radius = cv2.minEnclosingCircle(contour)
                if 15 < radius < 22:
                    x, y = int(cx), int(cy)
                    label = 5
                    cv2.circle(annotated, (x, y), int(radius), (255, 0, 0), 2)
                    cv2.putText(annotated, "Circle", (x - int(radius), y - int(radius)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            if x is not None and label is not None:
                val_x = 5 - (x - 34) / 4.35
                val_y = (y - 158) / 4.21 + y_offset
                if -50 < val_x < 50 and y_offset < val_y < 50:
                    return (val_x, val_y, label), annotated

        return None, annotated
