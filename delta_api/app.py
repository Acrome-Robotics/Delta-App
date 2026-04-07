import sys
import os
import time
import numpy as np

# Add project root and python-library to sys.path so we can import delta related modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'python-library'))
sys.path.append(os.path.join(BASE_DIR, 'delta_conveyor'))

from flask import Flask, request, jsonify
from flask_cors import CORS
from acrome.controller import Delta
from DeltaRobot import AcromeDelta

app = Flask(__name__)
CORS(app)

dev = None
robot = None

def init_robot():
    global dev, robot
    com_port = input("Please enter the COM port the Delta Robot is connected to (e.g., COM20): ")
    com_port = com_port.strip()
    if not com_port:
        com_port = "COM20"
        print(f"Input is empty, defaulting to {com_port}.")
        
    print(f"Connecting to: {com_port}...")
    try:
        dev = Delta(com_port)
        robot = AcromeDelta()
        print("Connection successful!")
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)

@app.route('/move_pos', methods=['POST'])
def move_pos():
    data = request.json
    x, y, z = data.get('x'), data.get('y'), data.get('z')
    
    if None in [x, y, z]:
        return jsonify({"error": "x, y, z parameters are required"}), 400
        
    try:
        theta = robot.inverse_kin(x, y, z)
        pos = robot.angletoPos(theta)
        dev.set_motors(np.int_(pos))
        dev.update()
        return jsonify({"status": "success", "theta": theta, "pos": pos.tolist()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/move_pos_traj', methods=['POST'])
def move_pos_traj():
    data = request.json
    x, y, z = data.get('x'), data.get('y'), data.get('z')
    ms = data.get('ms', 1000) # Default to 1 second if not provided
    
    if None in [x, y, z]:
        return jsonify({"error": "x, y, z parameters are required"}), 400
        
    try:
        traj_time = ms / 1000.0 # calculate time in seconds
        
        # Get Current position as Initial Position
        dev.update() # Get latest reading
        curr_mot_pos = dev.position
        
        # postoAngle needs a single value per array call, but dev.position is a list.
        # postoAngle seems to work natively with scalar integers too based on DeltaRobot code
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
            dev.set_motors(np.int_(pos))
            dev.update()
            end_time = time.time()
            time.sleep(0.01) # Small delay for yielding cpu
            
        # Ensure it reaches exactly the final point
        theta = robot.inverse_kin(fpos[0], fpos[1], fpos[2])
        pos = robot.angletoPos(theta)
        dev.set_motors(np.int_(pos))
        dev.update()
        
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
        dev.pick(bool(state))
        dev.update()
        return jsonify({"status": "success", "state": state})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_mot_pos', methods=['GET'])
def get_mot_pos():
    try:
        dev.update()
        return jsonify({
            "m1": dev.position[0],
            "m2": dev.position[1],
            "m3": dev.position[2]
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
        dev.update()
        curr_mot_pos = dev.position
        
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

if __name__ == '__main__':
    # Initialize the board and ask user for port before launching server
    init_robot()
    
    print("\nStarting Flask server. You can access the API endpoints on http://127.0.0.1:5000")
    print("Press CTRL+C to stop.")
    app.run(host='0.0.0.0', port=5000)
