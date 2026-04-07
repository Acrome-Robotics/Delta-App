# Acrome Delta Robot App Suite

This repository contains various interfaces, applications, and libraries for controlling the Acrome Delta Robot. It includes a user-friendly standalone Desktop GUI, an HTTP API for remote integrations, core Python SDKs, and ready-to-run examples.

## 📂 Project Structure

This project is divided into several modules. Here is where you can find everything:

- **`Delta_GUI/`** 🖥️
  The main standalone desktop application built with PyQt5. It features:
  - **Manual Control Phase:** Drive the robot to X, Y, Z coordinates manually.
  - **Demo Movements:** Instruct the robot to draw circles or squares with adjustable speeds and radiuses.
  - **Conveyor Mode:** Fully automated computer vision-based pick-and-place mode using a camera feed to detect and relocate shapes (circles, squares, triangles).
  - **Standalone Executable:** You do not need Python to run the GUI! Simply navigate to `Delta_GUI/dist/` and run **`AcromeDeltaGUI.exe`**.

- **`delta_api/`** 🌐
  A web API (HTTP interface) to control the Delta robot. Useful for remote executions, integration into bigger factory systems, or controlling the robot via external post requests without needing a direct serial connection.

- **`python-library/`** 📚
  The core Python API wrapper (`acrome` module) used by all the other applications to communicate over Serial COM ports. If you want to build your own custom script for the Delta Robot, you should reference or install this package.

- **`examples/`** 📝
  Simple, single-purpose scripts and tutorials focusing on specific operations such as `delta_conveyor` (pure conveyor logic) and `delta_demo` (drawing shapes). Ideal for developers looking to understand the underlying code logic without the complexity of a GUI.

## 🚀 Quick Start (Running the GUI)

### Option 1: No Installation Required (Windows)
1. Go to the `Delta_GUI/dist/` directory.
2. Double-click on `AcromeDeltaGUI.exe`.
3. Select your Delta Robot's COM port and your USB Camera from the settings panel and click "Connect".

### Option 2: Running from Source
If you are developing or modifying the behavior:
1. Ensure your Python environment (Python 3) is active.
2. Install the necessary dependencies via the requirements files:
   ```bash
   pip install -r Delta_GUI/requirements.txt
   ```
   *(Note: Make sure the `acrome` python-library is accessible in your environment).*
3. Run the GUI:
   ```bash
   cd Delta_GUI
   python main.py
   ```

## 🎥 Conveyor Mode & Computer Vision
The Conveyor Mode requires a camera to be positioned correctly overlooking the pick zone.
1. Start the camera from the GUI.
2. Run the **Conveyor Mode** toggle.
3. The application will track the designated ROI (Region of Interest) at approximately 30 FPS, recognizing blocks via geometry (Square=4 sides, Triangle=3 sides, Circle=>4 sides with specific area checks). When detected, the robot computes inverse kinematics and executes a safe 6-step pick-and-place trajectory automatically. 

## 🔧 Troubleshooting
- **No Camera Found:** Check system device permissions or USB connections. Try clicking "Refresh" under the camera settings.
- **Lag in Video Feed:** Video performance has been optimized for the Region of Interest. Ensure well-lit conditions for best object extraction and shape approximations using OpenCV.
- **Robot Connection Error:** Ensure no other application (like Arduino IDE) is currently using the COM port.

---
*Built for Acrome Delta Robot systems.*
