import sys
import os
import time
import numpy as np
import threading

# Add project root and python-library to sys.path so we can import delta related modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'python-library'))

from flask import Flask, request, jsonify
from flask_cors import CORS
from acrome.controller import Delta
from delta_robot import AcromeDelta
import serial.tools.list_ports

app = Flask(__name__)
CORS(app)

dev = None
robot = None
api_lock = threading.Lock()
is_running = True

def telemetry_loop():
    """
    Background thread that continuously polls dev.update() every 10ms.
    This mimics the working Delta_GUI timer mechanism and prevents 
    the controller from timing out or dropping serial synchronization.
    """
    global dev
    while is_running:
        if dev is not None:
            with api_lock:
                try:
                    dev.update()
                except Exception as e:
                    # Clear input buffer on error to recover sync
                    try:
                        if hasattr(dev, '_Controller__ph'):
                            dev._Controller__ph.reset_input_buffer()
                    except:
                        pass
        time.sleep(0.01)

@app.route('/list_ports', methods=['GET'])
def list_ports():
    ports = list(serial.tools.list_ports.comports())
    
    port_list = [{"device": p.device, "description": p.description} for p in sorted(ports, key=lambda x: x.device)]
    
    # Raspberry Pi'de donanimsal UART portlari (serial0) her zaman pnp id'si olmadigi icin pyserial 
    # tarafindan filtrelenebilir. Eger Linux'taysak ve bu port varsa listeye kesin olarak zorla ekleyelim:
    import platform
    import os
    if platform.system() == "Linux" and os.path.exists('/dev/serial0'):
        if not any(p['device'] == '/dev/serial0' for p in port_list):
            port_list.append({"device": "/dev/serial0", "description": "Raspberry Pi Hardware UART (Pin 14/15)"})

    print(f"\n--- DEBUG: {len(port_list)} PORT BULUNDU ---")
    for p in port_list:
        print(f"Port: {p['device']} | Tanim: {p['description']}")
    print("--------------------------------\n")
    
    return jsonify({"ports": port_list})
@app.route('/connect', methods=['POST'])
def connect():
    global dev, robot
    data = request.json
    com_port = data.get('port')
    if not com_port:
        return jsonify({"error": "port parameter is required", "status": "failed"}), 400
        
    with api_lock:
        if dev is not None:
            return jsonify({"error": "already connected", "status": "failed"}), 400
            
    print(f"Connecting to: {com_port}...")
    try:
        new_dev = Delta(com_port)
        new_robot = AcromeDelta()
        
        # Prevent the robot from slamming into the ground:
        try:
            theta = new_robot.inverse_kin(0, 0, -180)
            pos = new_robot.angletoPos(theta)
            new_dev.set_motors(np.int_(pos))
            new_dev.update() # Send initial position frame safely
        except Exception as e:
            pass
            
        with api_lock:
            dev = new_dev
            robot = new_robot
            
        print("Connection successful!")
        return jsonify({"status": "success", "port": com_port})
    except Exception as e:
        print(f"Connection error: {e}")
        return jsonify({"error": str(e), "status": "failed"}), 500

@app.route('/disconnect', methods=['POST'])
def disconnect():
    global dev, robot
    with api_lock:
        if dev is None:
            return jsonify({"status": "success", "message": "already disconnected"})
        dev = None
        robot = None
    print("Disconnected.")
    return jsonify({"status": "success"})

@app.route('/status', methods=['GET'])
def status():
    with api_lock:
        is_connected = dev is not None
    return jsonify({"connected": is_connected})

