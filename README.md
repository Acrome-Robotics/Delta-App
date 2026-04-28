# Acrome Delta Robot App Suite

This repository contains the completely modernized Client-Server architecture for controlling the Acrome Delta Robot. It includes a user-friendly standalone Desktop GUI and a high-performance HTTP REST API for seamless remote and wireless control.

## 📂 Project Structure

- **`GUI_/`** 🖥️
  The main standalone desktop application built with PyQt5. It acts as an API Client, meaning it no longer communicates with the hardware directly. Instead, it sends HTTP requests to the backend API over the network. It features:
  - **Manual Control:** Drive the robot to X, Y, Z coordinates manually via sliders or XYZ pads.
  - **Demo Movements:** Instruct the robot to draw precise circles or squares continuously.
  - **Conveyor Mode:** Automated computer vision-based pick-and-place mode.
  - **Standalone Executable:** You do not need Python to run the GUI! Simply navigate to `GUI_/src/dist/` and run **`AcromeDeltaGUI.exe`**.

- **`API/`** 🌐
  The brain of the operation. This is a RESTful HTTP backend Server (Flask-based) designed to run directly on the Raspberry Pi (or your local Windows machine). It connects to the Delta robot's hardware UART/USB ports, computes complex forward/inverse kinematics, and exposes extremely simple web endpoints for the GUI.

- **`examples/` & `windows/`** 📝
  Legacy or alternative scripts and deployment files for specific operations.

---

## 📡 REST API Documentation

The Delta API runs on `http://<YOUR_IP>:5000` and provides a fast, asynchronous interface to control the robot. The backend engine handles all complex mathematical conversions (Angles to XYZ, XYZ to Angles) automatically.

### 1. System Endpoints

#### `GET /list_ports`
Returns a list of all available serial ports on the server machine (including Raspberry Pi hardware UARTs like `/dev/serial0`).
- **Response:**
  ```json
  {
    "ports": [
      {"device": "/dev/serial0", "description": "Raspberry Pi Hardware UART (Pin 14/15)"},
      {"device": "COM3", "description": "USB Serial Port"}
    ]
  }
  ```

#### `POST /connect`
Connects the backend to the specified serial port and synchronizes the robot.
- **Request Body:**
  ```json
  { "port": "/dev/serial0" }
  ```
- **Response:** `{"status": "success"}` or `{"error": "..."}`

#### `POST /disconnect`
Safely terminates the serial connection to the robot.
- **Response:** `{"status": "success"}`

#### `GET /status`
Returns the current connection status of the backend API.
- **Response:** `{"status": "connected", "port": "/dev/serial0"}`

### 2. Telemetry Endpoints

#### `GET /get_telemetry`
Fetches both the raw motor AD angles (M1, M2, M3) and the calculated End-Effector spatial coordinates (X, Y, Z) in a single optimized request. Recommended for high-frequency polling.
- **Response:**
  ```json
  {
    "m1": 456, "m2": 512, "m3": 512,
    "x": 0.0, "y": 0.0, "z": -180.5
  }
  ```

#### `GET /get_mot_pos` & `GET /get_ee_pos`
Legacy fallback endpoints to fetch motor-only or end-effector-only positions individually.

### 3. Movement & Control Endpoints

#### `POST /move_pos`
Moves the robot directly to a specific X, Y, Z coordinate in space. The API automatically calculates the Inverse Kinematics and translates it to motor positions.
- **Request Body:**
  ```json
  {
    "x": 10.5,
    "y": -20.0,
    "z": -150.0
  }
  ```
- **Response:** `{"status": "success"}`

#### `POST /move_pos_traj`
Executes a time-based smooth trajectory movement to a specific X, Y, Z coordinate over a given duration.
- **Request Body:**
  ```json
  {
    "x": 10.5,
    "y": -20.0,
    "z": -150.0,
    "ms": 1500
  }
  ```
- **Response:** `{"status": "success"}`

#### `POST /grab`
Activates or deactivates the end-effector tool (e.g., electromagnet or pneumatic suction).
- **Request Body:**
  ```json
  { "state": 1 }  // 1 to turn ON, 0 to turn OFF
  ```
- **Response:** `{"status": "success", "state": 1}`

#### `POST /delay`
Introduces a strict delay (sleep) on the backend processing queue.
- **Request Body:**
  ```json
  { "ms": 500 }
  ```

---

### 🚀 How to Run the API (Raspberry Pi)
The API can be run automatically as a background service. A `delta_api.service` file is included in the `API` folder for Linux systemd integration.

To start it manually from the terminal:
```bash
cd API
source venv/bin/activate
python3 app.py
```
