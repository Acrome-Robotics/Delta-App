# Acrome Delta Robot App Suite

This repository contains the completely modernized Client-Server architecture for controlling the Acrome Delta Robot. It includes a user-friendly standalone Desktop GUI and a high-performance HTTP REST API for seamless remote and wireless control.

## 📂 Project Structure

- **`gui/`** 🖥️ — Desktop GUI uygulamaları (PyQt5)
  - **`gui/remote/`** — API Client modu. HTTP üzerinden backend API'ye bağlanarak robotu kontrol eder.
  - **`gui/standalone/`** — Standalone modu. Doğrudan USB/UART üzerinden donanıma bağlanır (API gerekmez).
  - Her iki mod da şu özelliklere sahiptir:
    - **Manual Control:** Slider ve XY pad ile X, Y, Z koordinatlarına hareket.
    - **Demo Movements:** Daire ve kare çizim modları.
    - **Conveyor Mode:** Bilgisayar görüntüsüne dayalı otomatik taşıma.

- **`api/`** 🌐 — REST API Sunucusu (Flask)
  Raspberry Pi veya Windows üzerinde çalışan backend sunucu. Delta robotun UART/USB portlarına bağlanır, ileri/ters kinematik hesaplar ve basit HTTP endpoint'leri sunar.

- **`examples/`** 📝 — Kullanım Örnekleri
  - **`api_usage/`** — API üzerinden robot kontrolü örnekleri (Python & MATLAB).
  - **`delta_conveyor/`** & **`delta_demo/`** — Doğrudan donanım erişimli legacy scriptler.

- **`deploy/`** 🚀 — Dağıtım dosyaları (`setup.sh`, `delta_api.service`)

- **`build/`** 🔧 — PyInstaller build konfigürasyonları (`.spec` dosyaları)

- **`releases/windows/`** 📦 — Derlenmiş Windows EXE dosyaları:
  - `AcromeDeltaGUI_Remote.exe` — API client GUI
  - `AcromeDeltaGUI_Standalone.exe` — Standalone GUI (API gerekmez)
  - `DeltaAPI.exe` — API sunucusu

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
The API can be run automatically as a background service. A `delta_api.service` file is included in the `deploy/` folder for Linux systemd integration.

To start it manually from the terminal:
```bash
cd api
source venv/bin/activate
python3 app.py
```

For automated setup on Raspberry Pi, use the setup script:
```bash
cd deploy
bash setup.sh
```
