# Delta API Server

This folder contains the Flask API to control the Delta Device.

## Installation

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running as a Python script

```bash
python app.py
```
It will ask you for the COM port, then start the server at `http://127.0.0.1:5000`.

## Building the Executable (.exe)

You can convert this API to a standalone executable to distribute it without needing Python installed on the target machine.

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build the executable:
   ```bash
   pyinstaller --onefile app.py
   ```
   *Note: Because our script adds parent directories to `sys.path` to import `DeltaRobot` and `acrome.controller`, PyInstaller might need help locating these files. We can specify hidden imports or paths:*
   
   ```bash
   pyinstaller --onefile --paths=../python-library --paths=../delta_conveyor app.py
   ```

3. Your `app.exe` will be located in the `dist` folder. You can double click it, and it will run the terminal asking for the COM port.

## Endpoints

- `POST /move_pos`: `{"x": 0, "y": 0, "z": -200}`
- `POST /move_pos_traj`: `{"x": 0, "y": 0, "z": -200, "ms": 1500}`
- `POST /grab`: `{"state": 1}` or `{"state": 0}`
- `GET /get_mot_pos`
- `POST /delay`: `{"ms": 500}`
- `GET /get_ee_pos`
