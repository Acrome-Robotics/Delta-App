"""
Camera feed thread — captures frames from a USB camera in a QThread,
emits frames as QImage signals for GUI display.
"""

import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, Qt
from PyQt5.QtGui import QImage


class CameraThread(QThread):
    """Background thread that continuously reads frames from a camera."""

    frame_ready = pyqtSignal(QImage)        # Raw frame for display
    raw_frame_ready = pyqtSignal(np.ndarray)  # Raw numpy frame for processing

    def __init__(self, camera_index=0, parent=None):
        super().__init__(parent)
        self._camera_index = camera_index
        self._running = False
        self._mutex = QMutex()
        self._capture = None

    def set_camera_index(self, index):
        """Change camera index. Thread must be stopped first."""
        self._camera_index = index

    def run(self):
        """Main loop: capture frames and emit signals."""
        self._capture = cv2.VideoCapture(self._camera_index + cv2.CAP_DSHOW)

        if not self._capture.isOpened():
            return

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self._running = True

        while self._running:
            ret, frame = self._capture.read()
            if not ret:
                continue

            # Emit raw frame for processing
            self.raw_frame_ready.emit(frame.copy())

            # Convert BGR → RGB for Qt display
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_ready.emit(q_img.copy())

            self.msleep(30)  # ~33 FPS

        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def stop(self):
        """Stop the capture loop."""
        self._running = False
        self.wait(3000)


class CameraEnumerator:
    """Utility to discover available cameras on the system."""

    @staticmethod
    def get_camera_names_windows():
        names = []
        try:
            import subprocess
            out = subprocess.check_output(
                ["powershell", "-Command", "Get-PnpDevice -Class Camera,ImageType,Image -Status OK -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FriendlyName"],
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode('utf-8', errors='ignore')
            names = [line.strip() for line in out.split('\n') if line.strip()]
        except Exception:
            pass
        return names

    @staticmethod
    def list_cameras(max_index=5):
        """
        Scan camera indices and return list of available ones.

        Returns:
            list of tuples: [(index, name_string), ...]
        """
        available = []
        hw_names = CameraEnumerator.get_camera_names_windows()
        hw_idx = 0
        for i in range(max_index):
            cap = cv2.VideoCapture(i + cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    name_str = f"Camera {i}"
                    if hw_idx < len(hw_names):
                        name_str += f" - {hw_names[hw_idx]}"
                        hw_idx += 1
                    available.append((i, name_str))
                cap.release()
        return available
