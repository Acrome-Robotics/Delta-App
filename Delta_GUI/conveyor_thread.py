"""
Conveyor thread — automated pick-and-place mode.
Reads latest frame, detects objects, and performs 6-step trajectory.
"""

import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from delta_robot import AcromeDelta

class ConveyorThread(QThread):
    status_msg = pyqtSignal(str)          # Feedback messages to GUI
    processed_frame = pyqtSignal(object)  # Annotated frame to show in GUI

    def __init__(self, robot: AcromeDelta, dev, dev_mutex, z_limit=-206, parent=None):
        super().__init__(parent)
        self.robot = robot
        self.dev = dev
        self.dev_mutex = dev_mutex
        self._running = False
        self._mutex = QMutex()
        
        self.latest_frame = None
        
        # Conveyor params
        self.calc_Z = z_limit
        self.x_offset = 2
        self.y_offset = -15
        self.initialPos = [-15, -20, -180]
        self._is_at_initial_pos = False

    def set_frame(self, frame):
        """Receive the latest frame from CameraThread."""
        self._mutex.lock()
        self.latest_frame = frame
        self._mutex.unlock()

    def run(self):
        self._running = True
        
        # Go to initial position
        self.status_msg.emit("Conveyor started. Moving to initial position...")
        try:
            if self.dev is not None:
                self.dev_mutex.lock()
                self.dev.pick(False)
                theta = self.robot.inverse_kin(self.initialPos[0], self.initialPos[1], self.initialPos[2])
                pos = self.robot.angle_to_pos(theta)
                self.dev.set_motors(np.int_(pos))
                self.dev_mutex.unlock()
                self._is_at_initial_pos = True
        except Exception as e:
            self.status_msg.emit(f"Error: {e}")
            if self.dev_mutex.tryLock():
                self.dev_mutex.unlock()
            self._running = False
            return
            
        while self._running:
            self._mutex.lock()
            frame = self.latest_frame.copy() if self.latest_frame is not None else None
            self._mutex.unlock()
            
            if frame is None:
                self.msleep(50)
                continue
                
            try:
                # Detect object in the frame
                detection, annotated_frame = self.robot.detect(frame)
                
                # Emit annotated frame for display when conveyor mode is active
                self.processed_frame.emit(annotated_frame)
                
                if detection is not None:
                    self._is_at_initial_pos = False
                    obj_x, obj_y, label = detection
                    self.status_msg.emit(f"Object detected! Type: {label}")
                    
                    coinPos = [obj_x + self.x_offset, obj_y - obj_y/20, self.calc_Z]
                    
                    if label == 3: # Triangle
                        placingPos = [20, coinPos[1], self.calc_Z]
                    elif label == 4: # Square
                        placingPos = [32, coinPos[1], self.calc_Z]
                    elif label == 5: # Circle
                        placingPos = [45, coinPos[1], self.calc_Z]
                    else:
                        placingPos = [0, coinPos[1], self.calc_Z]
                        
                    waypoint = [placingPos[0], coinPos[1], self.calc_Z + 20]
                    
                    for i in range(6):
                        if not self._running:
                            break
                            
                        startTime = time.time()
                        
                        if i == 0:
                            Ipos = self.initialPos
                            coinPos[2] = self.initialPos[2]
                            Fpos = coinPos
                            trajTime = 1.0
                        elif i == 1:
                            Ipos = coinPos
                            coinPos[2] = self.calc_Z
                            Fpos = coinPos
                            trajTime = 0.5
                        elif i == 2:
                            Ipos = coinPos
                            coinPos[2] = self.initialPos[2]
                            Fpos = coinPos
                            trajTime = 0.5
                        elif i == 3:
                            Ipos = coinPos
                            Fpos = waypoint
                            trajTime = 0.5
                        elif i == 4:
                            Ipos = waypoint
                            Fpos = placingPos
                            trajTime = 1.0
                        elif i == 5:
                            Ipos = placingPos
                            Fpos = self.initialPos
                            trajTime = 1.0
                            
                        endTime = time.time()
                        while (endTime - startTime) < trajTime:
                            if not self._running:
                                break
                            traj_pos = self.robot.trajectory(startTime, Ipos, Fpos, trajTime)
                            theta = self.robot.inverse_kin(traj_pos[0], traj_pos[1], traj_pos[2])
                            pos = self.robot.angle_to_pos(theta)
                            
                            if self.dev is not None:
                                self.dev_mutex.lock()
                                self.dev.pick(True if i in [2, 3, 4] else False)
                                self.dev.set_motors(np.int_(pos))
                                self.dev_mutex.unlock()
                            
                            # Keep camera view fluid during movement by emitting latest raw frame
                            self._mutex.lock()
                            feed = self.latest_frame.copy() if self.latest_frame is not None else None
                            self._mutex.unlock()
                            if feed is not None:
                                self.processed_frame.emit(feed)
                            
                            endTime = time.time()
                            self.msleep(10) # Prevent 100% CPU
                            
                    self.status_msg.emit("Transfer complete, waiting for new object...")
                else:
                    self.status_msg.emit("Waiting for object...")
                    if self.dev is not None and not self._is_at_initial_pos:
                        theta = self.robot.inverse_kin(self.initialPos[0], self.initialPos[1], self.initialPos[2])
                        pos = self.robot.angle_to_pos(theta)
                        self.dev_mutex.lock()
                        self.dev.pick(False)
                        self.dev.set_motors(np.int_(pos))
                        self.dev_mutex.unlock()
                        self._is_at_initial_pos = True
                    self.msleep(30) # Wait a bit before trying to detect again (changed from 500 to keep fluid video)
            except Exception as e:
                self.status_msg.emit(f"Error: {e}")
                self.msleep(1000)

    def stop(self):
        self._running = False
        self.wait(5000)
