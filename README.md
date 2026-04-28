# Acrome Delta Robot App Suite

This repository contains the completely modernized Client-Server architecture for controlling the Acrome Delta Robot. It includes a user-friendly standalone Desktop GUI and a high-performance HTTP REST API for seamless remote and wireless control.

## 📂 Project Structure

- **`gui/`** 🖥️ — Desktop GUI applications (PyQt5)
  - **`gui/remote/`** — API Client mode. Controls the robot over HTTP via the backend API.
  - **`gui/standalone/`** — Standalone mode. Connects directly to hardware via USB/UART (no API required).
  - Both modes feature:
    - **Manual Control:** Drive the robot to X, Y, Z coordinates via sliders and XY pad.
    - **Demo Movements:** Continuous circle and square drawing modes.
    - **Conveyor Mode:** Automated computer vision-based pick-and-place.

- **`api/`** 🌐 — REST API Server (Flask)
  Backend server that runs on Raspberry Pi or Windows. Connects to the Delta robot's UART/USB ports, computes forward/inverse kinematics, and exposes simple HTTP endpoints.

- **`examples/`** 📝 — Usage Examples
  - **`api_usage/`** — Robot control examples via the API (Python & MATLAB).
  - **`delta_conveyor/`** & **`delta_demo/`** — Legacy scripts with direct hardware access.

- **`deploy/`** 🚀 — Deployment files (`setup.sh`, `delta_api.service`)

- **`build/`** 🔧 — PyInstaller build configurations (`.spec` files)

- **`releases/windows/`** 📦 — Compiled Windows executables:
  - `AcromeDeltaGUI_Remote/` — API client GUI (folder mode)
  - `AcromeDeltaGUI_Standalone.exe` — Standalone GUI (no API required)
  - `DeltaAPI.exe` — API server

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

### 🚀 Raspberry Pi Setup

Copy the project to your Raspberry Pi and run the setup script:
```bash
cd Delta-App/deploy
bash setup.sh
```

After setup, from any terminal:
```bash
delta start    # Start the API server
delta stop     # Stop the API server
delta status   # Check if API is running
delta log      # Follow logs in real-time
```
