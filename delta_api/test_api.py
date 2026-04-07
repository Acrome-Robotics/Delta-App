import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def print_response(res):
    print(f"  --> Status Code: {res.status_code}")
    try:
        # Check if there is a JSON response to show
        json_data = res.json()
        print(f"  --> API Response: {json.dumps(json_data, indent=2)}")
        return json_data
    except ValueError:
        print(f"  --> API Response: {res.text}")
        return None

def test_api():
    print(f"[{BASE_URL}] Starting Detailed API Movement Test...\n")
    print("Delays have been added between steps to allow physical machine movements to be observed.\n")
    time.sleep(1)

    # 1. Soft transition to Start/Home position (Z=-150)
    print("Step 1: Soft transition to Start/Home position (Z=-150) (takes 2 sec)")
    data = {"x": 0, "y": 0, "z": -150, "ms": 2000}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    time.sleep(2.5) # Wait for movement to finish + 0.5s pause

    # 2. Smooth movement right on the X-axis
    print("\nStep 2: Moving right to point X=40 (2 sec)")
    data = {"x": 40, "y": 0, "z": -150, "ms": 2000}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    time.sleep(2.5)

    # 3. Smooth movement left on the X-axis (longer distance)
    print("\nStep 3: Moving left to point X=-40 (3 sec)")
    data = {"x": -40, "y": 0, "z": -150, "ms": 3000}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    time.sleep(3.5)

    # 4. Return to center point
    print("\nStep 4: Returning to center (X=0) (1.5 sec)")
    data = {"x": 0, "y": 0, "z": -150, "ms": 1500}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    time.sleep(2)

    # 5. Read instantaneous position and print to terminal
    print("\nStep 5: Reading current Motor and End-effector positions")
    print("  --- /get_mot_pos ---")
    mot_pos_res = requests.get(f"{BASE_URL}/get_mot_pos")
    print_response(mot_pos_res)
    
    print("  --- /get_ee_pos ---")
    ee_pos_res = requests.get(f"{BASE_URL}/get_ee_pos")
    print_response(ee_pos_res)
    time.sleep(1)

    # 6. Magnet Test (Grab Object)
    print("\nStep 6: Fast instantaneous drop to Z=-200 to grab object (move_pos will drop instantly!)")
    data = {"x": 0, "y": 0, "z": -200}
    res = requests.post(f"{BASE_URL}/move_pos", json=data)
    print_response(res)
    time.sleep(1) # Wait slightly to observe the effect since it's instantaneous
    
    print("\n  -> Turning Magnet ON (grab=1)")
    res = requests.post(f"{BASE_URL}/grab", json={"state": 1})
    print_response(res)
    time.sleep(2) # Keep magnet open for 2 seconds

    print("\n  -> Turning Magnet OFF (grab=0)")
    res = requests.post(f"{BASE_URL}/grab", json={"state": 0})
    print_response(res)
    time.sleep(1)

    # 7. Final - Finish by rising to Home position
    print("\nStep 7: Operation finished. Gently rising to Home position (1.5 sec)")
    data = {"x": 0, "y": 0, "z": -150, "ms": 1500}
    res = requests.post(f"{BASE_URL}/move_pos_traj", json=data)
    print_response(res)
    
    print("\nDetailed test completed successfully!")

if __name__ == "__main__":
    test_api()