@app.route('/move_pos', methods=['POST'])
def move_pos():
    data = request.json
    x, y, z = data.get('x'), data.get('y'), data.get('z')
    
    if None in [x, y, z]:
        return jsonify({"error": "x, y, z parameters are required"}), 400
        
    try:
        theta = robot.inverse_kin(x, y, z)
        pos = robot.angletoPos(theta)
        
        with api_lock:
            if dev: dev.set_motors(np.int_(pos))
            
        return jsonify({"status": "success", "theta": theta, "pos": pos.tolist()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/move_pos_traj', methods=['POST'])
def move_pos_traj():
    data = request.json
    x, y, z = data.get('x'), data.get('y'), data.get('z')
    ms = data.get('ms', 1000) 
    
    if None in [x, y, z]:
        return jsonify({"error": "x, y, z parameters are required"}), 400
        
    try:
        traj_time = ms / 1000.0 
        
        with api_lock:
            if not dev: return jsonify({"error": "Device offline"}), 500
            curr_mot_pos = dev.position
            
        theta1 = robot.postoAngle(curr_mot_pos[0])
        theta2 = robot.postoAngle(curr_mot_pos[1])
        theta3 = robot.postoAngle(curr_mot_pos[2])
        ipos = robot.forward_kin(theta1, theta2, theta3)
        
        fpos = [x, y, z]
        start_time = time.time()
        end_time = time.time()
        
        while (end_time - start_time) < traj_time:
            traj_pos = robot.trajectory(start_time, ipos, fpos, traj_time)
            theta = robot.inverse_kin(traj_pos[0], traj_pos[1], traj_pos[2])
            pos = robot.angletoPos(theta)
            
            with api_lock:
                if dev: dev.set_motors(np.int_(pos))
            
            end_time = time.time()
            time.sleep(0.01) 
            
        # Ensure it reaches exactly the final point
        theta = robot.inverse_kin(fpos[0], fpos[1], fpos[2])
        pos = robot.angletoPos(theta)
        
        with api_lock:
            if dev: dev.set_motors(np.int_(pos))
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/grab', methods=['POST'])
def grab():
    data = request.json
    state = data.get('state')
    
    if state is None:
        return jsonify({"error": "state parameter (1 or 0) is required"}), 400
        
    try:
        with api_lock:
            if dev: dev.pick(bool(state))
            
        return jsonify({"status": "success", "state": state})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_mot_pos', methods=['GET'])
def get_mot_pos():
    try:
        with api_lock:
            if not dev: return jsonify({"error": "Device offline"}), 500
            pos = list(dev.position) # Make a copy to avoid race conditions
            
        return jsonify({
            "m1": pos[0],
            "m2": pos[1],
            "m3": pos[2]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delay', methods=['POST'])
def delay_cmd():
    data = request.json
    ms = data.get('ms')
    
    if ms is None:
        return jsonify({"error": "ms parameter is required"}), 400
        
    time.sleep(ms / 1000.0)
    return jsonify({"status": "success", "delayed_ms": ms})

@app.route('/get_ee_pos', methods=['GET'])
def get_ee_pos():
    try:
        with api_lock:
            if not dev: return jsonify({"error": "Device offline"}), 500
            curr_mot_pos = list(dev.position)
            
        theta1 = robot.postoAngle(curr_mot_pos[0])
        theta2 = robot.postoAngle(curr_mot_pos[1])
        theta3 = robot.postoAngle(curr_mot_pos[2])
        
        ee_pos = robot.forward_kin(theta1, theta2, theta3)
        
        return jsonify({
            "x": ee_pos[0],
            "y": ee_pos[1],
            "z": ee_pos[2]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_telemetry', methods=['GET'])
def get_telemetry():
    try:
        with api_lock:
            if not dev: return jsonify({"error": "Device offline"}), 500
            curr_mot_pos = list(dev.position)
            
        theta1 = robot.postoAngle(curr_mot_pos[0])
        theta2 = robot.postoAngle(curr_mot_pos[1])
        theta3 = robot.postoAngle(curr_mot_pos[2])
        
        ee_pos = robot.forward_kin(theta1, theta2, theta3)
        
        return jsonify({
            "m1": curr_mot_pos[0],
            "m2": curr_mot_pos[1],
            "m3": curr_mot_pos[2],
            "x": ee_pos[0],
            "y": ee_pos[1],
            "z": ee_pos[2]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start the background telemetry thread globally once
    t = threading.Thread(target=telemetry_loop, daemon=True)
    t.start()
    print("Background telemetry thread started.")
    
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    import subprocess
    import platform
    print("\n" + "="*60)
    print(" API SERVER SUCCESSFULLY STARTED")
    print("="*60)
    print(" * (All)      Listening Address   : 0.0.0.0:5000")
    print(" * (Local)    Access Address      : http://127.0.0.1:5000")
    
    if platform.system() == "Linux":
        try:
            output = subprocess.getoutput("ip -4 -o addr")
            for line in output.split('\n'):
                parts = line.split()
                if len(parts) >= 4:
                    iface = parts[1]
                    ip = parts[3].split('/')[0]
                    if iface == "lo": continue
                    
                    label = ""
                    if "eth" in iface or "en" in iface:
                        label = "(Ethernet)"
                    elif "wlan" in iface or "wl" in iface:
                        label = "(Wireless)"
                    else:
                        label = f"({iface})"
                        
                    print(f" * {label:<10} Access Address      : http://{ip}:5000")
        except:
            pass
    print("="*60 + "\n")
    print("API Endpoints: GET /list_ports, POST /connect, POST /disconnect, GET /status")
    print("Press CTRL+C to quit...\n")
    
    app.run(host='0.0.0.0', port=5000)
