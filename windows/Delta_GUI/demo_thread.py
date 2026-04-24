"""
Demo thread for Delta Robot.
Executes Circle or Square trajectories for demonstration.
"""

import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from delta_robot import AcromeDelta

class DemoThread(QThread):
    status_msg = pyqtSignal(str)

    MODE_CIRCLE = 1
    MODE_SQUARE = 2

    def __init__(self, robot: AcromeDelta, dev, dev_mutex, mode=MODE_CIRCLE, cx=0, cy=0, cz=-180, radius=50, parent=None):
        super().__init__(parent)
        self.robot = robot
        self.dev = dev
        self.dev_mutex = dev_mutex
        self.mode = mode
        self._running = False
        self.speed_factor = 1.0
        self.cx = cx
        self.cy = cy
        
        # Circle Parameters
        self.amplitude = radius
        self.circle_z = cz
        
        # Square Parameters
        self.base_trajTime = 0.5
        square_z = cz
        self.Rect1 = [cx - radius, cy - radius, square_z]
        self.Rect2 = [cx + radius, cy - radius, square_z]
        self.Rect3 = [cx + radius, cy + radius, square_z]
        self.Rect4 = [cx - radius, cy + radius, square_z]

    def set_mode(self, mode):
        self.mode = mode

    def set_speed(self, factor):
        self.speed_factor = max(0.1, factor)

    def run(self):
        self._running = True
        
        # Move to initial position depending on the mode safely
        try:
            if self.dev is not None:
                if self.mode == self.MODE_CIRCLE:
                    theta = self.robot.inverse_kin(self.cx, self.cy, self.circle_z)
                    self.status_msg.emit("Starting Circle demo...")
                else:
                    theta = self.robot.inverse_kin(self.Rect4[0], self.Rect4[1], self.Rect4[2])
                    self.status_msg.emit("Starting Square demo...")
                
                pos = self.robot.angle_to_pos(theta)
                self.dev_mutex.lock()
                self.dev.set_motors(np.int_(pos))
                self.dev_mutex.unlock()
                self.msleep(1000)
        except Exception as e:
            self.status_msg.emit(f"Start Error: {e}")
            self._running = False
            if self.dev_mutex.tryLock(): # safeguard unlock
                self.dev_mutex.unlock()
            return

        last_time = time.time()
        phase = 0.0
        
        while self._running:
            try:
                current_time = time.time()
                if self.mode == self.MODE_CIRCLE:
                    dt = current_time - last_time
                    last_time = current_time
                    phase += dt * (2.0 * self.speed_factor)
                    
                    circlePos = [0, 0, self.circle_z]
                    circlePos[0] = self.cx + np.sin(phase) * self.amplitude
                    circlePos[1] = self.cy + np.cos(phase) * self.amplitude
                    
                    theta = self.robot.inverse_kin(circlePos[0], circlePos[1], circlePos[2])
                    pos = self.robot.angle_to_pos(theta)
                    
                    if self.dev is not None:
                        self.dev_mutex.lock()
                        self.dev.set_motors(np.int_(pos))
                        self.dev_mutex.unlock()
                        
                    self.msleep(10)
                    
                elif self.mode == self.MODE_SQUARE:
                    # Execute 4 sides of the rectangle
                    for i in range(4):
                        if not self._running:
                            break
                            
                        seg_start = time.time()
                        last_seg_time = seg_start
                        
                        if i == 0:
                            Ipos = self.Rect4
                            Fpos = self.Rect1
                        elif i == 1:
                            Ipos = self.Rect1
                            Fpos = self.Rect2
                        elif i == 2:
                            Ipos = self.Rect2
                            Fpos = self.Rect3
                        elif i == 3:
                            Ipos = self.Rect3
                            Fpos = self.Rect4
                            
                        # Use current speed factor for this segment
                        current_trajTime = self.base_trajTime / self.speed_factor
                        
                        while True:
                            t = time.time()
                            elapsed = t - seg_start
                            if elapsed >= current_trajTime or not self._running:
                                break
                                
                            traj_pos = self.robot.trajectory(seg_start, Ipos, Fpos, current_trajTime)
                            theta = self.robot.inverse_kin(traj_pos[0], traj_pos[1], traj_pos[2])
                            pos = self.robot.angle_to_pos(theta)
                            
                            if self.dev is not None:
                                self.dev_mutex.lock()
                                self.dev.set_motors(np.int_(pos))
                                self.dev_mutex.unlock()
                                
                            self.msleep(15)
                            
                    # Update last_time just in case mode switches (though mode doesn't switch dynamically here)
                    last_time = time.time()
            except Exception as e:
                self.status_msg.emit(f"Error: {e}")
                self.msleep(500)

    def stop(self):
        self._running = False
        self.wait(3000)
